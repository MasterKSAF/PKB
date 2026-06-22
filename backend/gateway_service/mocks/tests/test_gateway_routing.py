"""
Unit tests for the REAL gateway's resolve_service() function.

Tests service routing logic directly from gateway.client, covering:
  - All /api/v1/registry/ sub-paths resolve to "registry"
  - Old paths without /registry/ return None (404)
  - Other service prefixes (auth, orchestrator, query) still work
  - Edge cases: exact match, trailing slashes, unknown paths, health endpoint
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import httpx
import pytest
from fastapi import Request
from gateway.client import resolve_service, proxy_request
from unittest.mock import AsyncMock, patch


# ===========================================================================
# Registry paths — /api/v1/registry/
# ===========================================================================

class TestRegistryPaths:
    """All paths under /api/v1/registry/ must resolve to 'registry'."""

    @pytest.mark.parametrize("path", [
        "/api/v1/registry/classifiers",
        "/api/v1/registry/classifiers/",
        "/api/v1/registry/classifiers/tree",
        "/api/v1/registry/terminology",
        "/api/v1/registry/terminology/",
        "/api/v1/registry/documents",
        "/api/v1/registry/documents/",
        "/api/v1/registry/common/stats",
        "/api/v1/registry/drafts",
    ])
    def test_registry_paths(self, path: str):
        assert resolve_service(path) == "registry"


# ===========================================================================
# Old paths (no /registry/) — should return None
# ===========================================================================

class TestOldPathsReturnNone:
    """Legacy paths without /api/v1/registry/ prefix must return None."""

    @pytest.mark.parametrize("path", [
        "/api/v1/classifiers",
        "/api/v1/classifiers/",
        "/api/v1/terminology",
        "/api/v1/common/stats",
    ])
    def test_old_paths_return_none(self, path: str):
        assert resolve_service(path) is None


# ===========================================================================
# Other service routes
# ===========================================================================

class TestOtherServices:
    """Other service prefixes must still resolve correctly."""

    def test_auth_me(self):
        assert resolve_service("/api/v1/auth/me") == "auth"

    def test_documents(self):
        assert resolve_service("/api/v1/documents/") == "orchestrator"

    def test_chat_sessions(self):
        assert resolve_service("/api/v1/chat/sessions") == "query"

    def test_rag_search(self):
        """RAG Search paths must resolve to 'rag_search'."""
        assert resolve_service("/api/v1/rag/search") == "rag_search"
        assert resolve_service("/api/v1/rag/") == "rag_search"


# ===========================================================================
# Edge cases
# ===========================================================================

class TestEdgeCases:
    """Boundary and edge cases for resolve_service."""

    def test_exact_match(self):
        """Exact match without trailing slash: /api/v1/registry → 'registry'."""
        assert resolve_service("/api/v1/registry") == "registry"

    def test_health_returns_none(self):
        """system/health is a gateway-owned endpoint, should return None."""
        assert resolve_service("/api/v1/system/health") is None

    def test_unknown_path_returns_none(self):
        """Completely unrecognised path should return None."""
        assert resolve_service("/api/v1/unknown/endpoint") is None


# ===========================================================================
# Trailing slash handling
# ===========================================================================

class TestTrailingSlashHandling:
    """resolve_service must not be affected by trailing slashes (no 307
    redirect needed — the function itself normalises the path)."""

    @pytest.mark.parametrize("path,expected", [
        ("/api/v1/registry/", "registry"),
        ("/api/v1/documents/", "orchestrator"),
        ("/api/v1/documents", "orchestrator"),
    ])
    def test_trailing_slashes(self, path: str, expected: str):
        """Both with and without trailing slash should resolve identically."""
        assert resolve_service(path) == expected


# ===========================================================================
# proxy_request path normalisation
# ===========================================================================

class TestProxyRequestPathNormalization:
    """Verifies proxy_request strips trailing slashes before forwarding to the
    downstream microservice, preventing unwanted 307 redirects from servers
    with redirect_slashes enabled."""

    @staticmethod
    def _make_request(path: str) -> Request:
        """Build a minimal fastapi.Request from an ASGI scope dict."""
        async def _receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        return Request({
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "server": ("testserver", 80),
            "path": path,
            "query_string": b"",
            "headers": [],
        }, receive=_receive)

    @pytest.mark.asyncio
    async def test_trailing_slash_is_stripped(self):
        """Path with trailing slash (/classifiers/) has it removed in target_url."""
        with (
            patch("gateway.client.get_client") as mock_get_client,
            patch("gateway.client.config") as mock_config,
        ):
            mock_config.service_urls = {"registry": "http://registry:8084"}

            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b""
            mock_client.request.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = self._make_request("/api/v1/registry/classifiers/")
            await proxy_request(request, "registry")

            url = mock_client.request.call_args.kwargs["url"]
            assert url == "http://registry:8084/api/v1/registry/classifiers", (
                f"Expected trailing slash stripped, got {url!r}"
            )

    @pytest.mark.asyncio
    async def test_no_trailing_slash_stays_unchanged(self):
        """Path without trailing slash stays as-is."""
        with (
            patch("gateway.client.get_client") as mock_get_client,
            patch("gateway.client.config") as mock_config,
        ):
            mock_config.service_urls = {"registry": "http://registry:8084"}

            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b""
            mock_client.request.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = self._make_request("/api/v1/registry/classifiers")
            await proxy_request(request, "registry")

            url = mock_client.request.call_args.kwargs["url"]
            assert url == "http://registry:8084/api/v1/registry/classifiers", (
                f"Expected unchanged path, got {url!r}"
            )

    @pytest.mark.asyncio
    async def test_root_path_stays_slash(self):
        """Root path / is preserved (edge case, not stripped to empty string)."""
        with (
            patch("gateway.client.get_client") as mock_get_client,
            patch("gateway.client.config") as mock_config,
        ):
            mock_config.service_urls = {"registry": "http://registry:8084"}

            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b""
            mock_client.request.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = self._make_request("/")
            await proxy_request(request, "registry")

            url = mock_client.request.call_args.kwargs["url"]
            assert url == "http://registry:8084/", (
                f"Expected root path /, got {url!r}"
            )
