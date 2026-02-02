import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from datetime import datetime

class DataLoader:
    """Load and validate financial inclusion data for Ethiopia"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def load_data(self, data_path: str, ref_codes_path: str) -> Dict[str, pd.DataFrame]:
        """
        Load unified data and reference codes with validation
        
        Parameters:
        -----------
        data_path : str
            Path to ethiopia_fi_unified_data.csv
        ref_codes_path : str
            Path to reference_codes.csv
            
        Returns:
        --------
        Dict containing 'data' and 'reference_codes' DataFrames
        """
        try:
            # Load main dataset
            data = pd.read_csv(
    data_path,
    parse_dates=['observation_date', 'period_start', 'period_end']
)

            
            # Load reference codes
            ref_codes = pd.read_csv(ref_codes_path)
            
            # Validate data structure
            self._validate_schema(data, ref_codes)
            
            return {
                'data': data,
                'reference_codes': ref_codes
            }
            
        except FileNotFoundError as e:
            self.logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    def _validate_schema(self, data: pd.DataFrame, ref_codes: pd.DataFrame):
        """Validate data against schema and reference codes"""
        required_columns = [
            'record_type', 'pillar', 'indicator', 'indicator_code',
            'value_numeric', 'observation_date', 'source_name'
        ]
        
        # Check required columns
        missing_cols = [col for col in required_columns if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        # Validate record types
        valid_record_types = ref_codes[ref_codes['field'] == 'record_type']['code'].tolist()
        invalid_records = data[~data['record_type'].isin(valid_record_types)]
        if len(invalid_records) > 0:
            self.logger.warning(f"Found {len(invalid_records)} records with invalid record_type")