"""
Tests for configuration module (config.py).

Verifies that Settings and ServiceConfig correctly parse environment
variables and apply defaults.
"""

import os
from unittest.mock import patch

import pytest

from app.core.config import ServiceConfig, Settings, get_settings


class TestServiceConfig:
    """Tests for ServiceConfig (per-service settings)."""

    def test_default_mock_mode(self):
        """All services default to mock=True."""
        config = ServiceConfig()
        assert config.AUTH_SERVICE_MOCK is True
        assert config.QUERY_SERVICE_MOCK is True
        assert config.REGISTRY_SERVICE_MOCK is True
        assert config.INTEGRATION_SERVICE_MOCK is True
        assert config.VALIDATE_SERVICE_MOCK is True
        assert config.RAG_SERVICE_MOCK is True
        assert config.OCR_SERVICE_MOCK is True

    def test_default_service_urls(self):
        """All service URLs default to None."""
        config = ServiceConfig()
        assert config.AUTH_SERVICE_URL is None
        assert config.QUERY_SERVICE_URL is None
        assert config.REGISTRY_SERVICE_URL is None
        assert config.INTEGRATION_SERVICE_URL is None
        assert config.VALIDATE_SERVICE_URL is None
        assert config.RAG_SERVICE_URL is None
        assert config.OCR_SERVICE_URL is None

    def test_override_with_env(self):
        """Setting env vars should override defaults."""
        with patch.dict(os.environ, {
            "AUTH_SERVICE_URL": "http://auth:8082",
            "AUTH_SERVICE_MOCK": "false",
            "RAG_SERVICE_URL": "http://rag:8087",
            "RAG_SERVICE_MOCK": "false",
        }, clear=False):
            config = ServiceConfig()
            assert config.AUTH_SERVICE_URL == "http://auth:8082"
            assert config.AUTH_SERVICE_MOCK is False
            assert config.RAG_SERVICE_URL == "http://rag:8087"
            assert config.RAG_SERVICE_MOCK is False

    def test_mixed_mock_and_real(self):
        """Some services mock, some real."""
        with patch.dict(os.environ, {
            "AUTH_SERVICE_MOCK": "false",
            "OCR_SERVICE_MOCK": "false",
        }, clear=False):
            config = ServiceConfig()
            assert config.AUTH_SERVICE_MOCK is False
            assert config.OCR_SERVICE_MOCK is False
            assert config.QUERY_SERVICE_MOCK is True  # still default


class TestSettings:
    """Tests for main Settings class."""

    def test_default_app_values(self):
        settings = Settings()
        assert settings.APP_NAME == "orchestrator-service"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.DEBUG is False
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.API_V1_PREFIX == "/api/v1"

    def test_default_jwt(self):
        settings = Settings()
        assert settings.JWT_SECRET_KEY == "your-secret-key-here"
        assert settings.JWT_ALGORITHM == "HS256"

    def test_override_app_settings(self):
        with patch.dict(os.environ, {
            "APP_VERSION": "2.0.0",
            "DEBUG": "true",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "API_V1_PREFIX": "/api/v2",
        }, clear=False):
            settings = Settings()
            assert settings.APP_VERSION == "2.0.0"
            assert settings.DEBUG is True
            assert settings.HOST == "127.0.0.1"
            assert settings.PORT == 9000
            assert settings.API_V1_PREFIX == "/api/v2"

    def test_override_jwt(self):
        with patch.dict(os.environ, {
            "JWT_SECRET_KEY": "my-super-secret-key",
            "JWT_ALGORITHM": "RS256",
        }, clear=False):
            settings = Settings()
            assert settings.JWT_SECRET_KEY == "my-super-secret-key"
            assert settings.JWT_ALGORITHM == "RS256"

    def test_nested_service_config(self):
        settings = Settings()
        assert isinstance(settings.services, ServiceConfig)
        assert settings.services.AUTH_SERVICE_MOCK is True


class TestGetSettings:
    """Tests for the get_settings() singleton."""

    def test_get_settings_returns_settings_instance(self):
        result = get_settings()
        assert isinstance(result, Settings)

    def test_get_settings_returns_same_type(self):
        result1 = get_settings()
        result2 = get_settings()
        assert type(result1) == type(result2)
        assert result1.APP_NAME == result2.APP_NAME


class TestEnvFileLoading:
    """Tests for .env file loading."""

    def test_settings_has_env_file_configured(self):
        """Verify that Settings.model_config has env_file set."""
        assert Settings.model_config.get("env_file") == ".env"

    def test_env_nested_delimiter(self):
        """Verify nested env delimiter is configured."""
        assert Settings.model_config.get("env_nested_delimiter") == "__"
