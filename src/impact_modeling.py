import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class EventImpactModel:
    """Model event impacts on financial inclusion indicators"""
    
    def __init__(self, data_path: str):
        """Initialize with enriched dataset"""
        self.df = pd.read_csv(data_path)
        self.events = self.df[self.df['record_type'] == 'event']
        self.observations = self.df[self.df['record_type'] == 'observation']
        self.impact_links = self.df[self.df['record_type'] == 'impact_link']
        
    def build_event_indicator_matrix(self) -> pd.DataFrame:
        """Create association matrix showing event impacts on indicators"""
        
        # Extract key indicators from observations
        key_indicators = [
            'ACC_OWNERSHIP', 'ACC_MM_ACCOUNT', 'USG_DIGITAL_PAYMENT',
            'ACC_ACC_BANK', 'INFRA_AGENT_DENSITY', 'INFRA_4G_COVERAGE'
        ]
        
        # Initialize matrix
        events_list = self.events['event_name'].unique()
        matrix = pd.DataFrame(index=events_list, columns=key_indicators)
        matrix_confidence = pd.DataFrame(index=events_list, columns=key_indicators)
        
        # Fill matrix from impact links
        for _, link in self.impact_links.iterrows():
            event_id = link['parent_id']
            event = self.events[self.events['record_id'] == event_id]
            if not event.empty:
                event_name = event.iloc[0]['event_name']
                indicator = link['related_indicator']
                direction = link['impact_direction']
                magnitude = link['impact_magnitude']
                confidence = link.get('confidence', 'medium')
                
                if indicator in key_indicators:
                    # Convert direction and magnitude to numeric impact
                    if direction == 'positive':
                        impact = magnitude if isinstance(magnitude, (int, float)) else 1.0
                    elif direction == 'negative':
                        impact = -magnitude if isinstance(magnitude, (int, float)) else -1.0
                    else:
                        impact = 0
                    
                    matrix.loc[event_name, indicator] = impact
                    matrix_confidence.loc[event_name, indicator] = confidence
        
        # Fill missing values with comparable country evidence
        matrix = self._add_comparable_evidence(matrix)
        
        return matrix, matrix_confidence
    
    def _add_comparable_evidence(self, matrix: pd.DataFrame) -> pd.DataFrame:
        """Add impact estimates based on comparable country evidence"""
        
        # Comparable evidence from literature (Kenya, Tanzania, Ghana)
        comparable_evidence = {
            # Telebirr launch (similar to M-Pesa in Kenya 2007)
            'Telebirr Launch': {
                'ACC_MM_ACCOUNT': 5.0,  # +5% points in first year
                'USG_DIGITAL_PAYMENT': 4.0,
                'ACC_OWNERSHIP': 3.0
            },
            # M-Pesa Ethiopia launch
            'M-Pesa Launch': {
                'ACC_MM_ACCOUNT': 2.5,  # +2.5% points
                'USG_DIGITAL_PAYMENT': 3.0,
                'INFRA_AGENT_DENSITY': 15.0  # % increase
            },
            # CBDC pilot (based on Nigeria eNaira)
            'CBDC Pilot': {
                'ACC_OWNERSHIP': 1.5,
                'USG_DIGITAL_PAYMENT': 2.0
            }
        }
        
        # Apply comparable evidence where we have gaps
        for event, impacts in comparable_evidence.items():
            if event in matrix.index:
                for indicator, impact in impacts.items():
                    if pd.isna(matrix.loc[event, indicator]) and indicator in matrix.columns:
                        matrix.loc[event, indicator] = impact
        
        return matrix
    
    def model_event_effects_over_time(self, event_date: str, impact: float, 
                                    effect_type: str = 'immediate') -> pd.Series:
        """Model how an event's effect propagates over time"""
        
        # Define time window (36 months)
        months = np.arange(0, 37)
        
        if effect_type == 'immediate':
            # Immediate effect with gradual adoption
            effect = impact * (1 - np.exp(-months / 12))
        elif effect_type == 'gradual':
            # Gradual buildup (logistic)
            effect = impact / (1 + np.exp(-(months - 6) / 3))
        elif effect_type == 'saturating':
            # Quick initial effect then saturation
            effect = impact * np.tanh(months / 18)
        else:
            effect = np.zeros_like(months)
        
        return pd.Series(effect, index=months)
    
    def validate_against_historical(self, event_name: str, indicator: str) -> Dict:
        """Validate modeled impact against historical data"""
        
        # Get event details
        event = self.events[self.events['event_name'] == event_name].iloc[0]
        event_date = pd.to_datetime(event['event_date'])
        
        # Get pre/post observations for this indicator
        observations = self.observations[
            self.observations['indicator_code'] == indicator
        ].copy()
        observations['date'] = pd.to_datetime(observations['observation_date'])
        observations = observations.sort_values('date')
        
        # Find observations around event
        pre_obs = observations[observations['date'] < event_date]
        post_obs = observations[observations['date'] > event_date]
        
        if len(pre_obs) > 0 and len(post_obs) > 0:
            # Calculate actual change
            pre_value = pre_obs.iloc[-1]['value_numeric']
            post_value = post_obs.iloc[0]['value_numeric']
            actual_change = post_value - pre_value
            
            # Get modeled impact
            matrix, _ = self.build_event_indicator_matrix()
            modeled_impact = matrix.loc[event_name, indicator]
            
            validation_result = {
                'event': event_name,
                'indicator': indicator,
                'event_date': event_date,
                'pre_value': pre_value,
                'post_value': post_value,
                'actual_change': actual_change,
                'modeled_impact': modeled_impact,
                'difference': actual_change - (modeled_impact if not pd.isna(modeled_impact) else 0),
                'valid': abs(actual_change - (modeled_impact if not pd.isna(modeled_impact) else 0)) < 2.0
            }
            
            return validation_result
        
        return None
    
    def generate_impact_curve(self, events: List[str], indicator: str, 
                            start_date: str = '2020-01-01') -> pd.DataFrame:
        """Generate cumulative impact curve for multiple events"""
        
        dates = pd.date_range(start=start_date, end='2024-12-01', freq='MS')
        impact_curve = pd.Series(0, index=dates)
        
        matrix, _ = self.build_event_indicator_matrix()
        
        for event in events:
            if event in matrix.index and indicator in matrix.columns:
                impact = matrix.loc[event, indicator]
                if not pd.isna(impact):
                    # Get event date
                    event_row = self.events[self.events['event_name'] == event]
                    if not event_row.empty:
                        event_date = pd.to_datetime(event_row.iloc[0]['event_date'])
                        
                        # Generate effect over time
                        effect_series = self.model_event_effects_over_time(
                            event_date, impact, effect_type='gradual'
                        )
                        
                        # Add to cumulative impact
                        for months, effect in effect_series.items():
                            impact_date = event_date + pd.DateOffset(months=months)
                            if impact_date in impact_curve.index:
                                impact_curve[impact_date] += effect
        
        return impact_curve.to_frame('cumulative_impact')