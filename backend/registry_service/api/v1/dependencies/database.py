from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Note: Ideally this URL should be retrieved from environment variables.
# Using a placeholder since the description states data will be in PostgreSQL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
