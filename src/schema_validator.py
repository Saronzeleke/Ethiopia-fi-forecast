from typing import List, Dict
import pandas as pd

class SchemaValidator:
    """Validate data against defined schema"""
    
    SCHEMA = {
        'observation': {
            'required': ['pillar', 'indicator', 'value_numeric', 'observation_date'],
            'optional': ['source_url', 'confidence', 'notes']
        },
        'event': {
            'required': ['event_name', 'event_date', 'category'],
            'optional': ['description', 'source_url']
        },
        'impact_link': {
            'required': ['parent_id', 'pillar', 'related_indicator'],
            'optional': ['impact_magnitude', 'lag_months']
        }
    }
    
    def validate_record(self, record: pd.Series, record_type: str) -> List[str]:
        """Validate a single record against schema"""
        errors = []
        
        if record_type not in self.SCHEMA:
            errors.append(f"Unknown record type: {record_type}")
            return errors
        
        # Check required fields
        for field in self.SCHEMA[record_type]['required']:
            if field not in record or pd.isna(record[field]):
                errors.append(f"Missing required field: {field}")
        
        # Validate field types
        if 'value_numeric' in record and not pd.isna(record['value_numeric']):
            try:
                float(record['value_numeric'])
            except ValueError:
                errors.append("value_numeric must be numeric")
        
        if 'observation_date' in record and not pd.isna(record['observation_date']):
            try:
                pd.to_datetime(record['observation_date'])
            except ValueError:
                errors.append("Invalid date format")
        
        return errors