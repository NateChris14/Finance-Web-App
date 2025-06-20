import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from src.components.clustering.data_transformation import DataTransformation
from src.exception import CustomException
import os

class TestDataTransformation(unittest.TestCase):
    def setUp(self):
        self.transformation = DataTransformation()

    def test_get_data_transformer_object(self):
        preprocessor = self.transformation.get_data_transformer_object()
        self.assertIsNotNone(preprocessor)

    @patch('src.components.clustering.data_transformation.pd.read_csv')
    @patch('src.components.clustering.data_transformation.save_object')
    def test_initiate_data_transformation_success(self, mock_save_object, mock_read_csv):
        mock_df = MagicMock()
        mock_read_csv.return_value = mock_df
        preprocessor = self.transformation.get_data_transformer_object()
        with patch.object(preprocessor, 'fit_transform', return_value=np.zeros((1,3))):
            with patch.object(self.transformation, 'get_data_transformer_object', return_value=preprocessor):
                arr, path = self.transformation.initiate_data_transformation('dummy.csv')
                self.assertEqual(arr.shape, (1,3))
                self.assertTrue(os.path.normpath(path).endswith(os.path.normpath('artifacts/clustering/preprocessor.pkl')))

    @patch('src.components.clustering.data_transformation.pd.read_csv', side_effect=Exception('fail'))
    def test_initiate_data_transformation_exception(self, mock_read_csv):
        with self.assertRaises(CustomException):
            self.transformation.initiate_data_transformation('dummy.csv')

if __name__ == '__main__':
    unittest.main() 