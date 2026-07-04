"""
Unit tests for the REAL gateway's resolve_service() function.

Tests service routing logic directly from gateway.client, covering:
  - Registry: draft reading (GET) → registry
  - Orchestrator: draft write/manage → orchestrator
  - Registry: document CRUD → registry (with path transformation)
  - Orchestrator: document pipeline operations → orchestrator
  - Registry: /api/v1/registry/* → registry
  - Other services (auth, query, etc.) still work
  - Edge cases: trailing slashes, unknown paths, health endpoint
  - Path transformation for Registry
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import httpx
import pytest
from fastapi import Request
from gateway.client import resolve_service, proxy_request, ROUTE_TABLE
from unittest.mock import AsyncMock, patch


# ===========================================================================
# Helper: run resolve_service with default GET method
# ===========================================================================

def _resolve(method: str, path: str):
    """Helper to call resolve_service and return just the service name."""
    result = resolve_service(method, path)
    return result[0] if result else None


def _resolve_full(method: str, path: str):
    """Helper to call resolve_service and return full result."""
    return resolve_service(method, path)


# ===========================================================================
# Registry: draft reading (GET) → registry
# ===========================================================================

class TestDraftReadToRegistry:
    """GET /api/v1/drafts/* must resolve to 'registry' with path transform."""

    @pytest.mark.parametrize("method,path", [
        ("GET", "/api/v1/drafts"),
        ("GET", "/api/v1/drafts/123"),
        ("GET", "/api/v1/drafts/42"),
    ])
    def test_draft_read_to_registry(self, method: str, path: str):
        service, target = _resolve_full(method, path)
        assert service == "registry"
        # Path must be transformed: /api/v1/drafts → /api/v1/registry/drafts
        expected = path.replace("/api/v1/drafts", "/api/v1/registry/drafts", 1)
        assert target == expected, f"Expected {expected}, got {target}"

    def test_draft_preview_read_to_registry(self):
        """GET /api/v1/drafts/{id}/preview → registry."""
        service, target = _resolve_full("GET", "/api/v1/drafts/5/preview")
        assert service == "registry"
        assert target == "/api/v1/registry/drafts/5/preview"


# ===========================================================================
# Orchestrator: draft write/manage → orchestrator
# ===========================================================================

class TestDraftWriteToOrchestrator:
    """Write/manage operations on drafts must resolve to 'orchestrator'."""

    @pytest.mark.parametrize("method,path", [
        ("POST", "/api/v1/drafts"),
        ("POST", "/api/v1/drafts/123/preview"),
        ("GET", "/api/v1/drafts/123/preview/status"),
        ("PATCH", "/api/v1/drafts/123/decide"),
        ("PATCH", "/api/v1/drafts/123/metadata"),
        ("DELETE", "/api/v1/drafts/123"),
        ("GET", "/api/v1/drafts/123/tasks"),
    ])
    def test_draft_write_to_orchestrator(self, method: str, path: str):
        service, target = _resolve_full(method, path)
        assert service == "orchestrator"
        # No transform — target should equal normalized path
        assert target == path.rstrip("/")


# ===========================================================================
# Registry: document CRUD → registry
# ===========================================================================

class TestDocumentCrudToRegistry:
    """CRUD operations on documents must resolve to 'registry' with path transform."""

    @pytest.mark.parametrize("method,path", [
        ("GET", "/api/v1/documents"),
        ("GET", "/api/v1/documents/123"),
        ("PUT", "/api/v1/documents/123"),
        ("PATCH", "/api/v1/documents/123"),
        ("DELETE", "/api/v1/documents/123"),
    ])
    def test_document_crud_to_registry(self, method: str, path: str):
        service, target = _resolve_full(method, path)
        assert service == "registry"
        # Path must be transformed: /api/v1/documents → /api/v1/registry/documents
        expected = path.replace("/api/v1/documents", "/api/v1/registry/documents", 1)
        assert target == expected, f"Expected {expected}, got {target}"


# ===========================================================================
# Registry: document sub-resources → registry
# ===========================================================================

class TestDocumentSubResourcesToRegistry:
    """Document sub-resources (pages, file, history, etc.) → registry."""

    @pytest.mark.parametrize("path", [
        "/api/v1/documents/123/sections",
        "/api/v1/documents/123/pages",
        "/api/v1/documents/123/pages/1",
        "/api/v1/documents/123/pages/1/text",
        "/api/v1/documents/123/pages/1/preview",
                "/api/v1/documents/123/pages/1/content_md",
        "/api/v1/documents/123/file",
        "/api/v1/documents/123/history",
        "/api/v1/documents/123/parameters",
        "/api/v1/documents/123/versions",
        "/api/v1/documents/123/succession",
    ])
    def test_document_sub_resource(self, path: str):
        service, target = _resolve_full("GET", path)
        assert service == "registry"
        # Path must be transformed
        expected = path.replace("/api/v1/documents", "/api/v1/registry/documents", 1)
        assert target == expected, f"Expected {expected}, got {target}"


# ===========================================================================
# Registry: document special operations → registry
# ===========================================================================

class TestDocumentSpecialOpsToRegistry:
    """Search, export, import, check-uniqueness → registry."""

    def test_search_get(self):
        """GET /api/v1/documents/search → registry, target = /api/v1/registry/search."""
        service, target = _resolve_full("GET", "/api/v1/documents/search")
        assert service == "registry"
        assert target == "/api/v1/registry/search", (
            f"Expected /api/v1/registry/search, got {target}"
        )

    def test_search_post(self):
        """POST /api/v1/documents/search → registry, target = /api/v1/registry/search."""
        service, target = _resolve_full("POST", "/api/v1/documents/search")
        assert service == "registry"
        assert target == "/api/v1/registry/search"

    def test_export(self):
        """GET /api/v1/documents/export → registry."""
        service, target = _resolve_full("GET", "/api/v1/documents/export")
        assert service == "registry"
        assert target == "/api/v1/registry/documents/export"

    def test_import(self):
        """POST /api/v1/documents/import → registry."""
        service, target = _resolve_full("POST", "/api/v1/documents/import")
        assert service == "registry"
        assert target == "/api/v1/registry/documents/import"

    def test_check_uniqueness(self):
        """POST /api/v1/documents/check-uniqueness → registry."""
        service, target = _resolve_full("POST", "/api/v1/documents/check-uniqueness")
        assert service == "registry"
        assert target == "/api/v1/registry/documents/check-uniqueness"


# ===========================================================================
# Orchestrator: document pipeline operations → orchestrator
# ===========================================================================

class TestDocumentPipelineToOrchestrator:
    """Pipeline operations on documents must resolve to 'orchestrator'."""

    @pytest.mark.parametrize("method,path", [
        ("POST", "/api/v1/documents"),  # deprecated (OR-11), returns 410
        ("GET", "/api/v1/documents/123/status"),
        ("GET", "/api/v1/documents/queue"),
        ("GET", "/api/v1/documents/123/errors"),
        ("POST", "/api/v1/documents/123/versions"),
        ("POST", "/api/v1/documents/123/reprocess"),
        ("GET", "/api/v1/documents/123/tasks"),
    ])
    def test_document_pipeline_to_orchestrator(self, method: str, path: str):
        service, target = _resolve_full(method, path)
        assert service == "orchestrator"
        # No transform — target should equal normalized path
        assert target == path.rstrip("/")


# ===========================================================================
# Registry: /api/v1/registry/* (direct access)
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
        service, target = _resolve_full("GET", path)
        assert service == "registry"
        # Direct /api/v1/registry/* paths stay unchanged
        normalized = path.rstrip("/")
        assert target == normalized, f"Expected {normalized}, got {target}"


# ===========================================================================
# Other service routes
# ===========================================================================

class TestOtherServices:
    """Other service prefixes must still resolve correctly."""

    def test_auth_me(self):
        assert _resolve("GET", "/api/v1/auth/me") == "auth"

    def test_admin_users(self):
        assert _resolve("GET", "/api/v1/admin/users") == "auth"

    def test_chat_sessions(self):
        assert _resolve("GET", "/api/v1/chat/sessions") == "query"

    def test_text_search(self):
        assert _resolve("POST", "/api/v1/text/search") == "query"

    def test_rag_search(self):
        assert _resolve("POST", "/api/v1/rag/search") == "rag_search"

    def test_analyse(self):
        assert _resolve("POST", "/api/v1/analyse/compare") == "analyse"

    def test_tasks_list(self):
        assert _resolve("GET", "/api/v1/tasks") == "orchestrator"

    def test_tasks_status(self):
        assert _resolve("GET", "/api/v1/tasks/1/status") == "orchestrator"

    def test_tasks_get(self):
        assert _resolve("GET", "/api/v1/tasks/42/steps") == "orchestrator"


# ===========================================================================
# Edge cases
# ===========================================================================

class TestEdgeCases:
    """Boundary and edge cases for resolve_service."""

    def test_health_returns_none(self):
        """system/health is a gateway-owned endpoint, should return None."""
        assert resolve_service("GET", "/api/v1/system/health") is None

    def test_mode_returns_none(self):
        """system/mode is a gateway-owned endpoint, should return None."""
        assert resolve_service("GET", "/api/v1/system/mode") is None

    def test_unknown_path_returns_none(self):
        """Completely unrecognised path should return None."""
        assert resolve_service("GET", "/api/v1/unknown/endpoint") is None

    def test_deprecated_integration_still_works(self):
        """Deprecated integration prefixes are handled before resolve_service."""
        from gateway.client import is_deprecated_integration_route
        assert is_deprecated_integration_route("/api/v1/meridian/export")
        assert is_deprecated_integration_route("/api/v1/files/upload")
        assert is_deprecated_integration_route("/api/v1/external/callback")


# ===========================================================================
# Method filtering
# ===========================================================================

class TestMethodFiltering:
    """resolve_service must respect HTTP method restrictions."""

    def test_drafts_post_is_orchestrator(self):
        """POST /api/v1/drafts is orchestrator (write), not registry."""
        assert _resolve("POST", "/api/v1/drafts") == "orchestrator"

    def test_drafts_get_is_registry(self):
        """GET /api/v1/drafts is registry (read), not orchestrator."""
        assert _resolve("GET", "/api/v1/drafts") == "registry"

    def test_document_status_get_is_orchestrator(self):
        """GET /api/v1/documents/1/status → orchestrator (pipeline)."""
        assert _resolve("GET", "/api/v1/documents/1/status") == "orchestrator"

    def test_document_get_is_registry(self):
        """GET /api/v1/documents/1 → registry (data read)."""
        assert _resolve("GET", "/api/v1/documents/1") == "registry"

    def test_document_delete_is_registry(self):
        """DELETE /api/v1/documents/1 → registry (data deletion)."""
        assert _resolve("DELETE", "/api/v1/documents/1") == "registry"


# ===========================================================================
# Trailing slash handling
# ===========================================================================

class TestTrailingSlashHandling:
    """resolve_service must not be affected by trailing slashes."""

    @pytest.mark.parametrize("method,path,expected_service", [
        ("GET", "/api/v1/registry/", "registry"),
        ("GET", "/api/v1/registry", "registry"),
        ("GET", "/api/v1/documents", "registry"),
        ("POST", "/api/v1/drafts/", "orchestrator"),
        ("POST", "/api/v1/drafts", "orchestrator"),
        ("GET", "/api/v1/tasks", "orchestrator"),
        ("GET", "/api/v1/auth/me/", "auth"),
    ])
    def test_trailing_slashes(self, method: str, path: str, expected_service: str):
        """Both with and without trailing slash should resolve identically."""
        assert _resolve(method, path) == expected_service


# ===========================================================================
# Path transformation (URL-transformation for Registry)
# ===========================================================================

class TestPathTransformation:
    """verify that paths are correctly transformed for Registry."""

    def test_document_path_transformed(self):
        """/api/v1/documents/123 → /api/v1/registry/documents/123."""
        _, target = _resolve_full("GET", "/api/v1/documents/123")
        assert target == "/api/v1/registry/documents/123"

    def test_draft_path_transformed(self):
        """/api/v1/drafts/42 → /api/v1/registry/drafts/42."""
        _, target = _resolve_full("GET", "/api/v1/drafts/42")
        assert target == "/api/v1/registry/drafts/42"

    def test_document_pages_path_transformed(self):
        """/api/v1/documents/1/pages/1 → /api/v1/registry/documents/1/pages/1."""
        _, target = _resolve_full("GET", "/api/v1/documents/1/pages/1")
        assert target == "/api/v1/registry/documents/1/pages/1"

    def test_search_path_transformed_special(self):
        """/api/v1/documents/search → /api/v1/registry/search (special case)."""
        _, target = _resolve_full("GET", "/api/v1/documents/search")
        assert target == "/api/v1/registry/search"

    def test_orchestrator_path_not_transformed(self):
        """Orchestrator paths remain unchanged (no path transform)."""
        _, target = _resolve_full("POST", "/api/v1/drafts")
        assert target == "/api/v1/drafts"
        _, target = _resolve_full("POST", "/api/v1/drafts/1/preview")
        assert target == "/api/v1/drafts/1/preview"

    def test_tasks_path_not_transformed(self):
        """/api/v1/tasks/* → orchestrator, no transform."""
        _, target = _resolve_full("GET", "/api/v1/tasks/1/status")
        assert target == "/api/v1/tasks/1/status"


# ===========================================================================
# proxy_request with target_path
# ===========================================================================

class TestProxyRequestWithTargetPath:
    """Verifies proxy_request uses target_path when provided."""

    @staticmethod
    def _make_request(path: str, method: str = "GET") -> Request:
        """Build a minimal fastapi.Request from an ASGI scope dict."""
        async def _receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        return Request({
            "type": "http",
            "method": method,
            "scheme": "http",
            "server": ("testserver", 80),
            "path": path,
            "query_string": b"",
            "headers": [],
        }, receive=_receive)

    @pytest.mark.asyncio
    async def test_target_path_is_used(self):
        """target_path parameter should override the original path."""
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

            request = self._make_request("/api/v1/documents/123")
            # Pass transformed target_path
            await proxy_request(request, "registry", "/api/v1/registry/documents/123")

            url = mock_client.request.call_args.kwargs["url"]
            assert url == "http://registry:8084/api/v1/registry/documents/123", (
                f"Expected transformed path, got {url!r}"
            )

    @pytest.mark.asyncio
    async def test_no_target_path_uses_original(self):
        """Without target_path, the original path should be used."""
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
                f"Expected original path, got {url!r}"
            )


# ===========================================================================
# Full integration: resolve_service + proxy_request
# ===========================================================================

class TestResolveAndProxyIntegration:
    """End-to-end: resolve_service determines the route, proxy_request uses it."""

    @staticmethod
    def _make_request(path: str, method: str = "GET") -> Request:
        async def _receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        return Request({
            "type": "http",
            "method": method,
            "scheme": "http",
            "server": ("testserver", 80),
            "path": path,
            "query_string": b"",
            "headers": [],
        }, receive=_receive)

    @pytest.mark.asyncio
    async def test_document_get_goes_to_registry_with_transform(self):
        """GET /api/v1/documents/1 → resolve → proxy to registry at /api/v1/registry/documents/1."""
        with (
            patch("gateway.client.get_client") as mock_get_client,
            patch("gateway.client.config") as mock_config,
        ):
            mock_config.service_urls = {"registry": "http://registry:8084"}
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.content = b'{"data": {"id": 1}}'
            mock_client.request.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = self._make_request("/api/v1/documents/1")
            result = resolve_service("GET", "/api/v1/documents/1")
            assert result is not None
            service, target = result
            response = await proxy_request(request, service, target)

            url = mock_client.request.call_args.kwargs["url"]
            assert url == "http://registry:8084/api/v1/registry/documents/1"
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_document_status_goes_to_orchestrator(self):
        """GET /api/v1/documents/1/status → resolve → proxy to orchestrator without transform."""
        with (
            patch("gateway.client.get_client") as mock_get_client,
            patch("gateway.client.config") as mock_config,
        ):
            mock_config.service_urls = {"orchestrator": "http://orchestrator:8081"}
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.content = b'{"status": "indexed"}'
            mock_client.request.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = self._make_request("/api/v1/documents/1/status")
            result = resolve_service("GET", "/api/v1/documents/1/status")
            assert result is not None
            service, target = result
            response = await proxy_request(request, service, target)

            url = mock_client.request.call_args.kwargs["url"]
            assert url == "http://orchestrator:8081/api/v1/documents/1/status"
            assert response.status_code == 200
