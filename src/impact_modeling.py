import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
from typing import List,Dict
warnings.filterwarnings('ignore')

class EventImpactModel:
    def __init__(self, data_path: str):
        """Initialize event impact model with enriched dataset"""
        self.data = pd.read_csv(data_path)
        
        # Filter by record_type
        self.impact_links = self.data[self.data['record_type'] == 'impact_link']
        self.events = self.data[self.data['record_type'] == 'event']
        self.observations = self.data[self.data['record_type'] == 'observation']
        
        # Debug prints to understand data structure
        print(f"Loaded {len(self.data)} total records")
        print(f"  - {len(self.events)} events")
        print(f"  - {len(self.impact_links)} impact links")
        print(f"  - {len(self.observations)} observations")
        
    def create_event_indicator_matrix(self) -> pd.DataFrame:
        """Create event-indicator association matrix"""
        
        # Filter relevant indicators for forecasting
        key_indicators = [
            'ACC_OWNERSHIP', 'ACC_MM_ACCOUNT', 'USG_DIGITAL_PAYMENT',
            'INF_AGENT_DENSITY', 'INF_4G_COVERAGE', 'INF_SMARTPHONE_PENETRATION'
        ]
        
        # Extract event-impact relationships
        impact_data = []
        
        # Check what columns exist
        print(f"\nAvailable columns in impact_links: {list(self.impact_links.columns)}")
        
        for _, link in self.impact_links.iterrows():
            # Link events using parent_id (not event_id)
            parent_id = link['parent_id']
            
            # Find the corresponding event
            event_match = self.events[self.events['record_id'] == parent_id]
            
            if len(event_match) > 0:
                event = event_match.iloc[0]
                event_name = event.get('value_text', f"Event_{parent_id}")
                event_date = event.get('observation_date')
                event_category = event.get('category', 'policy')
                
                # Get impact details - handle missing columns
                related_indicator = link.get('related_indicator', link.get('indicator_code', ''))
                impact_direction = link.get('impact_direction', 'positive')
                
                # Try different possible column names for magnitude
                magnitude = 0
                if 'impact_magnitude' in link:
                    magnitude = link['impact_magnitude']
                elif 'impact_estimate' in link:
                    magnitude = link['impact_estimate']
                
                # Convert magnitude to float if possible
                try:
                    magnitude = float(magnitude) if pd.notna(magnitude) else 0
                except:
                    magnitude = 0
                
                # Get lag months if available
                lag_months = link.get('lag_months', 0)
                try:
                    lag_months = int(lag_months) if pd.notna(lag_months) else 0
                except:
                    lag_months = 0
                
                impact_data.append({
                    'parent_id': parent_id,
                    'event_name': event_name,
                    'event_date': event_date,
                    'event_category': event_category,
                    'indicator': related_indicator,
                    'direction': impact_direction,
                    'magnitude': magnitude,
                    'lag_months': lag_months,
                    'evidence_basis': link.get('evidence_basis', 'expert_judgment')
                })
        
        if not impact_data:
            print("WARNING: No impact links found!")
            return pd.DataFrame()
        
        impact_df = pd.DataFrame(impact_data)
        print(f"\nExtracted {len(impact_df)} impact relationships")
        print(f"Unique events: {impact_df['parent_id'].nunique()}")
        print(f"Unique indicators: {impact_df['indicator'].nunique()}")
        
        # Create pivot matrix
        matrix_data = []
        for event_id in impact_df['parent_id'].unique():
            event_impacts = impact_df[impact_df['parent_id'] == event_id]
            event_info = event_impacts.iloc[0]
            
            row = {
                'event_id': event_id, 
                'event_name': event_info['event_name'],
                'event_category': event_info['event_category'],
                'event_date': event_info['event_date']
            }
            
            for indicator in key_indicators:
                indicator_impacts = event_impacts[event_impacts['indicator'] == indicator]
                if len(indicator_impacts) > 0:
                    # Calculate weighted impact score
                    impact_score = 0
                    for _, impact in indicator_impacts.iterrows():
                        magnitude = impact['magnitude']
                        direction = 1 if impact['direction'].lower() == 'positive' else -1
                        impact_score += direction * magnitude
                    row[indicator] = impact_score
                else:
                    row[indicator] = 0  # No impact
            
            matrix_data.append(row)
        
        matrix_df = pd.DataFrame(matrix_data)
        
        # Fill NaN values with 0
        matrix_df = matrix_df.fillna(0)
        
        return matrix_df
    
    def model_impact_function(self, event_date: str, indicator: str, 
                            magnitude: float, direction: str, lag: int = 0) -> Dict:
        """Model how an event's impact unfolds over time"""
        
        # Different impact functions based on event type
        impact_functions = {
            'policy': self._policy_impact_function,
            'product_launch': self._launch_impact_function,
            'infrastructure': self._infrastructure_impact_function,
            'market_entry': self._market_entry_function
        }
        
        # Get event type
        event_type = self._get_event_type(event_date)
        impact_func = impact_functions.get(event_type, self._default_impact_function)
        
        return impact_func(event_date, indicator, magnitude, direction, lag)
    
    def _policy_impact_function(self, event_date: str, indicator: str, 
                              magnitude: float, direction: str, lag: int):
        """Policy impacts typically have gradual ramp-up"""
        return {
            'immediate_effect': magnitude * 0.1 * (1 if direction == 'positive' else -1),
            'peak_effect': magnitude * (1 if direction == 'positive' else -1),
            'peak_time_months': lag + 12,
            'decay_rate': 0.05,
            'duration_months': 36
        }
    
    def _launch_impact_function(self, event_date: str, indicator: str,
                              magnitude: float, direction: str, lag: int):
        """Product launches have rapid initial impact"""
        return {
            'immediate_effect': magnitude * 0.3 * (1 if direction == 'positive' else -1),
            'peak_effect': magnitude * (1 if direction == 'positive' else -1),
            'peak_time_months': lag + 6,
            'decay_rate': 0.02,
            'duration_months': 48
        }
    
    def validate_against_historical(self, indicator: str = 'ACC_MM_ACCOUNT'):
        """Validate impact model against historical data"""
        
        # Get historical observations
        historical = self.observations[
            (self.observations['indicator_code'] == indicator) &
            (self.observations['value_numeric'].notna())
        ].copy()
        
        if len(historical) == 0:
            print(f"No historical data found for {indicator}")
            return pd.DataFrame()
        
        historical['observation_date'] = pd.to_datetime(historical['observation_date'])
        historical = historical.sort_values('observation_date')
        
        # Simulate predictions
        predictions = []
        for idx, row in historical.iterrows():
            date = row['observation_date']
            predicted = self._simulate_impact_at_date(date, indicator)
            actual = row['value_numeric']
            
            predictions.append({
                'date': date,
                'actual': actual,
                'predicted': predicted if pd.notna(predicted) else None,
                'error': predicted - actual if pd.notna(predicted) and pd.notna(actual) else None
            })
        
        return pd.DataFrame(predictions)
    
    def _simulate_impact_at_date(self, date: datetime, indicator: str):
        """Simulate cumulative impact of all events up to a given date"""
        base_value = self._get_base_value(indicator)
        cumulative_impact = 0
        
        # Get all events before this date
        events_before = self.events[
            pd.to_datetime(self.events['observation_date']) <= date
        ]
        
        for _, event in events_before.iterrows():
            event_id = event['record_id']
            impacts = self.impact_links[
                (self.impact_links['parent_id'] == event_id)
            ]
            
            # Check if this event affects our indicator
            for _, impact in impacts.iterrows():
                # Check different possible column names
                related_indicator = impact.get('related_indicator', impact.get('indicator_code', ''))
                if related_indicator != indicator:
                    continue
                
                # Get impact magnitude
                magnitude = 0
                if 'impact_magnitude' in impact:
                    magnitude = impact['impact_magnitude']
                elif 'impact_estimate' in impact:
                    magnitude = impact['impact_estimate']
                
                try:
                    magnitude = float(magnitude) if pd.notna(magnitude) else 0
                except:
                    magnitude = 0
                
                # Get direction
                direction_str = impact.get('impact_direction', 'positive')
                direction = 1 if direction_str.lower() == 'positive' else -1
                
                # Get lag
                lag = impact.get('lag_months', 0)
                try:
                    lag = int(lag) if pd.notna(lag) else 0
                except:
                    lag = 0
                
                # Calculate impact considering lag
                event_date = pd.to_datetime(event['observation_date'])
                months_since_event = ((date - event_date).days // 30)
                
                if months_since_event >= lag:
                    # Apply impact with time-based adjustment
                    time_factor = min(1.0, months_since_event / 12)
                    cumulative_impact += direction * magnitude * time_factor
        
        return base_value + cumulative_impact if pd.notna(base_value) else cumulative_impact
    
    def _get_base_value(self, indicator: str):
        """Get baseline value for an indicator"""
        indicator_data = self.observations[
            (self.observations['indicator_code'] == indicator) &
            (self.observations['value_numeric'].notna())
        ]
        
        if len(indicator_data) > 0:
            # Get the earliest value
            sorted_data = indicator_data.sort_values('observation_date')
            return sorted_data.iloc[0]['value_numeric']
        
        # Default baseline if no data
        baseline_values = {
            'ACC_OWNERSHIP': 10.0,
            'ACC_MM_ACCOUNT': 1.0,
            'USG_DIGITAL_PAYMENT': 5.0
        }
        return baseline_values.get(indicator, 0.0)
    
    def _get_event_type(self, event_date: str):
        """Determine event type from date"""
        try:
            event = self.events[pd.to_datetime(self.events['observation_date']) == pd.to_datetime(event_date)]
            if len(event) > 0:
                return event.iloc[0].get('category', 'policy')
        except:
            pass
        return 'policy'
    
    def _infrastructure_impact_function(self, event_date: str, indicator: str,
                                      magnitude: float, direction: str, lag: int):
        """Infrastructure impacts"""
        return {
            'immediate_effect': magnitude * 0.2 * (1 if direction == 'positive' else -1),
            'peak_effect': magnitude * (1 if direction == 'positive' else -1),
            'peak_time_months': lag + 18,  # Infrastructure takes longest
            'decay_rate': 0.01,  # Very slow decay
            'duration_months': 60  # Long-lasting impact
        }
    
    def _market_entry_function(self, event_date: str, indicator: str,
                             magnitude: float, direction: str, lag: int):
        """Market entry impacts"""
        return {
            'immediate_effect': magnitude * 0.4 * (1 if direction == 'positive' else -1),
            'peak_effect': magnitude * (1 if direction == 'positive' else -1),
            'peak_time_months': lag + 9,
            'decay_rate': 0.03,
            'duration_months': 36
        }
    
    def _default_impact_function(self, event_date: str, indicator: str,
                               magnitude: float, direction: str, lag: int):
        """Default impact function"""
        return {
            'immediate_effect': magnitude * 0.2 * (1 if direction == 'positive' else -1),
            'peak_effect': magnitude * (1 if direction == 'positive' else -1),
            'peak_time_months': lag + 9,
            'decay_rate': 0.03,
            'duration_months': 24
        }