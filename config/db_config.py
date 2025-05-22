from sqlalchemy.engine import URL
from dotenv import load_dotenv

def get_db_url():
    return URL.create(
        drivername="postgresql+psycopg2",
        username="postgres",
        password="postgres14",
        host="postgres.c7oayqqgg723.eu-north-1.rds.amazonaws.com",
        port=5432,
        database="postgres"
    )