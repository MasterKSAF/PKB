"""
Тесты GatewayConfig — валидация окружения, CORS, service_urls.

Проверяет:
  - GATEWAY_MODE=real принимается, другие режимы — ошибка
  - ENV=development/production — валидация
  - CORS_ALLOWED_ORIGINS=* запрещён для production
  - service_urls: 10 сервисов, порты соответствуют README
  - Таймауты, idempotency_ttl, rate_limit_enabled по умолчанию
  - allow_anonymous=true (установлено в conftest.py)

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.config import GatewayConfig, config as global_config


class TestModeValidation:
    """Валидация GATEWAY_MODE."""

    def test_mode_real_accepted(self):
        """GATEWAY_MODE=real — допустимое значение."""
        cfg = GatewayConfig()
        assert cfg.mode == "real"

    def test_mode_invalid_raises(self):
        """GATEWAY_MODE=mock — ValueError."""
        with pytest.raises(ValueError):
            GatewayConfig(mode="mock", env="development", cors_allowed_origins="*")


class TestEnvValidation:
    """Валидация ENV (GW-3)."""

    def test_env_production_cors_wildcard_raises(self):
        """ENV=production + CORS=* → ValueError (GW-3)."""
        with pytest.raises(ValueError):
            GatewayConfig(mode="real", env="production", cors_allowed_origins="*")

    def test_env_production_cors_specific_ok(self):
        """ENV=production + CORS=example.com — OK."""
        cfg = GatewayConfig(mode="real", env="production", cors_allowed_origins="https://example.com")
        assert cfg.env == "production"

    def test_env_development_cors_wildcard_ok(self):
        """ENV=development + CORS=* — OK."""
        cfg = GatewayConfig(mode="real", env="development", cors_allowed_origins="*")
        assert cfg.env == "development"

    def test_env_invalid_raises(self):
        """ENV=staging → ValueError."""
        with pytest.raises(ValueError):
            GatewayConfig(mode="real", env="staging", cors_allowed_origins="*")


class TestServiceUrls:
    """Проверка service_urls по умолчанию."""

    def test_default_service_urls_count(self):
        """10 сервисов в service_urls."""
        cfg = GatewayConfig()
        assert len(cfg.service_urls) == 10

    def test_default_service_urls_keys(self):
        """Ключи сервисов."""
        cfg = GatewayConfig()
        expected = {
            "auth", "orchestrator", "query", "registry",
            "converter_validator", "parser", "ocr", "analyse",
            "rag_builder", "rag_search",
        }
        assert set(cfg.service_urls.keys()) == expected

    def test_default_service_urls_ports(self):
        """Порты сервисов."""
        cfg = GatewayConfig()
        assert cfg.service_urls["auth"] == "http://127.0.0.1:8082"
        assert cfg.service_urls["orchestrator"] == "http://127.0.0.1:8081"
        assert cfg.service_urls["query"] == "http://127.0.0.1:8083"
        assert cfg.service_urls["registry"] == "http://127.0.0.1:8084"


class TestEnvOverride:
    """Проверка переопределения через environment variables."""

    def test_auth_service_url_override(self, monkeypatch):
        """AUTH_SERVICE_URL переопределяется."""
        monkeypatch.setenv("AUTH_SERVICE_URL", "http://auth:9090")
        cfg = GatewayConfig()
        assert cfg.service_urls["auth"] == "http://auth:9090"

    def test_timeout_default(self):
        """request_timeout=30.0 по умолчанию."""
        cfg = GatewayConfig()
        assert cfg.request_timeout == 30.0

    def test_health_timeout_default(self):
        """health_timeout=5.0 по умолчанию."""
        cfg = GatewayConfig()
        assert cfg.health_timeout == 5.0

    def test_idempotency_ttl_default(self):
        """idempotency_ttl=3600 по умолчанию."""
        cfg = GatewayConfig()
        assert cfg.idempotency_ttl == 3600

    def test_rate_limit_disabled(self, monkeypatch):
        """RATE_LIMIT_ENABLED=0."""
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "0")
        cfg = GatewayConfig()
        assert cfg.rate_limit_enabled is False

    def test_allow_anonymous_enabled(self, monkeypatch):
        """ALLOW_ANONYMOUS=true."""
        monkeypatch.setenv("ALLOW_ANONYMOUS", "true")
        cfg = GatewayConfig()
        assert cfg.allow_anonymous is True
