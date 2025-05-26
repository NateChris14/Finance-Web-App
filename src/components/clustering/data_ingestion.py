import os
import sys
from src.exception import CustomException
from src.logger import logging
from src.utils import load_data
import pandas as pd

from dataclasses import dataclass

@dataclass
class DataIngestionConfig:

    raw_data_path : str = os.path.join(os.getcwd(),'data','stock_cluster.csv')

class DataIngestion:
    def __init__(self):
        self.ingestion_config = DataIngestionConfig()

    def initiate_data_ingestion(self):
        logging.info("Entered the data ingestion component for clustering")
        try:
            #Specifying the columns to be imported
            columns = [
            "sd.ticker","sd.date","sd.open","sd.high","sd.low","sd.close","sd.volume",
            "ti.ticker","ti.date","ti.rsi","ti.macd","ti.sma","ti.ema","ti.atr","ti.bb_upper","ti.bb_middle","ti.bb_lower"]

            #Getting the data in batches
            data_chunks = load_data(join=True,columns=columns,chunksize=10000)

            #Loading the data into a single dataframe
            df = pd.concat(data_chunks,ignore_index=True)
            logging.info("Read the dataset as a dataframe")

            os.makedirs(os.path.dirname(self.ingestion_config.raw_data_path),exist_ok=True)

            df.to_csv(self.ingestion_config.raw_data_path,index=False,header=True)

            logging.info("Ingestion of the data is completed!")

            return self.ingestion_config.raw_data_path
        
        except Exception as e:
            raise CustomException(e,sys)


#if __name__ == '__main__':
    #raw_path = os.path.join(os.getcwd(),'data','stock_cluster.csv')
    #obj = DataIngestion()
    #obj.initiate_data_ingestion()
