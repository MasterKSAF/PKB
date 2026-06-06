"""Конфигурация сервиса через pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Корневой объект настроек, загружается из .env и окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Service ---
    service_name: str = Field(default="rag-search", alias="SERVICE_NAME")
    service_version: str = Field(default="0.1.0", alias="SERVICE_VERSION")
    service_port: int = Field(default=8091, alias="SERVICE_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_pii_fields: str = Field(
        default="password,access_token,refresh_token", 
        alias="LOG_PII_FIELDS"
    )

    # --- Database ---
    postgres_user: str = Field(default="rag_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="rag_password", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="knowledge_base", alias="POSTGRES_DB")
    postgres_host: str = Field(default="127.0.0.1", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_pool_min: int = Field(default=2, alias="POSTGRES_POOL_MIN")
    postgres_pool_max: int = Field(default=10, alias="POSTGRES_POOL_MAX")

    # --- Embedding Provider ---
    embedding_api_key: str = Field(default="", alias="EMBEDDING_API_KEY")
    embedding_base_url: str = Field(
        default="https://api.openai.com/v1", alias="EMBEDDING_BASE_URL"
    )
    embedding_model: str = Field(
        default="intfloat/multilingual-e5-large", alias="EMBEDDING_MODEL"
    )
    embedding_dim: int = Field(default=1024, alias="EMBEDDING_DIM")
    embedding_timeout: int = Field(default=30, alias="EMBEDDING_TIMEOUT")

    # --- Search ---
    search_default_top_k: int = Field(default=10, alias="SEARCH_DEFAULT_TOP_K")
    search_max_top_k: int = Field(default=100, alias="SEARCH_MAX_TOP_K")
    search_rrf_k: int = Field(default=60, alias="SEARCH_RRF_K")
    search_fetch_multiplier: int = Field(default=2, alias="SEARCH_FETCH_MULTIPLIER")

    # --- Health Check ---
    health_check_timeout: int = Field(default=5, alias="HEALTH_CHECK_TIMEOUT")

    @property
    def pii_fields_list(self) -> list[str]:
        """Возвращает список PII-полей для маскирования в логах."""
        if not self.log_pii_fields:
            return []
        return [f.strip() for f in self.log_pii_fields.split(",") if f.strip()]

    @property
    def database_url(self) -> str:
        """DSN для asyncpg."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def use_local_embedding(self) -> bool:
        """Если API-ключ не задан — используем локальную модель."""
        return not bool(self.embedding_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Кэшированный синглтон настроек."""
    return Settings()