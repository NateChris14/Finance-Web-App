#Function to store the database configurations
import os
import sys
from src.exception import CustomException
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd

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