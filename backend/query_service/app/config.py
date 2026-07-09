from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://pkb:pkb@localhost:5432/pkb_query",
        alias="DATABASE_URL",
    )
    APP_HOST: str = Field(default="0.0.0.0", alias="APP_HOST")
    APP_PORT: int = Field(default=8083, alias="APP_PORT")
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3010", "http://localhost:3000"],
        alias="CORS_ORIGINS",
    )
    DEV_AUTH_MODE: bool = Field(default=True, alias="DEV_AUTH_MODE")
    MOCK_RAG_ENABLED: bool = Field(default=False, alias="MOCK_RAG_ENABLED")
    MOCK_REGISTRY_ENABLED: bool = Field(default=False, alias="MOCK_REGISTRY_ENABLED")
    MOCK_LLM_ENABLED: bool = Field(default=False, alias="MOCK_LLM_ENABLED")

    RAG_SERVICE_URL: str = Field(default="http://localhost:8091", alias="RAG_SERVICE_URL")
    REGISTRY_SERVICE_URL: str = Field(default="http://localhost:8084/api/v1", alias="REGISTRY_SERVICE_URL")

    LLM_API_URL: str = Field(..., alias="LLM_API_URL")
    LLM_MODEL: str = Field(..., alias="LLM_MODEL")
    LLM_API_KEY: str = Field(default="", alias="LLM_API_KEY")
    LLM_MAX_TOKENS: int = Field(default=8196, alias="LLM_MAX_TOKENS")
    LLM_TIMEOUT: int = Field(default=120, alias="LLM_TIMEOUT")

    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="signoz-otel-collector:4317",
        alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )

    DEV_USER_ID: str = "u-001"
    DEV_USER_NAME: str = "Инженер-конструктор"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
