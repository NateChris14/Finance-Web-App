import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from src.components.clustering.model_trainer import ModelTrainer
from src.exception import CustomException
import pandas as pd

class TestModelTrainer(unittest.TestCase):
    def setUp(self):
        self.trainer = ModelTrainer()

    @patch('src.components.clustering.model_trainer.mlflow')
    @patch('src.components.clustering.model_trainer.save_object')
    @patch('src.components.clustering.model_trainer.pd.read_csv')
    @patch('src.components.clustering.model_trainer.DataIngestion')
    def test_initiate_model_trainer_success(self, mock_data_ingestion, mock_read_csv, mock_save_object, mock_mlflow):
        mock_data_ingestion.return_value.initiate_data_ingestion.return_value = 'dummy.csv'
        mock_read_csv.return_value = pd.DataFrame({
            'ticker': ['A'], 'date': ['2020-01-01'], 'open': [1], 'high': [1], 'low': [1], 'close': [1], 'volume': [1],
            'rsi': [1], 'macd': [1], 'sma': [1], 'ema': [1], 'atr': [1], 'bb_upper': [1], 'bb_middle': [1], 'bb_lower': [1]
        })
        input_array = np.zeros((10,3))
        score = self.trainer.initiate_model_trainer(input_array)
        self.assertIsInstance(score, float)

    @patch('src.components.clustering.model_trainer.mlflow.start_run', side_effect=Exception('fail'))
    def test_initiate_model_trainer_exception(self, mock_start_run):
        with self.assertRaises(CustomException):
            self.trainer.initiate_model_trainer(np.zeros((1,3)))

if __name__ == '__main__':
    unittest.main() 