"""
Тесты PIIQueryValidatorMiddleware (GW-7).

Проверяет, что query-параметры с PII-данными блокируются (400),
а безопасные параметры пропускаются.

Unit-тесты через TestClient к реальному Gateway (не требуют Docker).
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


class TestPIIQueryValidatorBlocked:
    """Query-параметры с PII должны блокироваться (400)."""

    @pytest.mark.parametrize("param_name,param_value", [
        ("password", "secret123"),
        ("email", "test@test.com"),
        ("access_token", "eyJhbGciOiJIUzI1NiJ9"),
        ("refresh_token", "rftok123"),
        ("api_key", "abc123"),
        ("apikey", "xyz789"),
        ("secret_key", "sk-xxx"),
        ("phone", "+71234567890"),
        ("passport", "1234 567890"),
        ("inn", "1234567890"),
        ("snils", "123-456-789 00"),
        ("ogrn", "1027700132195"),
    ])
    def test_pii_param_blocked(self, param_name: str, param_value: str, client):
        """PII-параметр в query → 400 BAD_REQUEST."""
        resp = client.get(f"/api/v1/system/health?{param_name}={param_value}")
        assert resp.status_code == 400, (
            f"Expected 400 for {param_name}, got {resp.status_code}: {resp.text}"
        )
        data = resp.json()
        assert "PII_IN_QUERY_STRING" in str(data.get("error", {}))

    def test_multiple_pii_params_blocked(self, client):
        """Несколько PII-параметров → 400 (первый же блокирует)."""
        resp = client.get(
            "/api/v1/system/health?password=123&email=test@test.com"
        )
        assert resp.status_code == 400


class TestPIIQueryValidatorAllowed:
    """Разрешённые параметры не должны блокироваться."""

    @pytest.mark.parametrize("param_name,param_value", [
        ("document_key", "doc-123"),
        ("file_key", "file-456"),
        ("search", "query text"),
        ("q", "search term"),
        ("page", "1"),
        ("limit", "20"),
        ("offset", "0"),
        ("sort", "created_at"),
        ("filter", "status=active"),
    ])
    def test_safe_param_allowed(self, param_name: str, param_value: str, client):
        """Безопасный параметр → не блокируется."""
        resp = client.get(f"/api/v1/system/health?{param_name}={param_value}")
        assert resp.status_code != 400, (
            f"Expected non-400 for {param_name}, got {resp.status_code}"
        )


class TestPIIQueryValidatorCaseInsensitive:
    """Проверка регистронезависимости паттернов."""

    @pytest.mark.parametrize("param_name", [
        "Password",
        "PASSWORD",
        "Access_Token",
        "API_KEY",
        "ApiKey",
    ])
    def test_case_insensitive_blocked(self, param_name: str, client):
        """PII-параметр в любом регистре → 400."""
        resp = client.get(f"/api/v1/system/health?{param_name}=value")
        assert resp.status_code == 400
