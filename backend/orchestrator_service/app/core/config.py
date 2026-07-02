"""
Configuration module for Orchestrator Service.
Supports dual mode: real API calls or mock/stub mode for each external service.
"""

from typing import Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings


class ServiceConfig(BaseSettings):
    """Configuration for external services."""

    # Registry Service (port 8084)
    REGISTRY_SERVICE_URL: Optional[str] = Field(
        default="http://registry-service:8084", description="URL for registry service"
    )
    REGISTRY_SERVICE_MOCK: bool = Field(
        default=False, description="Use mock mode for registry service"
    )

    # RAG Builder Service (port 8090) — indexing
    RAG_BUILDER_SERVICE_URL: Optional[str] = Field(
        default="http://rag-builder:8090", description="URL for RAG Builder service (indexing)"
    )
    # RAG Search Service (port 8091) — search
    RAG_SEARCH_SERVICE_URL: Optional[str] = Field(
        default="http://rag-search:8091", description="URL for RAG Search service (search)"
    )
    # Deprecated: use RAG_BUILDER_SERVICE_URL
    RAG_SERVICE_URL: Optional[str] = Field(
        default=None, description="[DEPRECATED] Use RAG_BUILDER_SERVICE_URL"
    )
    RAG_SERVICE_MOCK: bool = Field(
        default=False, description="Use mock mode for rag service"
    )

    @model_validator(mode='after')
    def _sync_rag_urls(self):
        if self.RAG_SERVICE_URL is not None:
            self.RAG_BUILDER_SERVICE_URL = self.RAG_SERVICE_URL
        return self

    # OCR Service (port 8088)
    OCR_SERVICE_URL: Optional[str] = Field(
        default="http://ocr-service:8088", description="URL for OCR service"
    )
    OCR_SERVICE_MOCK: bool = Field(
        default=False, description="Use mock mode for OCR service"
    )
    OCR_ENABLED: bool = Field(
        default=True, description="Enable OCR service"
    )

    # Parser Service (port 8089)
    PARSER_SERVICE_URL: Optional[str] = Field(
        default="http://parser-service:8089", description="URL for parser service"
    )
    PARSER_SERVICE_MOCK: bool = Field(
        default=False, description="Use mock mode for parser service"
    )
    PARSER_ENABLED: bool = Field(
        default=True, description="Enable parser service"
    )
    PARSER_FALLBACK_TO_OCR: bool = Field(
        default=True, description="Fallback from parser to OCR if parser unavailable or preview_not_supported"
    )

    # Converter-Validator Service (port 8086)
    CONVERTER_SERVICE_URL: Optional[str] = Field(
        default="http://converter-validator:8086", description="URL for converter-validator service"
    )
    CONVERTER_SERVICE_MOCK: bool = Field(
        default=False, description="Use mock mode for converter-validator service"
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

    # Per-state timeout: max time a step can stay in 'pending' before being marked stale
    PENDING_STATE_TIMEOUT: int = Field(
        default=180,
        description="Max seconds a step can stay in pending state (P3S-1)",
    )

    # Running step timeout: max time a step can stay in 'running' before being checked
    RUNNING_STEP_TIMEOUT: int = Field(
        default=600,
        description="Max seconds a step can stay in running before health check (B2)",
    )

    # Absolute task timeout: max total time for any pipeline task
    ABSOLUTE_TASK_TIMEOUT_HOURS: int = Field(
        default=48,
        description="Max hours a task can exist before being killed (P3S-1)",
    )

    # Full phase mode (P1F-9): auto | partial | full
    # auto  — full_completed (preview_not_supported) → skip processing, else full Parser/OCR
    # partial — always run full Parser/OCR even if full preview is available
    # full   — skip full Parser/OCR entirely (full_completed must be True)
    FULL_PHASE_MODE: str = Field(
        default="auto",
        description="Full phase strategy: auto | partial | full",
    )

    # Auto-approve thresholds (§3 Quality-решения и авто-апрув)
    AUTO_APPROVE_ENABLED: bool = Field(
        default=False,
        description="Enable auto-approve when quality conditions are met",
    )
    AUTO_APPROVE_MAX_CRITICAL: int = Field(
        default=0,
        description="Max critical notifications allowed for auto-approve",
    )
    AUTO_APPROVE_MAX_WARNING: int = Field(
        default=2,
        description="Max warning notifications allowed for auto-approve",
    )

    # Quality confidence thresholds (§3)
    # operator_avg_confidence_below — порог ручной проверки (review_required)
    # reprocess_avg_confidence_below — порог отбраковки (discarded)
    # Max concurrent pipeline tasks (preview + full)
    MAX_CONCURRENT_TASKS: int = Field(
        default=4,
        description="Max number of concurrent active pipeline tasks",
    )

    QUALITY_OPERATOR_CONFIDENCE_BELOW: float = Field(
        default=0.8,
        description="Confidence below this → review_required (manual check)",
    )
    QUALITY_REPROCESS_CONFIDENCE_BELOW: float = Field(
        default=0.5,
        description="Confidence below this → discarded (unreadable)",
    )


class HTTPClientConfig(BaseSettings):
    """HTTP client settings for external service calls."""

    # Default timeout for HTTP requests (seconds)
    DEFAULT_TIMEOUT: int = Field(
        default=30, description="Default HTTP request timeout"
    )

    # Connection timeout (seconds)
    CONNECT_TIMEOUT: int = Field(
        default=10, description="TCP connection timeout"
    )

    # Read timeout (seconds)
    READ_TIMEOUT: int = Field(
        default=30, description="HTTP read/response timeout"
    )

    # Converter-validator specific read timeout (seconds) — full conversion
    # can be slow on large documents (hierarchy build, LLM enrich, validation).
    # Default: 180s, overridable via CONVERTER_READ_TIMEOUT env var.
    CONVERTER_READ_TIMEOUT: int = Field(
        default=180, description="HTTP read timeout for Converter-Validator requests"
    )

    # Pool timeout (seconds) — max time to wait for a connection from pool
    POOL_TIMEOUT: int = Field(
        default=5, description="Connection pool timeout"
    )

    # Connection pool limits
    POOL_CONNECTIONS: int = Field(
        default=50, description="Max connections in pool"
    )
    POOL_MAX_SIZE: int = Field(
        default=100, description="Max keepalive connections"
    )

    # Retry settings
    MAX_RETRIES: int = Field(
        default=3, description="Max retries for HTTP requests"
    )
    RETRY_BACKOFF_FACTOR: float = Field(
        default=2.0, description="Exponential backoff multiplier"
    )


class MinioConfig(BaseSettings):
    """MinIO / S3-compatible storage configuration."""

    MINIO_ENDPOINT: str = Field(
        default="minio:9000", description="MinIO endpoint (host:port)"
    )
    MINIO_ACCESS_KEY: str = Field(
        default="minioadmin", description="MinIO access key"
    )
    MINIO_SECRET_KEY: str = Field(
        default="minioadmin", description="MinIO secret key"
    )
    MINIO_BUCKET: str = Field(
        default="documents", description="MinIO bucket for document files"
    )
    MINIO_IMAGE_BUCKET: str = Field(
        default="images", description="MinIO bucket for images"
    )
    MINIO_SECURE: bool = Field(
        default=False, description="Use HTTPS for MinIO"
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

    # Database — обязательный параметр, задаётся в .env или переменной окружения.
    # Для разработки: sqlite+aiosqlite:///./orchestrator.db
    # Для production: postgresql+asyncpg://user:pass@host/db
    DATABASE_URL: str = Field(
        ...,
        description="Async SQLAlchemy database URL. Must be set explicitly.",
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

    # MinIO Storage Configuration
    minio: MinioConfig = Field(
        default_factory=MinioConfig,
        description="MinIO / S3-compatible storage configuration",
    )

    # HTTP Client Configuration
    http_client: HTTPClientConfig = Field(
        default_factory=HTTPClientConfig,
        description="HTTP client settings for external service calls",
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
