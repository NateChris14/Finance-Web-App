#Function to store the database configurations
import os
import sys
from src.exception import CustomException
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd
import dill
from sklearn.base import BaseEstimator, TransformerMixin


# Loading the database credentials from the .env file
load_dotenv()

#Getting the database details and storing it
def get_db_url():
    try:
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT","5432")
        db = os.getenv("DB_NAME")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    except Exception as e:
        raise CustomException(e,sys)

#Function to load data from the database in batches
def load_data(join: bool = False,chunksize :int = None,columns:list = None, limit:int = None):
    engine = create_engine(get_db_url())

    #Building the select clause
    cols = ", ".join(columns) if columns else "*"

    #Defining the query with optional join
    if join:
        query = f"""
        SELECT {cols}
        FROM stock_data sd
        JOIN technical_indicators ti
        ON sd.ticker = ti.ticker AND sd.date = ti.date
        """

    else:
        query = f"SELECT {cols} FROM stock_data"

    if limit:
        query += f"LIMIT {limit}"

    if chunksize:
        return pd.read_sql(query, engine, chunksize=chunksize)
    else:
        df = pd.read_sql(query, engine)
        engine.dispose()
        return df
    
#Function to save an object 
def save_object(file_path, obj):
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path,exist_ok=True)

        with open(file_path,"wb") as file_obj:
            dill.dump(obj,file_obj)
    
    except Exception as e:
        raise CustomException(e,sys)
    

#Specifying a custom class for FeatureEngineering
class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self, keep_ticker=True):
        self.keep_ticker = keep_ticker
        self.tickers_ = None #to store the tickers for mapping later

    def fit(self,X,y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X['date'] = pd.to_datetime(X['date'])
        X = X.sort_values(by=['ticker','date'])

        X['daily_return'] = X.groupby('ticker')['close'].pct_change()
        X['rolling_volatility'] = X.groupby('ticker')['daily_return'].rolling(window=3).std().reset_index(level=0, drop=True)
        X['avg_volume'] = X.groupby('ticker')['volume'].rolling(window=3).mean().reset_index(level=0,drop=True)
        X['trend_strength'] = (X['close'] - X['sma']) / X['sma']
        X['volatility_range'] = X['high'] - X['low']

        #Dropping rows with NaNs from rolling features
        X = X.dropna().reset_index(drop=True)

        #Saving tickers for downstream mapping
        if self.keep_ticker:
            self.tickers_ = X['ticker']

        #Dropping the non-numeric columns for clustering
        X = X.drop(columns=['date','ticker'])
        return X