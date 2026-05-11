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

    # External Services Configuration
    services: ServiceConfig = ServiceConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
