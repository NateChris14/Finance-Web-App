import sys
from src.exception import CustomException
from src.logger import logging
from src.components.clustering.data_ingestion import DataIngestion
from src.components.clustering.data_transformation import DataTransformation
from src.components.clustering.model_trainer import ModelTrainer

class TrainPipeline:
    def __init__(self):
        pass

    def run(self):
        try:
            logging.info("Starting the training pipeline")

            #Data Ingestion
            data_ingestion = DataIngestion()
            raw_path = data_ingestion.initiate_data_ingestion()
            logging.info(f"Data Ingestion Completed: {raw_path}")

            #Data Transformation
            data_transformation = DataTransformation()
            array, preprocessor_path = data_transformation.initiate_data_transformation(raw_path)
            logging.info(f"Data Transformation Completed. Preprocessor saved at {preprocessor_path}")

            #Model Trainer
            model_trainer = ModelTrainer()
            model_score = model_trainer.initiate_model_trainer(array)
            logging.info(f"Model completed with silhoutte score: {model_score}")

        except Exception as e:
            logging.error("Error occured in training pipeline")
            raise CustomException(e,sys)
        
if __name__ == '__main__':
    pipeline = TrainPipeline()
    pipeline.run()
