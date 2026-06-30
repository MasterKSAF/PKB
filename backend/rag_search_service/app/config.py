"""Конфигурация сервиса: app_settings.yaml (primary) + env vars (override)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Путь к app_settings.yaml (рядом с корнем проекта)
_APP_SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "app_settings.yaml"


def _load_yaml_config() -> dict:
    """Загрузить app_settings.yaml (если существует)."""
    if _APP_SETTINGS_PATH.exists():
        with open(_APP_SETTINGS_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _yaml_value(yaml_cfg: dict, dotpath: str, default=None):
    """Получить значение из YAML по dotpath (например, 'rag.search_strategy')."""
    keys = dotpath.split(".")
    val = yaml_cfg
    for key in keys:
        if isinstance(val, dict):
            val = val.get(key)
        else:
            return default
    return val if val is not None else default


class Settings(BaseSettings):
    """Корневой объект настроек, загружается из YAML + env."""

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
        default="password,access_token,refresh_token", alias="LOG_PII_FIELDS"
    )

    # --- Database ---
    postgres_user: str = Field(
        default="rag_user",
        validation_alias=AliasChoices("DB_USERNAME", "POSTGRES_USER"),
    )
    postgres_password: str = Field(
        default="rag_password",
        validation_alias=AliasChoices("DB_PASSWORD", "POSTGRES_PASSWORD"),
    )
    postgres_db: str = Field(
        default="knowledge_base",
        validation_alias=AliasChoices("DB_DATABASE", "POSTGRES_DB"),
    )
    postgres_host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("DB_HOST", "POSTGRES_HOST"),
    )
    postgres_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("DB_PORT", "POSTGRES_PORT"),
    )
    postgres_pool_min: int = Field(default=2, alias="POSTGRES_POOL_MIN")
    postgres_pool_max: int = Field(default=10, alias="POSTGRES_POOL_MAX")

    # --- Embedding Provider ---
    embedding_api_key: str = Field(default="", alias="EMBEDDING_API_KEY")
    embedding_base_url: str = Field(default="http://infinity:7997", alias="EMBEDDING_BASE_URL")
    embedding_model: str = Field(default="Qwen/Qwen3-Embedding-0.6B", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=1024, alias="EMBEDDING_DIM")
    # Таймаут 10с — эмбеддинг один и мелкий, долгого ожидания быть не может, сразу retry.
    embedding_timeout: int = Field(default=10, alias="EMBEDDING_TIMEOUT")
    embedding_instruction: str = Field(default="", alias="EMBEDDING_INSTRUCTION")

    # --- Search ---
    search_strategy: str = Field(default="dense_rerank", alias="SEARCH_STRATEGY")
    search_top_k: int = Field(default=10, alias="SEARCH_TOP_K")
    search_max_top_k: int = Field(default=100, alias="SEARCH_MAX_TOP_K")
    search_rrf_k: int = Field(default=60, alias="SEARCH_RRF_K")
    search_fetch_multiplier: int = Field(default=2, alias="SEARCH_FETCH_MULTIPLIER")
    context_expansion: int = Field(default=2, alias="CONTEXT_EXPANSION")

    # --- Reranker (TEI) ---
    reranker_base_url: str = Field(default="http://tei-reranker:8080", alias="RERANKER_BASE_URL")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3-int8", alias="RERANKER_MODEL")
    reranker_timeout: int = Field(default=10, alias="RERANKER_TIMEOUT")
    reranker_fetch_multiplier: int = Field(default=5, alias="RERANKER_FETCH_MULTIPLIER")
    rerank_top_n: int = Field(default=50, alias="RERANK_TOP_N")

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


def _apply_yaml_overrides(settings: Settings) -> Settings:
    """Перезаписать дефолты Settings значениями из app_settings.yaml (если env не задан)."""
    yaml_cfg = _load_yaml_config()
    if not yaml_cfg:
        return settings

    # Маппинг: dotpath в YAML → attribute в Settings + env alias
    overrides = {
        "service.name": ("service_name", "SERVICE_NAME"),
        "service.version": ("service_version", "SERVICE_VERSION"),
        "rag.search_strategy": ("search_strategy", "SEARCH_STRATEGY"),
        "rag.embedding_dim": ("embedding_dim", "EMBEDDING_DIM"),
        "rag.top_k": ("search_top_k", "SEARCH_TOP_K"),
        "rag.context_expansion": ("context_expansion", "CONTEXT_EXPANSION"),
        "rag.rerank_url": ("reranker_base_url", "RERANKER_BASE_URL"),
        "rag.rerank_model": ("reranker_model", "RERANKER_MODEL"),
        "rag.rerank_top_n": ("rerank_top_n", "RERANK_TOP_N"),
        "rag.embedding_api.endpoint": ("embedding_base_url", "EMBEDDING_BASE_URL"),
        "rag.embedding_api.model": ("embedding_model", "EMBEDDING_MODEL"),
    }

    for dotpath, (attr, env_var) in overrides.items():
        # Env var имеет приоритет над YAML
        if os.getenv(env_var):
            continue
        yaml_val = _yaml_value(yaml_cfg, dotpath)
        if yaml_val is not None:
            setattr(settings, attr, yaml_val)

    # PII fields из YAML (если env не задан)
    if not os.getenv("LOG_PII_FIELDS"):
        yaml_pii = _yaml_value(yaml_cfg, "logging.pii_fields")
        if yaml_pii and isinstance(yaml_pii, list):
            settings.log_pii_fields = ",".join(yaml_pii)

    return settings


@lru_cache
def get_settings() -> Settings:
    """Кэшированный синглтон настроек (YAML + env override)."""
    settings = Settings()
    return _apply_yaml_overrides(settings)
