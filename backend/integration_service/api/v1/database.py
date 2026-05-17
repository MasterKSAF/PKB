from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sys
from pathlib import Path

# Add integration_service root to sys.path so config can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
