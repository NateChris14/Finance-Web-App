import unittest
from unittest.mock import patch, MagicMock
import os
from src.components.clustering.data_ingestion import DataIngestion
from src.exception import CustomException

class TestDataIngestion(unittest.TestCase):
    @patch('src.components.clustering.data_ingestion.load_data')
    @patch('pandas.concat')
    def test_initiate_data_ingestion_success(self, mock_concat, mock_load_data):
        import pandas as pd
        mock_df = pd.DataFrame({'a': [1]})
        mock_concat.return_value = mock_df
        mock_load_data.return_value = [mock_df]
        with patch.object(mock_df, 'to_csv') as mock_to_csv:
            ingestion = DataIngestion()
            result = ingestion.initiate_data_ingestion()
            self.assertTrue(result.replace('\\', '/').endswith('data/stock_cluster.csv'))
            mock_to_csv.assert_called_once()

    @patch('src.components.clustering.data_ingestion.load_data', side_effect=Exception('fail'))
    def test_initiate_data_ingestion_exception(self, mock_load_data):
        ingestion = DataIngestion()
        with self.assertRaises(CustomException):
            ingestion.initiate_data_ingestion()

if __name__ == '__main__':
    unittest.main() 