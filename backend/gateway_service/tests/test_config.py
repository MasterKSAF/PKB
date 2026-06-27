"""
Tests for GatewayConfig — валидация конфигурации.

Сценарии:
  - mode=real — единственный поддерживаемый режим
  - mode=invalid — ValueError
  - env=production + CORS_ALLOWED_ORIGINS=* — ValueError
  - env=production + CORS_ALLOWED_ORIGINS=https://example.com — OK
  - env=development + CORS_ALLOWED_ORIGINS=* — OK
  - env=invalid — ValueError
  - service_urls по умолчанию — 11 сервисов
  - Override через env: AUTH_SERVICE_URL=http://custom:9090
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from gateway.config import GatewayConfig


class TestModeValidation:
    """GATEWAY_MODE валидация."""

    def test_mode_real_accepted(self):
        """mode=real — единственный поддерживаемый режим."""
        config = GatewayConfig(mode="real")
        assert config.mode == "real"

    def test_mode_invalid_raises(self):
        """mode=invalid → ValueError."""
        with pytest.raises(ValueError, match="не поддерживается"):
            GatewayConfig(mode="invalid")


class TestEnvValidation:
    """ENV валидация (GW-3)."""

    def test_env_production_cors_wildcard_raises(self):
        """env=production + CORS_ALLOWED_ORIGINS=* → ValueError."""
        with pytest.raises(ValueError, match="запрещён для production"):
            GatewayConfig(env="production", cors_allowed_origins="*")

    def test_env_production_cors_specific_ok(self):
        """env=production + CORS_ALLOWED_ORIGINS=https://example.com → OK."""
        config = GatewayConfig(
            env="production",
            cors_allowed_origins="https://example.com",
        )
        assert config.env == "production"
        assert config.cors_allowed_origins == "https://example.com"

    def test_env_development_cors_wildcard_ok(self):
        """env=development + CORS_ALLOWED_ORIGINS=* → OK (разрешено для dev)."""
        config = GatewayConfig(env="development", cors_allowed_origins="*")
        assert config.env == "development"
        assert config.cors_allowed_origins == "*"

    def test_env_invalid_raises(self):
        """env=invalid → ValueError."""
        with pytest.raises(ValueError, match="не поддерживается"):
            GatewayConfig(env="invalid")


class TestServiceUrls:
    """service_urls по умолчанию и override."""

    def test_default_service_urls_count(self):
        """По умолчанию 10 сервисов (gateway и integration не входят)."""
        config = GatewayConfig(mode="real", env="development")
        assert len(config.service_urls) == 10

    def test_default_service_urls_keys(self):
        """Список сервисов по умолчанию."""
        config = GatewayConfig(mode="real", env="development")
        expected_keys = {
            "auth", "orchestrator", "query", "registry",
            "converter_validator", "parser", "ocr", "analyse",
            "rag_builder", "rag_search",
        }
        assert expected_keys.issubset(set(config.service_urls.keys()))

    def test_default_service_urls_ports(self):
        """Проверка портов по умолчанию."""
        config = GatewayConfig(mode="real", env="development")
        assert config.service_urls["auth"] == "http://127.0.0.1:8082"
        assert config.service_urls["orchestrator"] == "http://127.0.0.1:8081"
        assert config.service_urls["query"] == "http://127.0.0.1:8083"
        assert config.service_urls["registry"] == "http://127.0.0.1:8084"


class TestEnvOverride:
    """Проверка переопределения через переменные окружения."""

    def test_auth_service_url_override(self, monkeypatch):
        """Override AUTH_SERVICE_URL через env."""
        monkeypatch.setenv("AUTH_SERVICE_URL", "http://custom:9090")
        config = GatewayConfig(mode="real", env="development")
        assert config.service_urls["auth"] == "http://custom:9090"

    def test_timeout_default(self):
        """GATEWAY_REQUEST_TIMEOUT по умолчанию 30.0 (flat default)."""
        config = GatewayConfig()
        assert config.request_timeout == 30.0

    def test_health_timeout_default(self):
        """GATEWAY_HEALTH_TIMEOUT по умолчанию 5.0 (flat default)."""
        config = GatewayConfig()
        assert config.health_timeout == 5.0

    def test_idempotency_ttl_default(self):
        """IDEMPOTENCY_TTL по умолчанию 3600 (flat default)."""
        config = GatewayConfig()
        assert config.idempotency_ttl == 3600

    def test_rate_limit_disabled(self, monkeypatch):
        """Override RATE_LIMIT_ENABLED=false."""
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "0")
        config = GatewayConfig(mode="real", env="development")
        assert config.rate_limit_enabled is False

    def test_allow_anonymous_enabled(self, monkeypatch):
        """Override ALLOW_ANONYMOUS=true."""
        monkeypatch.setenv("ALLOW_ANONYMOUS", "true")
        config = GatewayConfig(mode="real", env="development")
        assert config.allow_anonymous is True
