# tests/test_data_loader.py
import pytest
import pandas as pd
from src.data_loader import DataLoader

class TestDataLoader:
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    def test_load_data_success(self, loader, tmp_path):
        # Create test data
        test_data = pd.DataFrame({
            'record_type': ['observation', 'event'],
            'pillar': ['access', None],
            'indicator': ['Account ownership', None],
            'value_numeric': [45.5, None]
        })
        
        test_data_path = tmp_path / "test_data.csv"
        test_ref_path = tmp_path / "test_ref.csv"
        
        test_data.to_csv(test_data_path, index=False)
        pd.DataFrame({
            'field': ['record_type', 'pillar'],
            'code': ['observation', 'access'],
            'label': ['Observation', 'Access']
        }).to_csv(test_ref_path, index=False)
        
        # Test loading
        result = loader.load_data(str(test_data_path), str(test_ref_path))
        assert 'data' in result
        assert 'reference_codes' in result
        assert len(result['data']) == 2
    
    def test_load_data_file_not_found(self, loader):
        with pytest.raises(FileNotFoundError):
            loader.load_data('nonexistent.csv', 'nonexistent_ref.csv')