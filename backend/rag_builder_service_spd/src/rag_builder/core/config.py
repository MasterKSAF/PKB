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
    EMBEDDING_MODEL: str = "qwen3-embedding-4b"
    EMBEDDING_PRICE_PER_1M_TOKENS_USD: float = 0.0
    EMBEDDING_DIM: int = 2048

    EMBEDDING_API_MODE: str = "infinity"
    EMBEDDING_API_BASE_URL: str | None = None
    EMBEDDING_API_KEY: str | None = None

    OPENAI_API_KEY: str | None = None

    CHUNK_STRATEGY: str = "semantic_1024"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )


settings = Settings()