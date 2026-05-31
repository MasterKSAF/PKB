"""
Configuration module for Orchestrator Service.
Supports dual mode: real API calls or mock/stub mode for each external service.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class ServiceConfig(BaseSettings):
    """Configuration for external services."""

    # Auth Service (port 8082)
    AUTH_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for auth service"
    )
    AUTH_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for auth service"
    )

    # Query Service (port 8083)
    QUERY_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for query service"
    )
    QUERY_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for query service"
    )

    # Registry Service (port 8084)
    REGISTRY_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for registry service"
    )
    REGISTRY_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for registry service"
    )

    # Integration Service (port 8085)
    INTEGRATION_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for integration service"
    )
    INTEGRATION_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for integration service"
    )

    # Validation Service (port 8086)
    VALIDATE_SERVICE_URL: Optional[str] = Field(
        default=None, description="URL for validation service"
    )
    VALIDATE_SERVICE_MOCK: bool = Field(
        default=True, description="Use mock mode for validation service"
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
    PORT: int = 8000

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
    services: ServiceConfig = ServiceConfig()

    # Pipeline Configuration
    pipeline: PipelineConfig = PipelineConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
