import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_enricher import DataEnricher

class TestDataEnricher:
    """Test suite for DataEnricher class"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample base dataset matching the schema"""
        return pd.DataFrame({
            'record_id': ['REC_0001', 'REC_0002', 'EVT_0001'],
            'record_type': ['observation', 'observation', 'event'],
            'pillar': ['ACCESS', 'ACCESS', None],
            'indicator': ['Account Ownership Rate', 'Account Ownership Rate', 'Telebirr Launch'],
            'indicator_code': ['ACC_OWNERSHIP', 'ACC_OWNERSHIP', 'EVT_TELEBIRR'],
            'value_numeric': [22.0, 35.0, None],
            'observation_date': ['2014-12-31', '2017-12-31', None],
            'event_date': [None, None, '2021-05-17'],
            'source_name': ['Findex 2014', 'Findex 2017', 'Ethio Telecom'],
            'confidence': ['high', 'high', 'high']
        })
    
    @pytest.fixture
    def enricher(self, sample_data):
        return DataEnricher(sample_data)
    
    def test_initialization(self, enricher, sample_data):
        """Test that enricher initializes correctly"""
        assert len(enricher.base_data) == 3
        assert len(enricher.new_records) == 0
        assert 'record_type' in enricher.base_data.columns
    
    def test_add_findex_microdata(self, enricher):
        """Test adding Findex microdata"""
        enricher.add_findex_microdata()
        
        # Should add 5 records (2011, 2014, 2017, 2021, 2024)
        assert len(enricher.new_records) == 5
        
        # Check first record structure
        first_record = enricher.new_records[0]
        assert first_record['record_type'] == 'observation'
        assert first_record['pillar'] == 'access'
        assert first_record['indicator'] == 'Account ownership, female (% age 15+)'
        assert first_record['indicator_code'] == 'FINDEX_ACCOUNT_FEMALE'
        assert isinstance(first_record['value_numeric'], float)
        assert '2011-12-31' in str(first_record['observation_date'])
        assert first_record['confidence'] == 'high'
    
    def test_add_nbe_infrastructure_data(self, enricher):
        """Test adding NBE infrastructure data"""
        enricher.add_nbe_infrastructure_data()
        
        # Should add 6 records (3 ATM + 3 branch density)
        assert len(enricher.new_records) == 6
        
        # Check infrastructure records
        infra_records = [r for r in enricher.new_records 
                        if r['indicator_code'] in ['INFRA_ATM_DENSITY', 'INFRA_BRANCH_DENSITY']]
        assert len(infra_records) == 6
        
        # Verify data types and ranges
        for record in infra_records:
            assert record['record_type'] == 'observation'
            assert record['pillar'] == 'infrastructure'
            assert isinstance(record['value_numeric'], float)
            assert 6.0 <= record['value_numeric'] <= 8.5
            assert record['confidence'] == 'high'
    
    def test_add_gsma_mobile_data(self, enricher):
        """Test adding GSMA mobile data"""
        enricher.add_gsma_mobile_data()
        
        # Should add 8 records (4 mobile penetration + 4 4G coverage)
        assert len(enricher.new_records) == 8
        
        # Check mobile penetration records
        mobile_records = [r for r in enricher.new_records 
                         if r['indicator_code'] == 'GSMA_MOBILE_PENETRATION']
        assert len(mobile_records) == 4
        
        # Verify year coverage
        years = [record['observation_date'][:4] for record in mobile_records]
        assert '2021' in years
        assert '2024' in years
        
        # Verify value ranges
        for record in mobile_records:
            assert 44 <= record['value_numeric'] <= 55
    
    def test_add_policy_events(self, enricher):
        """Test adding policy events"""
        enricher.add_policy_events()
        
        # Should add 2 policy events
        assert len(enricher.new_records) == 2
        
        # Check event structure
        for record in enricher.new_records:
            assert record['record_type'] == 'event'
            assert record['category'] == 'policy'
            assert record['confidence'] == 'high'
            assert 'event_name' in record
            assert 'event_date' in record
    
    def test_add_impact_links(self, enricher):
        """Test adding impact links"""
        enricher.add_impact_links()
        
        # Should add 2 impact links
        assert len(enricher.new_records) == 2
        
        # Check impact link structure
        for record in enricher.new_records:
            assert record['record_type'] == 'impact_link'
            assert 'parent_id' in record
            assert 'pillar' in record
            assert 'impact_direction' in record
            assert 'impact_magnitude' in record
            assert isinstance(record['lag_months'], int)
    
    def test_get_enriched_data(self, enricher):
        """Test combining original and new data"""
        # Add some test data
        enricher.add_findex_microdata()
        enricher.add_policy_events()
        
        enriched = enricher.get_enriched_data()
        
        # Should have original + new records
        assert len(enriched) == 3 + 5 + 2  # Original: 3, Findex: 5, Policies: 2
        assert 'record_id' in enriched.columns
        assert 'record_type' in enriched.columns
        
        # Check column alignment
        original_cols = set(enricher.base_data.columns)
        enriched_cols = set(enriched.columns)
        assert original_cols == enriched_cols
        
        # Check data types
        assert pd.api.types.is_numeric_dtype(enriched['value_numeric'])
    
    def test_enriched_data_integrity(self, enricher):
        """Test data integrity after enrichment"""
        # Add all enrichments
        enricher.add_findex_microdata()
        enricher.add_nbe_infrastructure_data()
        enricher.add_gsma_mobile_data()
        enricher.add_policy_events()
        enricher.add_impact_links()
        
        enriched = enricher.get_enriched_data()
        
        # No duplicate record_ids
        if 'record_id' in enriched.columns:
            assert enriched['record_id'].is_unique or enriched['record_id'].isna().any()
        
        # Required columns present
        required_cols = ['record_type', 'indicator', 'value_numeric']
        for col in required_cols:
            assert col in enriched.columns
        
        # No mixed data types in critical columns
        assert pd.api.types.is_numeric_dtype(enriched['value_numeric'])
    
    def test_empty_base_data(self):
        """Test with empty base dataset"""
        empty_data = pd.DataFrame(columns=['record_type', 'pillar', 'indicator'])
        enricher = DataEnricher(empty_data)
        enricher.add_findex_microdata()
        
        enriched = enricher.get_enriched_data()
        assert len(enriched) == 5  # Only new records
        assert 'record_type' in enriched.columns
    
    def test_missing_columns_handling(self):
        """Test handling of datasets with missing expected columns"""
        minimal_data = pd.DataFrame({
            'record_type': ['observation'],
            'value': [100]  # Non-standard column name
        })
        
        # Should handle gracefully
        enricher = DataEnricher(minimal_data)
        enricher.add_findex_microdata()
        
        enriched = enricher.get_enriched_data()
        assert 'record_type' in enriched.columns
        assert 'value' in enriched.columns  # Original column preserved
    
    @pytest.mark.parametrize("method_name", [
        'add_findex_microdata',
        'add_nbe_infrastructure_data', 
        'add_gsma_mobile_data',
        'add_policy_events',
        'add_impact_links'
    ])
    def test_methods_return_none(self, enricher, method_name):
        """Test that enrichment methods return None (modify in-place)"""
        method = getattr(enricher, method_name)
        result = method()
        assert result is None
        
    def test_confidence_values(self, enricher):
        """Test that confidence values are valid"""
        enricher.add_findex_microdata()
        enricher.add_nbe_infrastructure_data()
        enricher.add_gsma_mobile_data()
        
        enriched = enricher.get_enriched_data()
        
        if 'confidence' in enriched.columns:
            valid_confidences = ['high', 'medium', 'low', 'estimated']
            invalid = enriched[~enriched['confidence'].isin(valid_confidences) & enriched['confidence'].notna()]
            assert len(invalid) == 0, f"Invalid confidence values: {invalid['confidence'].unique()}"