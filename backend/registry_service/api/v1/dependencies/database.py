import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from services.logger import log_event

username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
database = os.getenv('DB_DATABASE')

DATABASE_URL = f'postgresql://{username}:{password}@{host}:{port}/{database}'

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        log_event('ERROR', 'database_connection', error=f"Database connection or operation failed: {str(e)}")
        raise
    finally:
        db.close()

