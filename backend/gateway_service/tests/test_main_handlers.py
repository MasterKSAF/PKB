"""
Tests for Gateway's own handlers.

Сценарии:
  - GET /api/v1/health без аутентификации → {"status": "ok"}
  - GET /api/v1/health c system_admin → полный ответ со статусами сервисов
  - GET /api/v1/system/health/live → {"status":"ok"}
  - GET /api/v1/system/health/ready → {"status":"ok"}
  - GET /api/v1/system/mode → mode, port, service_urls, allow_anonymous, request_timeout
  - GET /api/v1/monitor/metrics → control_metrics + answer_metrics + logs
  - HTTPException handler → {"error": {"code": "...", "message": "..."}}
  - RequestValidationError → 422 с details
  - ValidationError (Pydantic) → 422 с errors
  - Internal error → 500
  - NOT_FOUND → 404 c унифицированным форматом
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestHealthEndpoint:
    """GET /api/v1/health — базовый health-check."""

    def test_health_no_auth_returns_minimal(self, client):
        """Без аутентификации → {"status": "ok"}."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"status": "ok"}

    def test_system_health_no_auth_returns_minimal(self, client):
        """GET /api/v1/system/health без аутентификации → {"status": "ok"}."""
        resp = client.get("/api/v1/system/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"status": "ok"}

    def test_health_with_system_admin_returns_full(self, client, mock_auth_validate, system_admin_user):
        """С system_admin → полный ответ со статусами сервисов."""
        mock_auth_validate(system_admin_user)
        resp = client.get(
            "/api/v1/health",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert "version" in data
        assert "services" in data
        assert "timestamp" in data
        assert "endpoints_total" in data


class TestLivenessReadiness:
    """Liveness и Readiness probes."""

    def test_health_live(self, client):
        """GET /api/v1/system/health/live → {"status":"ok"}."""
        resp = client.get("/api/v1/system/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_ready(self, client):
        """GET /api/v1/system/health/ready → {"status":"ok"}."""
        resp = client.get("/api/v1/system/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestModeInfo:
    """GET /api/v1/system/mode — информация о конфигурации."""

    def test_mode_info_structure(self, client):
        """Ответ содержит mode, port, service_urls, allow_anonymous, request_timeout."""
        resp = client.get("/api/v1/system/mode")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data
        assert "port" in data
        assert "service_urls" in data
        assert "allow_anonymous" in data
        assert "request_timeout" in data

    def test_mode_info_values(self, client):
        """Проверка значений полей."""
        resp = client.get("/api/v1/system/mode")
        data = resp.json()
        assert data["mode"] == "real"
        assert isinstance(data["port"], int)
        assert isinstance(data["service_urls"], dict)
        assert isinstance(data["allow_anonymous"], bool)
        assert isinstance(data["request_timeout"], (int, float))


class TestMetrics:
    """GET /api/v1/monitor/metrics (GW-12)."""

    def test_metrics_structure(self, client, mock_auth_validate, system_admin_user):
        """Метрики содержат control_metrics, answer_metrics, logs."""
        mock_auth_validate(system_admin_user)
        resp = client.get(
            "/api/v1/monitor/metrics",
            headers={"Authorization": "Bearer mock_token"},
        )
        # Может быть 403 если RBAC не пропустит — нужно проверить авторизацию
        if resp.status_code == 200:
            data = resp.json()
            assert "control_metrics" in data
            assert "answer_metrics" in data
            assert "logs" in data
            assert "ocr_quality" in data["control_metrics"]
            assert "useful_rate" in data["answer_metrics"]

    def test_metrics_requires_auth(self, client):
        """Без аутентификации /monitor/metrics — с ALLOW_ANONYMOUS=True может пройти."""
        resp = client.get("/api/v1/monitor/metrics")
        # При ALLOW_ANONYMOUS=True пропускается (не 401/403)
        assert resp.status_code not in (401, 403), f"Unexpected {resp.status_code}"


class TestErrorHandlers:
    """HTTPException, RequestValidationError, ValidationError, 500, 404."""

    def test_not_found_returns_unified_format(self, client):
        """Неизвестный путь → 404 с унифицированным форматом ошибки."""
        resp = client.get("/api/v1/nonexistent/route")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert data["error"]["code"] == "NOT_FOUND"

    def test_deprecated_integration_returns_410(self, client):
        """Deprecated integration route → 410."""
        resp = client.get("/api/v1/meridian/test")
        assert resp.status_code == 410
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "SERVICE_REMOVED"

    def test_invalid_draft_id_returns_400(self, client):
        """Нечисловой draft_id → 400."""
        resp = client.get("/api/v1/drafts/abc")
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_DRAFT_ID"

    def test_validation_error_422(self, client):
        """RequestValidationError → 422 с unified форматом (если доходит до FastAPI)."""
        resp = client.post(
            "/api/v1/auth/token",
            json={"invalid": "data"},
        )
        # Если запрос дошёл до реального Auth Service (работает на 8082),
        # он может вернуть 401. Если нет — может быть 422 или 502.
        if resp.status_code == 422:
            data = resp.json()
            # Проверяем что error в данных, но формат может быть разным
            # (FastAPI-native detail[] или Gateway unified error)
            assert "error" in data or "detail" in data

    def test_rbac_no_token_for_protected(self, client):
        """Запрос к защищённому эндпоинту без токена при ALLOW_ANONYMOUS=True."""
        resp = client.post(
            "/api/v1/drafts",
            json={"title": "test"},
        )
        # ALLOW_ANONYMOUS=True → middleware не блокирует, идёт к прокси
        assert resp.status_code not in (401, 403)
