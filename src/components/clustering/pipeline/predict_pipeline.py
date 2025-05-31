import os
import sys
import pandas as pd
from src.exception import CustomException
from src.logger import logging
from src.utils import load_object

class PredictPipeline:
    def __init__(self):
        model_path = 'artifacts/model.pkl'
        preprocessor_path = 'artifacts/preprocessor.pkl'
        self.model = load_object(file_path=model_path)
        self.preprocessor = load_object(file_path=preprocessor_path)

    def predict_clusters(self, df: pd.DataFrame) -> pd.DataFrame:

        # Transforming the data
        transformed = self.preprocessor.transform(df)
        clusters = self.model.fit_predict(transformed)

        #Storing the 3d data to be visualised
        df_3d = pd.DataFrame(transformed,columns=['col1','col2','col3'])
        df_3d['clusters'] = clusters

        return df_3d
