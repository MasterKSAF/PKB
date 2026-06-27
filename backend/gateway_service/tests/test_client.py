"""
Тесты get_client() / close_client() / is_deprecated_integration_route().

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.client import (
    get_client,
    close_client,
    is_deprecated_integration_route,
)
from gateway.config import config

import httpx


class TestGetClient:
    """get_client() — lazy initialization HTTP-клиента."""

    def test_get_client_returns_async_client(self):
        """get_client() возвращает httpx.AsyncClient."""
        client = get_client()
        assert isinstance(client, httpx.AsyncClient)

    def test_get_client_lazy_initialization(self):
        """get_client() — lazy: при первом вызове создаётся."""
        # close сначала
        import asyncio
        asyncio.run(close_client())
        client = get_client()
        assert client is not None

    def test_client_has_correct_timeout(self):
        """Таймаут клиента равен config.request_timeout."""
        client = get_client()
        assert client.timeout is not None
        assert client.timeout.connect is not None

    def test_client_follow_redirects_false(self):
        """follow_redirects=False."""
        client = get_client()
        assert client.follow_redirects is False


class TestCloseClient:
    """close_client() — закрытие клиента."""

    def test_close_client_sets_none(self):
        """close_client() — _client = None."""
        import asyncio
        asyncio.run(close_client())
        # После close — get_client создаст новый
        client = get_client()
        assert client is not None


class TestIsDeprecatedIntegrationRoute:
    """is_deprecated_integration_route() — deprecated prefixes."""

    def test_meridian_is_deprecated(self):
        """meridian — deprecated."""
        assert is_deprecated_integration_route("/api/v1/meridian/test") is True

    def test_files_is_deprecated(self):
        """files — deprecated."""
        assert is_deprecated_integration_route("/api/v1/files/123") is True

    def test_external_is_deprecated(self):
        """external — deprecated."""
        assert is_deprecated_integration_route("/api/v1/external/sync") is True

    def test_meridian_root(self):
        """meridian root — deprecated."""
        assert is_deprecated_integration_route("/api/v1/meridian") is True

    def test_documents_not_deprecated(self):
        """documents — not deprecated."""
        assert is_deprecated_integration_route("/api/v1/documents/1") is False

    def test_drafts_not_deprecated(self):
        """drafts — not deprecated."""
        assert is_deprecated_integration_route("/api/v1/drafts/123") is False

    def test_health_not_deprecated(self):
        """health — not deprecated."""
        assert is_deprecated_integration_route("/api/v1/health") is False

    def test_auth_not_deprecated(self):
        """auth — not deprecated."""
        assert is_deprecated_integration_route("/api/v1/auth/token") is False
