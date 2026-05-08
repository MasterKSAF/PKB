from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# For Development only
# For production use environment variables only!


try:
    import env
except ImportError:
    pass

PASSWORD = os.getenv("DB_PASSWORD", "")
DATABASE = os.getenv("DB_DATABASE", "")
USERNAME = os.getenv("DB_USERNAME", "")
HOST = os.getenv("DB_HOST","")
PORT = int(os.getenv("DB_PORT", "5432"))

DATABASE_URL = f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
