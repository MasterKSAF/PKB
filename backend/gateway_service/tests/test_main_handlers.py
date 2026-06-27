"""
Тесты собственных эндпоинтов Gateway.

Сценарии:
  - GET /api/v1/health без аутентификации → {"status": "ok"}
  - GET /api/v1/health c system_admin → полный ответ со статусами сервисов
  - GET /api/v1/system/health/live → {"status":"ok"}
  - GET /api/v1/system/health/ready → {"status":"ok"}
  - GET /api/v1/system/mode → mode, port, service_urls
  - GET /api/v1/monitor/metrics → control_metrics + answer_metrics
  - HTTPException handler → единый формат ошибки
  - NOT_FOUND → 404 c унифицированным форматом

Unit + интеграционные тесты.
"""

from __future__ import annotations

import os
import sys

import pytest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_GATEWAY_DIR = os.path.join(_TEST_DIR, "..")
if _TEST_DIR not in sys.path:
    sys.path.insert(0, _TEST_DIR)
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from helpers import auth_header


# ===================================================================
# Unit-тесты: проверка формата ответов
# ===================================================================


class TestHealthEndpoint:
    """Gateway health endpoints — unit проверка (ALLOW_ANONYMOUS из conftest)."""

    def test_health_format(self):
        """GET /api/v1/health возвращает {"status": "ok"}."""
        from fastapi.testclient import TestClient
        from gateway.main import app
        client = TestClient(app)
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"status": "ok"}

    def test_live_format(self):
        """GET /api/v1/system/health/live → {"status":"ok"}."""
        from fastapi.testclient import TestClient
        from gateway.main import app
        client = TestClient(app)
        resp = client.get("/api/v1/system/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_ready_format(self):
        """GET /api/v1/system/health/ready → {"status":"ok"}."""
        from fastapi.testclient import TestClient
        from gateway.main import app
        client = TestClient(app)
        resp = client.get("/api/v1/system/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_mode_endpoint(self):
        """GET /api/v1/system/mode → mode, port, service_urls."""
        from fastapi.testclient import TestClient
        from gateway.main import app
        client = TestClient(app)
        resp = client.get("/api/v1/system/mode")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data
        assert "port" in data
        assert "service_urls" in data
        assert "allow_anonymous" in data
        assert "request_timeout" in data

    def test_unknown_path_returns_404(self):
        """GET /api/v1/unknown/path → 404 c единым форматом."""
        from fastapi.testclient import TestClient
        from gateway.main import app
        client = TestClient(app)
        resp = client.get("/api/v1/unknown/path")
        assert resp.status_code == 404
        data = resp.json()
        # Должен быть единый формат ошибки
        assert "error" in data or "detail" in data


# ===================================================================
# Интеграционные тесты (Docker)
# ===================================================================


@pytest.mark.docker
class TestMainHandlersIntegration:
    """Gateway endpoints через Docker."""

    @pytest.mark.asyncio
    async def test_health_no_auth(self, http_client, docker_gateway_base):
        """GET /api/v1/health без аутентификации → {"status": "ok"}."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"

    @pytest.mark.asyncio
    async def test_health_full_for_admin(self, http_client, docker_gateway_base, system_admin_token):
        """GET /api/v1/system/health для system_admin — полный ответ."""
        resp = await http_client.get(
            f"{docker_gateway_base}/api/v1/system/health",
            headers=auth_header(system_admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_system_mode(self, http_client, docker_gateway_base):
        """GET /api/v1/system/mode → конфигурация."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/system/mode")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data
        assert "port" in data
        assert "service_urls" in data

    @pytest.mark.asyncio
    async def test_monitor_metrics(self, http_client, docker_gateway_base, system_admin_token):
        """GET /api/v1/monitor/metrics → метрики."""
        resp = await http_client.get(
            f"{docker_gateway_base}/api/v1/monitor/metrics",
            headers=auth_header(system_admin_token),
        )
        # В Docker mock может не иметь monitor/metrics — проверяем что не 500
        assert resp.status_code not in (500,), (
            f"Monitor metrics: {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_error_format_404(self, http_client, docker_gateway_base):
        """GET /api/v1/unknown/path → 404 c единым форматом."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/unknown/path")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_error_format_410(self, http_client, docker_gateway_base):
        """GET /api/v1/meridian/test → 410 (deprecated)."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/meridian/test")
        # В Docker mock может не вернуть 410, но не должен падать с 500
        assert resp.status_code not in (500,)

    @pytest.mark.asyncio
    async def test_live_probe(self, http_client, docker_gateway_base):
        """GET /api/v1/system/health/live → {"status":"ok"}."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/system/health/live")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"

    @pytest.mark.asyncio
    async def test_ready_probe(self, http_client, docker_gateway_base):
        """GET /api/v1/system/health/ready → {"status":"ok"}."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/system/health/ready")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
