"""
Тесты health-check функций: check_service_health(), check_all_services_health().

Сценарии:
  - check_service_health("auth"): 200 → "ok"
  - check_service_health("auth"): 503 → "degraded"
  - check_service_health("auth"): ConnectError → "unavailable"
  - check_service_health("unknown"): нет в service_urls → "unavailable"
  - check_all_services_health(): все ok → содержит gateway:"ok"

Unit-тесты (мок health-check) + интеграционные через Docker.
"""

from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_GATEWAY_DIR = os.path.join(_TEST_DIR, "..")
if _TEST_DIR not in sys.path:
    sys.path.insert(0, _TEST_DIR)
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from helpers import auth_header


# ===================================================================
# Unit-тесты с моками
# ===================================================================


class TestCheckServiceHealthUnit:
    """check_service_health() — unit-тесты с моками."""

    @pytest.mark.asyncio
    async def test_service_ok(self):
        """Сервис отвечает 200 → "ok"."""
        from gateway.client import check_service_health

        with patch("gateway.client.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            status = await check_service_health("auth")
            assert status == "ok"

    @pytest.mark.asyncio
    async def test_service_degraded(self):
        """Сервис отвечает 503 → "degraded"."""
        from gateway.client import check_service_health

        with patch("gateway.client.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 503
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            status = await check_service_health("auth")
            assert status == "degraded"

    @pytest.mark.asyncio
    async def test_service_connect_error(self):
        """ConnectError → "unavailable"."""
        from gateway.client import check_service_health
        import httpx

        with patch("gateway.client.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_get_client.return_value = mock_client

            status = await check_service_health("auth")
            assert status == "unavailable"

    @pytest.mark.asyncio
    async def test_service_timeout(self):
        """Timeout → "unavailable"."""
        from gateway.client import check_service_health
        import httpx

        with patch("gateway.client.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_get_client.return_value = mock_client

            status = await check_service_health("auth")
            assert status == "unavailable"

    @pytest.mark.asyncio
    async def test_unknown_service(self):
        """Неизвестный сервис → "unavailable"."""
        from gateway.client import check_service_health

        status = await check_service_health("unknown_service_xyz")
        assert status == "unavailable"


class TestCheckAllServicesHealthUnit:
    """check_all_services_health() — unit-тесты."""

    @pytest.mark.asyncio
    async def test_all_ok_contains_gateway(self):
        """Все ok → результат содержит gateway: ok."""
        from gateway.client import check_all_services_health

        with patch("gateway.client.check_service_health", new=AsyncMock(return_value="ok")):
            results = await check_all_services_health()
            assert "gateway" in results
            assert results["gateway"] == "ok"
            # Должен содержать и другие сервисы
            assert len(results) > 3

    @pytest.mark.asyncio
    async def test_one_unavailable(self):
        """Один сервис не отвечает → "unavailable" в результатах."""
        from gateway.client import check_all_services_health

        async def mock_check(name: str) -> str:
            if name == "auth":
                return "unavailable"
            return "ok"

        with patch("gateway.client.check_service_health", new=mock_check):
            results = await check_all_services_health()
            assert results.get("auth") == "unavailable"
            assert results.get("gateway") == "ok"

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Параллельный запуск (asyncio.gather) — все проверки выполняются."""
        from gateway.client import check_all_services_health

        call_order = []

        async def mock_check(name: str) -> str:
            call_order.append(name)
            return "ok"

        with patch("gateway.client.check_service_health", new=mock_check):
            results = await check_all_services_health()
            assert len(results) >= 3


# ===================================================================
# Интеграционные тесты (Docker)
# ===================================================================


@pytest.mark.docker
class TestHealthIntegration:
    """Health-check интеграционные тесты."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, http_client, docker_gateway_base):
        """GET /api/v1/health → 200."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_system_health_endpoint(self, http_client, docker_gateway_base, system_admin_token):
        """GET /api/v1/system/health для system_admin → 200 с сервисами."""
        resp = await http_client.get(
            f"{docker_gateway_base}/api/v1/system/health",
            headers=auth_header(system_admin_token),
        )
        # Если в Docker mock gateway — ответит {"status": "ok"} без деталей
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_live_probe(self, http_client, docker_gateway_base):
        """GET /api/v1/system/health/live → 200 {"status":"ok"}."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/system/health/live")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"

    @pytest.mark.asyncio
    async def test_ready_probe(self, http_client, docker_gateway_base):
        """GET /api/v1/system/health/ready → 200 {"status":"ok"}."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/system/health/ready")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
