import sys
from dataclasses import dataclass
import numpy as np
import pandas as pd

from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from feature_engine.outliers import Winsorizer
from feature_engine.selection import DropDuplicateFeatures
from src.utils import FeatureEngineer
from sklearn.decomposition import PCA

import os
from src.utils import save_object

from src.exception import CustomException
from src.logger import logging

@dataclass
class DataTransformationConfig:
    preprocessor_ob_file_path = os.path.join(os.getcwd(),'artifacts','preprocessor.pkl')

class DataTransformation:
    def __init__(self):
        self.data_transformation_config = DataTransformationConfig()

    def get_data_transformer_object(self):
        """This function is responsible for data transformation"""

        try:
            columns = ['ticker','date','open','high','low','close','volume','rsi','macd','sma','ema','atr','bb_upper','bb_middle','bb_lower']

            #Pipeline
            transformer = Pipeline(steps=[
                ("drop_duplicate_features",DropDuplicateFeatures()),
                ("feature_engineering", FeatureEngineer()),
                ("Outlier removal", Winsorizer(capping_method='iqr',tail='both',fold=1.5)),
                ("Scaling",RobustScaler()),
                ("Dimensionality Reduction",PCA(n_components=3))
                
            ])

            logging.info(f"Columns : {columns}")

            preprocessor = ColumnTransformer(transformers=[
                ("transform",transformer,columns)
            ])

            return preprocessor
        
        except Exception as e:
            raise CustomException(e,sys)
        

    def initiate_data_transformation(self,raw_path):
        try:
            df = pd.read_csv(raw_path)

            logging.info("Read data completed!")

            logging.info("Obtaining preprocessing object")

            preprocessor_obj = self.get_data_transformer_object()

            logging.info("Applying preprocessing object on raw df")

            input_feature_arr = preprocessor_obj.fit_transform(df)

            arr = np.array(input_feature_arr)

            logging.info("Saving preprocessor object")

            save_object(
                file_path=self.data_transformation_config.preprocessor_ob_file_path,
                obj=preprocessor_obj

            )

            return(
                arr,
                self.data_transformation_config.preprocessor_ob_file_path
            )
        
        except Exception as e:
            raise CustomException(e,sys)
        

if __name__ == '__main__':
    raw_data_path = os.path.join(os.getcwd(),'data','stock_cluster.csv')
    obj = DataTransformation()
    obj.get_data_transformer_object()
    obj.initiate_data_transformation(raw_data_path)




