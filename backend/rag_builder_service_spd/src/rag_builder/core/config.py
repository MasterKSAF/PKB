# src/rag_builder/core/config.py

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    """
    Настройки сервиса.

    Значения читаются из .env файла.
    """

    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    POSTGRES_SCHEMA: str = "nsi"

    EMBEDDING_PROVIDER: str = "stub"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_PRICE_PER_1M_TOKENS_USD: float = 0.02
    EMBEDDING_DIM: int = 1536

    OPENAI_API_KEY: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )


settings = Settings()