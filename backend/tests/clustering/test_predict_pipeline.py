import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from src.components.clustering.pipeline.predict_pipeline import PredictPipeline
from src.exception import CustomException

class TestPredictPipeline(unittest.TestCase):
    @patch('src.components.clustering.pipeline.predict_pipeline.load_object')
    def test_predict_clusters_success(self, mock_load_object):
        mock_model = MagicMock()
        mock_model.fit_predict.return_value = np.array([0, 1])
        mock_preprocessor = MagicMock()
        mock_preprocessor.transform.return_value = np.zeros((2,3))
        mock_load_object.side_effect = [mock_model, mock_preprocessor]
        pipeline = PredictPipeline()
        df = pd.DataFrame({'a':[1,2],'b':[3,4],'c':[5,6]})
        result = pipeline.predict_clusters(df)
        self.assertEqual(result.shape, (2,4))
        self.assertIn('clusters', result.columns)

    @patch('src.components.clustering.pipeline.predict_pipeline.load_object', side_effect=Exception('fail'))
    def test_predict_clusters_exception(self, mock_load_object):
        with self.assertRaises(Exception):
            PredictPipeline()

if __name__ == '__main__':
    unittest.main() 