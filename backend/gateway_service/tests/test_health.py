"""
Тесты check_service_health(), check_all_services_health().

Все вызовы мокаются через monkeypatch.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import json
import os
import sys

import httpx
import pytest
from unittest.mock import AsyncMock, patch

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


class TestCheckServiceHealth:
    """check_service_health — проверка одного сервиса."""

    @pytest.mark.asyncio
    async def test_service_ok(self, monkeypatch):
        """Сервис отвечает 200 → "ok"."""
        from gateway.client import check_service_health, get_client

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b'{"status":"ok"}'

        async def mock_get(url, **kwargs):
            return mock_response

        mock_client.get = mock_get
        monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)

        result = await check_service_health("auth")
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_service_degraded(self, monkeypatch):
        """Сервис отвечает 503 → "degraded"."""
        from gateway.client import check_service_health

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 503

        async def mock_get(url, **kwargs):
            return mock_response

        mock_client.get = mock_get
        monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)

        result = await check_service_health("auth")
        assert result == "degraded"

    @pytest.mark.asyncio
    async def test_connect_error(self, monkeypatch):
        """ConnectError → "unavailable"."""
        from gateway.client import check_service_health

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        async def mock_get(url, **kwargs):
            raise httpx.ConnectError("Connection refused")

        mock_client.get = mock_get
        monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)

        result = await check_service_health("auth")
        assert result == "unavailable"

    @pytest.mark.asyncio
    async def test_timeout(self, monkeypatch):
        """Timeout → "unavailable"."""
        from gateway.client import check_service_health

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        async def mock_get(url, **kwargs):
            raise httpx.TimeoutException("Timeout")

        mock_client.get = mock_get
        monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)

        result = await check_service_health("auth")
        assert result == "unavailable"

    @pytest.mark.asyncio
    async def test_unknown_service(self):
        """Сервис не в service_urls → "unavailable"."""
        from gateway.client import check_service_health

        result = await check_service_health("unknown_service_name")
        assert result == "unavailable"


class TestCheckAllServicesHealth:
    """check_all_services_health — агрегированный health-check."""

    @pytest.mark.asyncio
    async def test_all_ok(self, monkeypatch):
        """Все сервисы отвечают → {"gateway":"ok", "auth":"ok", ...}."""
        from gateway.client import check_all_services_health

        async def mock_check(name):
            return "ok"

        monkeypatch.setattr(
            "gateway.client.check_service_health",
            mock_check,
        )

        results = await check_all_services_health()
        assert results["gateway"] == "ok"
        assert results.get("auth") == "ok"
        assert results.get("orchestrator") == "ok"

    @pytest.mark.asyncio
    async def test_one_unavailable(self, monkeypatch):
        """Один сервис не отвечает → "unavailable" в результатах."""
        from gateway.client import check_all_services_health

        async def mock_check(name):
            return "unavailable" if name == "auth" else "ok"

        monkeypatch.setattr(
            "gateway.client.check_service_health",
            mock_check,
        )

        results = await check_all_services_health()
        assert results["auth"] == "unavailable"
        assert results["orchestrator"] == "ok"

    @pytest.mark.asyncio
    async def test_gateway_always_ok(self, monkeypatch):
        """Gateway всегда "ok" (собственный статус)."""
        from gateway.client import check_all_services_health

        async def mock_check(name):
            return "unavailable"

        monkeypatch.setattr(
            "gateway.client.check_service_health",
            mock_check,
        )

        results = await check_all_services_health()
        assert results["gateway"] == "ok"

    @pytest.mark.asyncio
    async def test_all_services_covered(self, monkeypatch):
        """Проверяем, что все сервисы + gateway в результатах."""
        from gateway.client import check_all_services_health

        async def mock_check(name):
            return "ok"

        monkeypatch.setattr(
            "gateway.client.check_service_health",
            mock_check,
        )

        results = await check_all_services_health()
        assert len(results) >= 11
        assert "gateway" in results
