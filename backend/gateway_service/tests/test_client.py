"""
Tests for client utilities: get_client(), close_client(), is_deprecated_integration_route().

Проверяет:
  - get_client(): lazy initialization, timeout, follow_redirects
  - close_client(): клиент закрыт, _client = None
  - is_deprecated_integration_route(): meridian, files, external
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch

from gateway.client import get_client, close_client, is_deprecated_integration_route


class TestGetClient:
    """get_client() — lazy initialization."""

    @pytest.fixture(autouse=True)
    async def _cleanup_client(self):
        """Закрываем клиент после каждого теста, чтобы сбросить состояние."""
        yield
        try:
            await close_client()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_get_client_returns_async_client(self):
        """get_client() возвращает httpx.AsyncClient."""
        client = get_client()
        import httpx
        assert isinstance(client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_get_client_lazy_init(self):
        """Первый вызов создаёт клиент, второй возвращает тот же."""
        await close_client()
        c1 = get_client()
        c2 = get_client()
        assert c1 is c2  # тот же экземпляр

    @pytest.mark.asyncio
    async def test_get_client_timeout(self):
        """Таймаут клиента равен config.request_timeout."""
        from gateway.config import config
        client = get_client()
        assert client.timeout is not None

    @pytest.mark.asyncio
    async def test_get_client_follow_redirects_false(self):
        """follow_redirects=False."""
        client = get_client()
        # httpx.AsyncClient хранит follow_redirects
        assert not client.follow_redirects


class TestCloseClient:
    """close_client() — очистка состояния."""

    @pytest.mark.asyncio
    async def test_close_client_resets_to_none(self):
        """После close_client() _client = None."""
        get_client()  # инициализируем
        await close_client()
        from gateway.client import _client as cl
        assert cl is None

    @pytest.mark.asyncio
    async def test_close_client_twice_no_error(self):
        """Двойной close_client() не вызывает ошибку."""
        await close_client()
        await close_client()


class TestIsDeprecatedIntegrationRoute:
    """is_deprecated_integration_route() — legacy routes."""

    @pytest.mark.parametrize("path,expected", [
        ("/api/v1/meridian/test", True),
        ("/api/v1/files/123", True),
        ("/api/v1/external/sync", True),
        ("/api/v1/meridian", True),
        ("/api/v1/files", True),
        ("/api/v1/external", True),
        ("/api/v1/documents/1", False),
        ("/api/v1/drafts/1", False),
        ("/api/v1/auth/me", False),
        ("/api/v1/registry/classifiers", False),
        ("/api/v1/chat/sessions", False),
        ("/api/v1/system/health", False),
        ("/api/v1/health", False),
    ])
    def test_deprecated_routes(self, path: str, expected: bool):
        """Проверка deprecated-маршрутов."""
        assert is_deprecated_integration_route(path) == expected
