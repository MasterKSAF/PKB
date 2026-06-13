# src/rag_builder/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()