"""
Тесты GatewayConfig — валидация конфигурации.

8 сценариев: режим, окружение, CORS, service_urls.
Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys
import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


# ===================================================================
# Вспомогательная функция для создания конфига с override env
# ===================================================================


def _make_config(**overrides) -> "GatewayConfig":
    """Создаёт GatewayConfig с переопределёнными env."""
    from gateway.config import GatewayConfig

    # Сохраняем оригинальные env
    saved = {}
    for k, v in overrides.items():
        saved[k] = os.environ.get(k)
        os.environ[k] = str(v)

    try:
        return GatewayConfig()
    finally:
        # Восстанавливаем
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ===================================================================
# Тесты
# ===================================================================


class TestGatewayConfigMode:
    """GATEWAY_MODE валидация."""

    def test_mode_real_is_valid(self):
        """mode=real — единственный поддерживаемый режим."""
        config = _make_config(GATEWAY_MODE="real")
        assert config.mode == "real"

    def test_mode_invalid_raises(self):
        """mode=invalid → ValueError."""
        with pytest.raises(ValueError, match="не поддерживается"):
            _make_config(GATEWAY_MODE="invalid")


class TestGatewayConfigEnv:
    """ENV валидация (GW-3)."""

    def test_env_production_with_restricted_origins_is_ok(self):
        """env=production + CORS_ALLOWED_ORIGINS=https://example.com — OK."""
        config = _make_config(
            ENV="production",
            CORS_ALLOWED_ORIGINS="https://example.com",
        )
        assert config.env == "production"
        assert config.cors_allowed_origins == "https://example.com"

    def test_env_production_with_wildcard_raises(self):
        """env=production + CORS_ALLOWED_ORIGINS=* → ValueError."""
        with pytest.raises(ValueError, match="запрещён для production"):
            _make_config(
                ENV="production",
                CORS_ALLOWED_ORIGINS="*",
            )

    def test_env_development_with_wildcard_is_ok(self):
        """env=development + CORS_ALLOWED_ORIGINS=* — OK."""
        config = _make_config(
            ENV="development",
            CORS_ALLOWED_ORIGINS="*",
        )
        assert config.env == "development"
        assert config.cors_allowed_origins == "*"

    def test_env_invalid_raises(self):
        """env=invalid → ValueError."""
        with pytest.raises(ValueError, match="не поддерживается"):
            _make_config(ENV="invalid")


class TestGatewayConfigDefaults:
    """Проверка значений по умолчанию."""

    def test_service_urls_contains_all_services(self):
        """service_urls по умолчанию — 9 сервисов (без app/gateway)."""
        config = _make_config()
        # Все ключи сервисов из gateway/config.py
        expected_keys = {
            "auth", "orchestrator", "query", "registry",
            "converter_validator", "parser", "ocr", "analyse",
            "rag_builder", "rag_search",
        }
        assert expected_keys.issubset(config.service_urls.keys()), (
            f"Missing keys: {expected_keys - set(config.service_urls.keys())}"
        )
        assert len(config.service_urls) >= 10

    def test_default_port(self):
        """Порт по умолчанию 8080."""
        config = _make_config()
        assert config.port == 8080

    def test_default_timeout(self):
        """Таймауты по умолчанию."""
        config = _make_config()
        assert config.request_timeout == 30.0
        assert config.health_timeout == 5.0


class TestGatewayConfigOverrides:
    """Проверка переопределения через env."""

    def test_service_url_override(self):
        """AUTH_SERVICE_URL=http://custom:9090 → service_urls['auth']."""
        config = _make_config(AUTH_SERVICE_URL="http://custom:9090")
        assert config.service_urls["auth"] == "http://custom:9090"

    def test_rate_limit_disabled(self):
        """RATE_LIMIT_ENABLED=0 → rate_limit_enabled=False."""
        config = _make_config(RATE_LIMIT_ENABLED="0")
        assert config.rate_limit_enabled is False

    def test_rate_limit_enabled(self):
        """RATE_LIMIT_ENABLED=1 → rate_limit_enabled=True."""
        config = _make_config(RATE_LIMIT_ENABLED="1")
        assert config.rate_limit_enabled is True

    def test_allow_anonymous_true(self):
        """ALLOW_ANONYMOUS=true → allow_anonymous=True."""
        config = _make_config(ALLOW_ANONYMOUS="true")
        assert config.allow_anonymous is True
