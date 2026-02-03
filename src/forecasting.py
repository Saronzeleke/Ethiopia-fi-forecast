import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
from scipy import stats
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
warnings.filterwarnings('ignore')

class FinancialInclusionForecaster:
    historical_events_with_ongoing_impacts = []
    def __init__(self, data_path: str):
        """Initialize forecaster with enriched dataset"""
        try:
            self.data = pd.read_csv(data_path)
            
            # Filter by record_type
            self.observations = self.data[self.data['record_type'] == 'observation']
            self.events = self.data[self.data['record_type'] == 'event']
            self.impact_links = self.data[self.data['record_type'] == 'impact_link']
            self.targets = self.data[self.data['record_type'] == 'target']
            
            # Debug info
            print(f"Forecaster initialized with:")
            print(f"  - {len(self.observations)} observations")
            print(f"  - {len(self.events)} events")
            print(f"  - {len(self.impact_links)} impact links")
            print(f"  - {len(self.targets)} targets")
            
        except Exception as e:
            raise ValueError(f"Failed to load data from {data_path}: {str(e)}")
    
    def prepare_time_series(self, indicator_code: str, freq: str = 'Y') -> pd.Series:
        """Prepare time series data for forecasting"""
        
        # Filter observations for the indicator
        indicator_data = self.observations[
            (self.observations['indicator_code'] == indicator_code) &
            (self.observations['value_numeric'].notna())
        ].copy()
        
        if len(indicator_data) == 0:
            print(f"Warning: No data found for indicator {indicator_code}")
            return pd.Series(dtype=float)
        
        # Convert dates
        indicator_data['date'] = pd.to_datetime(indicator_data['observation_date'])
        indicator_data.set_index('date', inplace=True)
        indicator_data = indicator_data.sort_index()
        
        # Resample based on frequency
        if freq == 'Y':  # Yearly
            ts = indicator_data['value_numeric'].resample('Y').last().dropna()
        elif freq == 'Q':  # Quarterly
            ts = indicator_data['value_numeric'].resample('Q').last().dropna()
        elif freq == 'M':  # Monthly
            ts = indicator_data['value_numeric'].resample('M').last().dropna()
        else:
            ts = indicator_data['value_numeric']
        
        print(f"Prepared time series for {indicator_code}: {len(ts)} points from {ts.index.min().year} to {ts.index.max().year}")
        return ts
    
    def get_target_value(self, indicator_code: str) -> Optional[float]:
        """Get NFIS-II target value for an indicator"""
        target_data = self.targets[
            (self.targets['indicator_code'] == indicator_code) &
            (self.targets['value_numeric'].notna())
        ]
        
        if len(target_data) > 0:
            return float(target_data.iloc[-1]['value_numeric'])
        return None
    
    def trend_forecast(self, indicator_code: str, years_ahead: int = 3,
                      model_type: str = 'linear', confidence_level: float = 0.95) -> Dict:
        """Create trend-based forecast using regression"""
        
        # Get time series data
        ts = self.prepare_time_series(indicator_code, 'Y')
        
        if len(ts) < 2:
            raise ValueError(f"Insufficient data for {indicator_code}: only {len(ts)} data points")
        
        # Prepare data for regression
        X = np.arange(len(ts)).reshape(-1, 1)
        y = ts.values
        
        if model_type == 'linear':
            # Linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate forecasts
            future_X = np.arange(len(ts), len(ts) + years_ahead).reshape(-1, 1)
            forecasts = model.predict(future_X)
            
            # Calculate confidence intervals
            predictions = model.predict(X)
            residuals = y - predictions
            std_error = np.std(residuals)
            n = len(X)
            
            # T-statistic for confidence interval
            t_value = stats.t.ppf(1 - (1 - confidence_level) / 2, n - 2)
            
            ci_lower = []
            ci_upper = []
            for i, x_new in enumerate(future_X):
                # Standard error for prediction
                x_mean = np.mean(X)
                x_var = np.var(X)
                se_pred = std_error * np.sqrt(1 + 1/n + (x_new - x_mean)**2 / (n * x_var))
                
                ci_lower.append(forecasts[i] - t_value * se_pred)
                ci_upper.append(forecasts[i] + t_value * se_pred)
            
            r_squared = model.score(X, y)
            
        elif model_type == 'exponential':
            # Exponential growth (log-linear) model
            # Add small constant to avoid log(0)
            y_positive = np.maximum(y, 0.1)
            y_log = np.log(y_positive)
            
            model = LinearRegression()
            model.fit(X, y_log)
            
            # Generate forecasts in log space
            future_X = np.arange(len(ts), len(ts) + years_ahead).reshape(-1, 1)
            log_forecasts = model.predict(future_X)
            forecasts = np.exp(log_forecasts)
            
            # Confidence intervals in log space
            log_predictions = model.predict(X)
            log_residuals = y_log - log_predictions
            log_std_error = np.std(log_residuals)
            n = len(X)
            
            t_value = stats.t.ppf(1 - (1 - confidence_level) / 2, n - 2)
            x_mean = np.mean(X)
            x_var = np.var(X)
            
            ci_lower = []
            ci_upper = []
            for i, x_new in enumerate(future_X):
                se_pred = log_std_error * np.sqrt(1 + 1/n + (x_new - x_mean)**2 / (n * x_var))
                log_ci_lower = log_forecasts[i] - t_value * se_pred
                log_ci_upper = log_forecasts[i] + t_value * se_pred
                ci_lower.append(np.exp(log_ci_lower))
                ci_upper.append(np.exp(log_ci_upper))
            
            r_squared = model.score(X, y_log)
            
        else:
            raise ValueError(f"Unsupported model_type: {model_type}. Use 'linear' or 'exponential'")
        
        # Generate forecast dates
        last_date = ts.index[-1]
        forecast_dates = []
        for i in range(1, years_ahead + 1):
            forecast_dates.append(last_date + pd.DateOffset(years=i))
        
        # Get target value if exists
        target_value = self.get_target_value(indicator_code)
        
        return {
            'indicator': indicator_code,
            'model_type': model_type,
            'forecast_dates': forecast_dates,
            'forecast_values': forecasts.tolist(),
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'r_squared': r_squared,
            'last_historical_value': float(y[-1]),
            'last_historical_date': last_date,
            'target_value': target_value,
            'years_to_target': self._calculate_years_to_target(forecasts[-1], target_value, 
                                                              model, future_X[-1][0]) if target_value else None
        }
    
    def _calculate_years_to_target(self, last_forecast: float, target_value: float, 
                                  model, last_x: float) -> Optional[int]:
        """Calculate years needed to reach target"""
        if target_value is None or last_forecast >= target_value:
            return None
        
        # Estimate additional years needed based on slope
        if hasattr(model, 'coef_'):
            slope = model.coef_[0]
            if slope <= 0:
                return None  # Not growing toward target
            
            # Solve for x where y = target_value
            # y = mx + b
            intercept = model.intercept_
            years_needed = (target_value - intercept) / slope - last_x
            
            return max(1, int(np.ceil(years_needed)))
        return None
    
    def event_augmented_forecast(self, indicator_code: str, 
                                event_scenario: str = 'base',
                                years_ahead: int = 3,
                                include_future_events: bool = True) -> Dict:
        """Create forecast incorporating event impacts"""
        
        # Get baseline trend forecast
        try:
            baseline = self.trend_forecast(indicator_code, years_ahead, 'linear')
        except ValueError as e:
            print(f"Warning: {e}. Using simple average growth.")
            baseline = self._create_simple_baseline(indicator_code, years_ahead)
        
        # Get future events and their impacts
        future_events = []
        if include_future_events:
            future_events = self._get_future_events(years_ahead)
        
        # Also consider historical events that have ongoing impacts
        historical_events_with_impacts = self._get_historical_events_with_ongoing_impacts(indicator_code)
        
        # Adjust forecasts based on events
        adjusted_forecasts = baseline['forecast_values'].copy()
        event_impacts_by_year = []
        event_details_by_year = []
        
        for year_idx, forecast_date in enumerate(baseline['forecast_dates']):
            year_impact = 0
            year_event_details = []
            
            # Add impacts from historical events
            historical_events_with_ongoing_impacts = []
            for event in historical_events_with_ongoing_impacts:
                event_impact = self._calculate_ongoing_event_impact(
                    event, indicator_code, forecast_date, event_scenario
                )
                if event_impact != 0:
                    year_impact += event_impact
                    year_event_details.append({
                        'event': event['name'],
                        'impact': event_impact,
                        'type': 'historical_ongoing'
                    })
            
            # Add impacts from future events
            for event in future_events:
                event_impact = self._calculate_future_event_impact(
                    event, indicator_code, forecast_date, event_scenario
                )
                if event_impact != 0:
                    year_impact += event_impact
                    year_event_details.append({
                        'event': event['name'],
                        'impact': event_impact,
                        'type': 'future'
                    })
            
            adjusted_forecasts[year_idx] += year_impact
            event_impacts_by_year.append(year_impact)
            event_details_by_year.append(year_event_details)
        
        # Adjust confidence intervals for added uncertainty
        baseline_ci_range = [baseline['ci_upper'][i] - baseline['ci_lower'][i] 
                           for i in range(years_ahead)]
        
        # Add uncertainty from event impacts (assume 50% uncertainty on impact estimates)
        event_uncertainty = [abs(impact) * 0.5 for impact in event_impacts_by_year]
        
        adjusted_ci_lower = [
            max(0, baseline['ci_lower'][i] - event_uncertainty[i]) 
            for i in range(years_ahead)
        ]
        adjusted_ci_upper = [
            baseline['ci_upper'][i] + event_uncertainty[i] 
            for i in range(years_ahead)
        ]
        
        return {
            'indicator': indicator_code,
            'scenario': event_scenario,
            'forecast_dates': baseline['forecast_dates'],
            'baseline_values': baseline['forecast_values'],
            'adjusted_values': adjusted_forecasts,
            'event_impacts': event_impacts_by_year,
            'event_details': event_details_by_year,
            'ci_lower': adjusted_ci_lower,
            'ci_upper': adjusted_ci_upper,
            'baseline_r_squared': baseline.get('r_squared'),
            'num_events_considered': len(historical_events_with_ongoing_impacts) + len(future_events),
            'include_future_events': include_future_events
        }
    
    def _create_simple_baseline(self, indicator_code: str, years_ahead: int) -> Dict:
        """Create simple baseline when insufficient data for regression"""
        
        ts = self.prepare_time_series(indicator_code, 'Y')
        
        if len(ts) == 0:
            # No data at all - use reasonable defaults
            default_values = {
                'ACC_OWNERSHIP': [45.8, 46.5, 47.2, 47.9],
                'ACC_MM_ACCOUNT': [9.45, 10.0, 10.6, 11.2],
                'USG_DIGITAL_PAYMENT': [34.2, 36.0, 37.9, 39.8]
            }
            
            forecasts = default_values.get(indicator_code, [0] * (years_ahead + 1))[1:]
            current_value = default_values.get(indicator_code, [0])[0]
        elif len(ts) == 1:
            # Only one data point - assume 2% annual growth
            current_value = ts.iloc[-1]
            growth_rate = 0.02
            forecasts = [current_value * (1 + growth_rate) ** (i+1) for i in range(years_ahead)]
        else:
            # At least 2 points - use average growth
            current_value = ts.iloc[-1]
            growth_rates = []
            for i in range(1, len(ts)):
                growth = (ts.iloc[i] - ts.iloc[i-1]) / ts.iloc[i-1]
                growth_rates.append(growth)
            
            avg_growth = np.mean(growth_rates)
            forecasts = [current_value * (1 + avg_growth) ** (i+1) for i in range(years_ahead)]
        
        # Generate dates
        last_date = pd.Timestamp('2024-12-31') if len(ts) == 0 else ts.index[-1]
        forecast_dates = [last_date + pd.DateOffset(years=i+1) for i in range(years_ahead)]
        
        # Simple confidence intervals (+/- 20%)
        ci_lower = [f * 0.8 for f in forecasts]
        ci_upper = [f * 1.2 for f in forecasts]
        
        return {
            'indicator': indicator_code,
            'forecast_dates': forecast_dates,
            'forecast_values': forecasts,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'last_historical_value': current_value,
            'last_historical_date': last_date
        }
    
    def _get_future_events(self, years_ahead: int) -> List[Dict]:
        """Get scheduled future events (based on Ethiopian financial inclusion roadmap)"""
        
        current_date = datetime.now()
        future_cutoff = current_date + timedelta(days=365 * years_ahead)
        
        # Known/expected future events based on Ethiopia's financial inclusion roadmap
        future_events = [
            {
                'name': 'CBDC Pilot Expansion',
                'date': '2025-06-01',
                'type': 'policy',
                'expected_impact_acc': 1.5,  # percentage points
                'expected_impact_usage': 2.5,
                'lag_months': 6,
                'duration_months': 24,
                'certainty': 0.7  # 70% probability
            },
            {
                'name': 'Agent Network Expansion Program',
                'date': '2025-09-01',
                'type': 'infrastructure',
                'expected_impact_acc': 2.0,
                'expected_impact_usage': 1.5,
                'lag_months': 9,
                'duration_months': 36,
                'certainty': 0.8
            },
            {
                'name': 'Interoperability Mandate Implementation',
                'date': '2026-01-01',
                'type': 'policy',
                'expected_impact_acc': 1.0,
                'expected_impact_usage': 3.5,
                'lag_months': 12,
                'duration_months': 48,
                'certainty': 0.6
            },
            {
                'name': 'Digital ID Integration',
                'date': '2026-07-01',
                'type': 'infrastructure',
                'expected_impact_acc': 2.5,
                'expected_impact_usage': 1.8,
                'lag_months': 6,
                'duration_months': 60,
                'certainty': 0.5
            }
        ]
        
        # Filter to events within forecast horizon
        filtered_events = []
        for event in future_events:
            event_date = pd.to_datetime(event['date'])
            if event_date <= future_cutoff:
                filtered_events.append(event)
        
        print(f"Considering {len(filtered_events)} future events in forecast")
        return filtered_events
    
    def _get_historical_events_with_ongoing_impacts(self, indicator_code: str) -> List[Dict]:
        """Get historical events that still have ongoing impacts"""
        
        # Key historical events in Ethiopia
        historical_events = [
            {
                'name': 'Telebirr Launch',
                'date': '2021-05-01',
                'type': 'product_launch',
                'peak_impact_acc': 2.0,
                'peak_impact_usage': 4.0,
                'lag_months': 3,
                'duration_months': 36,
                'decay_rate': 0.03  # 3% monthly decay after peak
            },
            {
                'name': 'M-Pesa Entry',
                'date': '2023-08-01',
                'type': 'market_entry',
                'peak_impact_acc': 1.5,
                'peak_impact_usage': 3.0,
                'lag_months': 6,
                'duration_months': 30,
                'decay_rate': 0.04
            },
            {
                'name': 'NFIS-II Policy Launch',
                'date': '2021-01-01',
                'type': 'policy',
                'peak_impact_acc': 1.2,
                'peak_impact_usage': 2.0,
                'lag_months': 12,
                'duration_months': 60,
                'decay_rate': 0.02
            }
        ]
        
        current_date = datetime.now()
        ongoing_events = []
        
        for event in historical_events:
            event_date = pd.to_datetime(event['date'])
            months_since = (current_date.year - event_date.year) * 12 + (current_date.month - event_date.month)
            
            # Check if impact duration hasn't expired
            if months_since <= event['duration_months']:
                ongoing_events.append(event)
        
        return ongoing_events
    
    def _calculate_future_event_impact(self, event: Dict, indicator_code: str, 
                                     forecast_date: datetime, scenario: str) -> float:
        """Calculate impact of a future event"""
        
        # Get base impact based on indicator type
        if 'ACC' in indicator_code:
            base_impact = event.get('expected_impact_acc', 0)
        elif 'USG' in indicator_code:
            base_impact = event.get('expected_impact_usage', 0)
        else:
            base_impact = 0
        
        # Apply scenario multiplier
        scenario_multipliers = {
            'optimistic': 1.3,
            'base': 1.0,
            'pessimistic': 0.7
        }
        multiplier = scenario_multipliers.get(scenario, 1.0)
        
        # Apply probability/certainty
        certainty = event.get('certainty', 0.5)
        
        # Calculate time-based adjustment
        event_date = pd.to_datetime(event['date'])
        months_since = (forecast_date.year - event_date.year) * 12 + (forecast_date.month - event_date.month)
        lag_months = event.get('lag_months', 6)
        
        if months_since < lag_months:
            # Event hasn't had time to show full effect yet
            return 0
        elif months_since <= lag_months + 12:  # First year after lag
            # Ramp up to full effect
            months_after_lag = months_since - lag_months
            time_factor = min(1.0, months_after_lag / 12)
        else:
            # Sustained effect (no decay for future events in forecast horizon)
            time_factor = 1.0
        
        return base_impact * multiplier * certainty * time_factor
    
    def _calculate_ongoing_event_impact(self, event: Dict, indicator_code: str,
                                      forecast_date: datetime, scenario: str) -> float:
        """Calculate ongoing impact of a historical event"""
        
        # Get base impact
        if 'ACC' in indicator_code:
            base_impact = event.get('peak_impact_acc', 0)
        elif 'USG' in indicator_code:
            base_impact = event.get('peak_impact_usage', 0)
        else:
            base_impact = 0
        
        # Apply scenario multiplier
        scenario_multipliers = {
            'optimistic': 1.1,
            'base': 1.0,
            'pessimistic': 0.9
        }
        multiplier = scenario_multipliers.get(scenario, 1.0)
        
        # Calculate time-based decay
        event_date = pd.to_datetime(event['date'])
        months_since = (forecast_date.year - event_date.year) * 12 + (forecast_date.month - event_date.month)
        lag_months = event.get('lag_months', 6)
        duration_months = event.get('duration_months', 24)
        decay_rate = event.get('decay_rate', 0.03)
        
        if months_since < lag_months:
            # Before lag period
            return 0
        elif months_since <= lag_months + 12:  # First year after lag
            # Ramp up to peak
            months_after_lag = months_since - lag_months
            time_factor = min(1.0, months_after_lag / 12)
            return base_impact * multiplier * time_factor
        elif months_since <= duration_months:
            # Decay period
            months_after_peak = months_since - (lag_months + 12)
            decay_factor = max(0.1, 1.0 - decay_rate * months_after_peak)
            return base_impact * multiplier * decay_factor
        else:
            # Impact has ended
            return 0
    
    def generate_scenarios(self, indicator_code: str, years_ahead: int = 3) -> Dict:
        """Generate multiple forecast scenarios"""
        
        scenarios = {}
        
        for scenario in ['pessimistic', 'base', 'optimistic']:
            try:
                forecast = self.event_augmented_forecast(
                    indicator_code, scenario, years_ahead
                )
                scenarios[scenario] = forecast
            except Exception as e:
                print(f"Warning: Failed to generate {scenario} scenario for {indicator_code}: {e}")
                # Fall back to trend forecast
                try:
                    forecast = self.trend_forecast(indicator_code, years_ahead)
                    scenarios[scenario] = forecast
                except:
                    # Last resort: simple projection
                    scenarios[scenario] = self._create_simple_baseline(indicator_code, years_ahead)
        
        # Calculate scenario ranges
        if scenarios:
            values = np.array([scenarios[s]['adjusted_values'] for s in scenarios 
                              if 'adjusted_values' in scenarios[s]])
            
            if len(values) > 0:
                scenario_range = {
                    'min': values.min(axis=0).tolist(),
                    'max': values.max(axis=0).tolist(),
                    'mean': values.mean(axis=0).tolist(),
                    'std': values.std(axis=0).tolist(),
                    'range_size': (values.max(axis=0) - values.min(axis=0)).tolist()
                }
            else:
                scenario_range = {}
            
            return {
                'scenarios': scenarios,
                'range_summary': scenario_range,
                'forecast_dates': scenarios.get('base', {}).get('forecast_dates', []),
                'indicator': indicator_code
            }
        
        return {}
    
    def forecast_to_dataframe(self, indicator_code: str, 
                            include_scenarios: bool = True) -> pd.DataFrame:
        """Convert forecast results to DataFrame for visualization"""
        
        if include_scenarios:
            results = self.generate_scenarios(indicator_code)
            
            if not results or 'scenarios' not in results:
                return pd.DataFrame()
            
            # Create DataFrame with all scenarios
            dfs = []
            for scenario_name, scenario_data in results['scenarios'].items():
                if 'forecast_dates' not in scenario_data:
                    continue
                    
                for i, date in enumerate(scenario_data['forecast_dates']):
                    row = {
                        'date': date,
                        'indicator': indicator_code,
                        'scenario': scenario_name,
                        'value': scenario_data.get('adjusted_values', [0] * len(scenario_data['forecast_dates']))[i],
                        'ci_lower': scenario_data.get('ci_lower', [0] * len(scenario_data['forecast_dates']))[i],
                        'ci_upper': scenario_data.get('ci_upper', [0] * len(scenario_data['forecast_dates']))[i]
                    }
                    
                    # Add baseline if available
                    if 'baseline_values' in scenario_data:
                        row['baseline'] = scenario_data['baseline_values'][i]
                    
                    # Add event impacts if available
                    if 'event_impacts' in scenario_data:
                        row['event_impact'] = scenario_data['event_impacts'][i]
                    
                    dfs.append(row)
            
            return pd.DataFrame(dfs)
        else:
            # Single scenario forecast
            forecast = self.event_augmented_forecast(indicator_code, 'base')
            
            if 'forecast_dates' not in forecast:
                return pd.DataFrame()
            
            data = []
            for i, date in enumerate(forecast['forecast_dates']):
                row = {
                    'date': date,
                    'indicator': indicator_code,
                    'scenario': forecast.get('scenario', 'base'),
                    'value': forecast['adjusted_values'][i],
                    'ci_lower': forecast['ci_lower'][i],
                    'ci_upper': forecast['ci_upper'][i]
                }
                
                if 'baseline_values' in forecast:
                    row['baseline'] = forecast['baseline_values'][i]
                
                if 'event_impacts' in forecast:
                    row['event_impact'] = forecast['event_impacts'][i]
                
                data.append(row)
            
            return pd.DataFrame(data)
    
    def calculate_growth_rates(self, indicator_code: str) -> Dict:
        """Calculate historical and projected growth rates"""
        
        ts = self.prepare_time_series(indicator_code, 'Y')
        
        if len(ts) < 2:
            return {'error': 'Insufficient historical data'}
        
        # Historical growth rates
        historical_growth_rates = []
        historical_growth_pp = []
        
        for i in range(1, len(ts)):
            growth_rate = (ts.iloc[i] - ts.iloc[i-1]) / ts.iloc[i-1] * 100
            growth_pp = ts.iloc[i] - ts.iloc[i-1]
            
            historical_growth_rates.append(growth_rate)
            historical_growth_pp.append(growth_pp)
        
        # Projected growth from forecasts
        forecast_results = self.generate_scenarios(indicator_code, years_ahead=3)
        
        if not forecast_results:
            return {
                'historical_growth_rates': historical_growth_rates,
                'historical_growth_pp': historical_growth_pp,
                'avg_historical_growth_rate': np.mean(historical_growth_rates) if historical_growth_rates else None,
                'avg_historical_growth_pp': np.mean(historical_growth_pp) if historical_growth_pp else None,
                'latest_value': float(ts.iloc[-1]),
                'latest_date': ts.index[-1]
            }
        
        projected_growth = {}
        for scenario in ['pessimistic', 'base', 'optimistic']:
            if scenario in forecast_results['scenarios']:
                scenario_data = forecast_results['scenarios'][scenario]
                if 'adjusted_values' in scenario_data and len(scenario_data['adjusted_values']) >= 1:
                    last_historical = scenario_data.get('last_historical_value', ts.iloc[-1])
                    first_forecast = scenario_data['adjusted_values'][0]
                    
                    growth_rate = (first_forecast - last_historical) / last_historical * 100
                    growth_pp = first_forecast - last_historical
                    
                    projected_growth[scenario] = {
                        'growth_rate': growth_rate,
                        'growth_pp': growth_pp
                    }
        
        return {
            'historical_growth_rates': historical_growth_rates,
            'historical_growth_pp': historical_growth_pp,
            'avg_historical_growth_rate': np.mean(historical_growth_rates) if historical_growth_rates else None,
            'avg_historical_growth_pp': np.mean(historical_growth_pp) if historical_growth_pp else None,
            'projected_growth': projected_growth,
            'latest_value': float(ts.iloc[-1]),
            'latest_date': ts.index[-1]
        }
    
    def get_forecast_summary(self, indicator_codes: List[str] = None) -> pd.DataFrame:
        """Get summary table of forecasts for multiple indicators"""
        
        if indicator_codes is None:
            indicator_codes = ['ACC_OWNERSHIP', 'ACC_MM_ACCOUNT', 'USG_DIGITAL_PAYMENT']
        
        summary_data = []
        
        for indicator in indicator_codes:
            scenarios = self.generate_scenarios(indicator, years_ahead=3)
            
            if not scenarios or 'scenarios' not in scenarios:
                continue
            
            for scenario in ['pessimistic', 'base', 'optimistic']:
                if scenario in scenarios['scenarios']:
                    scenario_data = scenarios['scenarios'][scenario]
                    
                    if 'adjusted_values' in scenario_data and len(scenario_data['adjusted_values']) >= 3:
                        for year_idx, date in enumerate(scenario_data['forecast_dates']):
                            if year_idx < 3:  # Only next 3 years
                                summary_data.append({
                                    'Indicator': indicator,
                                    'Year': date.year,
                                    'Scenario': scenario.capitalize(),
                                    'Forecast (%)': round(scenario_data['adjusted_values'][year_idx], 1),
                                    'CI_Lower (%)': round(scenario_data['ci_lower'][year_idx], 1) if 'ci_lower' in scenario_data else None,
                                    'CI_Upper (%)': round(scenario_data['ci_upper'][year_idx], 1) if 'ci_upper' in scenario_data else None
                                })
        
        return pd.DataFrame(summary_data)