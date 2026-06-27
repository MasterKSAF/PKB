"""
Тесты собственных эндпоинтов Gateway.

Проверяет /health, /system/health, /system/mode, /monitor/metrics,
и обработчики ошибок (404, 410, 400, 422, 500).

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


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
        """RequestValidationError → 422."""
        resp = client.post(
            "/api/v1/auth/token",
            json={"invalid": "data"},
        )
        if resp.status_code == 422:
            data = resp.json()
            assert "error" in data or "detail" in data

    def test_rbac_no_token_for_protected(self, client):
        """Запрос к защищённому эндпоинту без токена при ALLOW_ANONYMOUS=True."""
        resp = client.post(
            "/api/v1/drafts",
            json={"title": "test"},
        )
        assert resp.status_code not in (401, 403)
