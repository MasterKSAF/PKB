"""
Configuration module for Orchestrator Service.
Supports dual mode: real API calls or mock/stub mode for each external service.
"""

from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class ServiceConfig(BaseSettings):
    """Configuration for external services."""

    # Registry Service (port 8084)
    REGISTRY_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for registry service"
    )
    REGISTRY_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for registry service"
    )

    # RAG Service (port 8087)
    RAG_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for rag service"
    )
    RAG_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for rag service"
    )

    # OCR Service (port 8088)
    OCR_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for OCR service"
    )
    OCR_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for OCR service"
    )

    # Parser Service (port 8089)
    PARSER_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for parser service"
    )
    PARSER_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for parser service"
    )

    # Converter-Validator Service (port 8090)
    CONVERTER_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for converter-validator service"
    )
    CONVERTER_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for converter-validator service"
    )


class PipelineConfig(BaseSettings):
    """Pipeline execution parameters."""

    # Max retries per step before failing the pipeline
    MAX_STEP_RETRIES: int = Field(default=3, description="Max retry attempts per step")

    # Base delay for exponential backoff (seconds)
    RETRY_BASE_DELAY: int = Field(default=60, description="Base retry delay in seconds")

    # Circuit breaker: failure threshold
    CIRCUIT_FAILURE_THRESHOLD: int = Field(
        default=5, description="Failures before circuit opens"
    )

    # Circuit breaker: recovery timeout (seconds)
    CIRCUIT_RECOVERY_TIMEOUT: int = Field(
        default=60, description="Seconds before circuit resets"
    )

    # Step-specific timeouts (seconds)
    STEP_TIMEOUT_OCR: int = Field(default=300, description="OCR step timeout")
    STEP_TIMEOUT_PARSER: int = Field(default=300, description="Parser step timeout")
    STEP_TIMEOUT_CONVERTER: int = Field(
        default=120, description="Converter step timeout"
    )
    STEP_TIMEOUT_REGISTRY: int = Field(
        default=30, description="Registry step timeout"
    )
    STEP_TIMEOUT_RAG_INDEX: int = Field(
        default=300, description="RAG Index step timeout"
    )

    # Saga compensation timeout
    SAGA_COMPENSATION_TIMEOUT: int = Field(
        default=60, description="Timeout per compensation action"
    )

    # Dead job detection: max time a job can be in "running" state
    MAX_JOB_RUNNING_TIME: int = Field(
        default=3600, description="Max seconds a job can stay running"
    )


class Settings(BaseSettings):
    """Main application settings."""

    # Application
    APP_NAME: str = "orchestrator-service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8081

    # API
    API_V1_PREFIX: str = "/api/v1"

    # JWT (for token validation)
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-here", description="JWT secret key"
    )
    JWT_ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./orchestrator.db",
        description="Async SQLAlchemy database URL",
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )

    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1", description="Celery broker URL (Redis)"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2", description="Celery result backend URL"
    )

    # External Services Configuration
    services: ServiceConfig = Field(
        default_factory=ServiceConfig,
        description="External services configuration (URL, mock mode)",
    )

    # Pipeline Configuration
    pipeline: PipelineConfig = Field(
        default_factory=PipelineConfig,
        description="Pipeline execution parameters",
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
