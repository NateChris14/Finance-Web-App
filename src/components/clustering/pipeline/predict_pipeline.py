import os
import sys
import pandas as pd
from src.exception import CustomException
from src.logger import logging
from src.utils import load_object

class PredictPipeline:
    def __init__(self):
        model_path = 'artifact/model.pkl'
        preprocessor_path = 'artifact/preprocessor.pkl'
        self.model = load_object(file_path=model_path)
        self.preprocessor = load_object(file_path=preprocessor_path)

    def predict_clusters(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            features = df.columns
            data_scaled = self.preprocessor.transform(features)
            clusters = self.model.predict(data_scaled)
            df['cluster'] = clusters
            return df
        except Exception as e:
            raise CustomException(e,sys) 
