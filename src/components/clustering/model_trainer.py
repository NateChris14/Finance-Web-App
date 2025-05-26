import os
import sys
from dataclasses import dataclass

import mlflow.sklearn
from sklearn.cluster import AgglomerativeClustering,KMeans,DBSCAN
from sklearn.metrics import silhouette_score

from src.exception import CustomException
from src.logger import logging
from src.utils import save_object,FeatureEngineer
from src.components.clustering.data_ingestion import DataIngestion
from src.components.clustering.data_transformation import DataTransformation
import pandas as pd
import mlflow
import mlflow.sklearn

mlflow.set_tracking_uri("http://127.0.0.1:5000")

@dataclass
class ModelTrainerConfig:
    trained_model_file_path = os.path.join(os.getcwd(),'artifacts','model.pkl')

class ModelTrainer:
    def __init__(self):
        self.model_trainer_config = ModelTrainerConfig()

    def initiate_model_trainer(self,input_array):
        try:
            with mlflow.start_run(run_name="cluster_model_training"):
                logging.info("Getting the preprocessed array")
                
                #Initializing the model
                AC = AgglomerativeClustering(n_clusters=4,linkage='ward')

                #Adding the clusters feature to the original dataframe

                #Creating the data ingestion object
                obj = DataIngestion()
                path = obj.initiate_data_ingestion()
                
                #Getting the dataframe 
                df_update = pd.read_csv(path)

                reduced_dimension_df = pd.DataFrame(input_array,columns=['col1','col2','col3'])

                #Fitting the model and predicting clusters
                y_hat = AC.fit_predict(input_array)

                #Storing the cluster predictions
                reduced_dimension_df['Clusters'] = y_hat

                # Performing feature engineering before adding the cluster labels
                fe = FeatureEngineer()
                df_final = fe.fit_transform(df_update)
                tickers = fe.tickers_

                #Adding the cluster feature
                df_final['Clusters'] = y_hat

                #Getting the silhoutte score
                X = reduced_dimension_df[['col1','col2','col3']]
                labels = reduced_dimension_df['Clusters']

                # Calculate silhouette score
                score = silhouette_score(X, labels)
                print(f'Silhouette Score: {score:.4f}')
                mlflow.log_metric("silhoutte-score",score)

                #Logging the model
                mlflow.sklearn.log_model(AC, artifact_path="models")

                logging.info(f"Model with silhoutte score : {score}")

                save_object(
                    file_path=self.model_trainer_config.trained_model_file_path,
                    obj=AC
                )

                #Saving the artifact on mlflow
                mlflow.log_artifact(self.model_trainer_config.trained_model_file_path)

                return score
            
        except Exception as e:
            raise CustomException(e,sys)
        
if __name__ == '__main__':
    raw_data_path = os.path.join(os.getcwd(),'data','stock_cluster.csv')
    tf = DataTransformation()
    arr,path = tf.initiate_data_transformation(raw_path=raw_data_path)
    mt = ModelTrainer()
    score = mt.initiate_model_trainer(arr)
    print(score)

