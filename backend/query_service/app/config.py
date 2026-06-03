import os
from functools import lru_cache


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://pkb:pkb@localhost:5432/pkb_query",
    )
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8083"))
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3010,http://localhost:3000"
    ).split(",")
    DEV_AUTH_MODE: bool = os.getenv("DEV_AUTH_MODE", "true").lower() == "true"
    MOCK_RAG_ENABLED: bool = os.getenv("MOCK_RAG_ENABLED", "true").lower() == "true"
    MOCK_REGISTRY_ENABLED: bool = os.getenv("MOCK_REGISTRY_ENABLED", "true").lower() == "true"
    MOCK_LLM_ENABLED: bool = os.getenv("MOCK_LLM_ENABLED", "true").lower() == "true"

    RAG_SERVICE_URL: str = os.getenv("RAG_SERVICE_URL", "http://localhost:8091/api/v1")
    REGISTRY_SERVICE_URL: str = os.getenv("REGISTRY_SERVICE_URL", "http://localhost:8084/api/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

    DEV_USER_ID: str = "u-001"
    DEV_USER_NAME: str = "Инженер-конструктор"


@lru_cache
def get_settings() -> Settings:
    return Settings()
