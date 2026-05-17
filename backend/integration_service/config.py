import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from pydantic import field_validator

PROJECT_ROOT = Path(__file__).parent.resolve()

class Settings(BaseSettings):
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DATABASE: str
    DB_HOST: str
    DB_PORT: str
    
    STORAGE_DIRECTORIES: list[Path] = [
        PROJECT_ROOT / "files1",
        PROJECT_ROOT / "files2"
    ]
    
    @field_validator('STORAGE_DIRECTORIES', mode='before')
    @classmethod
    def parse_and_resolve_dirs(cls, v):
        if isinstance(v, str):
            return [PROJECT_ROOT / d.strip() for d in v.split(',')]
        return v
    
    @property
    def database_url(self):
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        
    class Config:
        env_file = ".env"

settings = Settings()

for path in settings.STORAGE_DIRECTORIES:
    os.makedirs(path, exist_ok=True)

