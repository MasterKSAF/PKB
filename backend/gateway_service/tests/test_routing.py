"""
Тесты resolve_service() — таблица маршрутов ROUTE_TABLE.

Все сценарии из спецификации (51 тест):
  - Drafts: registry/orchestrator
  - Documents: registry/orchestrator
  - Registry direct, Tasks, Auth, Admin, Chat, Text, Analyse, RAG
  - Deprecated integration routes (410)
  - Invalid draft_id (400)
  - Unknown paths (404)
  - Trailing slash normalization
  - Priority: specific rules before generic

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.client import resolve_service, is_deprecated_integration_route


def _resolve(method: str, path: str):
    """Returns (service_name, target_path) or None."""
    return resolve_service(method, path)


def _service(method: str, path: str):
    """Returns just service name, for convenience."""
    result = resolve_service(method, path)
    return result[0] if result else None


def _target(method: str, path: str):
    """Returns just target path, for convenience."""
    result = resolve_service(method, path)
    return result[1] if result else None


class TestDraftsListToRegistry:
    """GET /api/v1/drafts — список черновиков, Registry с path transform."""

    def test_get_drafts_list(self):
        """#1 GET /api/v1/drafts → registry, target=/api/v1/registry/drafts."""
        svc, target = _resolve("GET", "/api/v1/drafts")
        assert svc == "registry"
        assert target == "/api/v1/registry/drafts"


class TestDraftDetailToOrchestrator:
    """GET /api/v1/drafts/{numeric_id} — детали черновика, Orchestrator."""

    @pytest.mark.parametrize("path", [
        "/api/v1/drafts/123",
        "/api/v1/drafts/456",
    ])
    def test_draft_detail_orchestrator(self, path: str):
        """#2-3 GET /api/v1/drafts/{id} → orchestrator."""
        result = _resolve("GET", path)
        assert result is not None
        svc, target = result
        assert svc == "orchestrator"
        assert target == path


class TestDraftPreviewGetRoute:
    """GET /api/v1/drafts/{id}/preview маршрутизируется в Orchestrator."""

    def test_preview_get_routes_to_orchestrator(self):
        """#4 GET /api/v1/drafts/5/preview → orchestrator."""
        result = _resolve("GET", "/api/v1/drafts/5/preview")
        assert result is not None
        svc, target = result
        assert svc == "orchestrator"
        assert target == "/api/v1/drafts/5/preview"


class TestDraftManageToOrchestrator:
    """Write/manage operations on drafts — Orchestrator."""

    @pytest.mark.parametrize("method,path", [
        ("POST",   "/api/v1/drafts"),
        ("POST",   "/api/v1/drafts/123/preview"),
        ("GET",    "/api/v1/drafts/123/preview/status"),
        ("PATCH",  "/api/v1/drafts/123/decide"),
        ("PATCH",  "/api/v1/drafts/123/metadata"),
        ("DELETE", "/api/v1/drafts/123"),
        ("GET",    "/api/v1/drafts/123/tasks"),
    ])
    def test_draft_manage_orchestrator(self, method: str, path: str):
        """#5-11 Draft manage → orchestrator."""
        svc, target = _resolve(method, path)
        assert svc == "orchestrator"
        assert target == path.rstrip("/")


class TestDocumentReadToRegistry:
    """Документы — операции чтения → Registry с path transform."""

    @pytest.mark.parametrize("method,path,expected_target", [
        ("GET", "/api/v1/documents", "/api/v1/registry/documents"),
        ("GET", "/api/v1/documents/1", "/api/v1/registry/documents/1"),
        ("PUT", "/api/v1/documents/1", "/api/v1/registry/documents/1"),
        ("PATCH", "/api/v1/documents/1", "/api/v1/registry/documents/1"),
        ("DELETE", "/api/v1/documents/1", "/api/v1/registry/documents/1"),
        ("GET", "/api/v1/documents/1/sections", "/api/v1/registry/documents/1/sections"),
        ("GET", "/api/v1/documents/1/pages", "/api/v1/registry/documents/1/pages"),
        ("GET", "/api/v1/documents/1/pages/1", "/api/v1/registry/documents/1/pages/1"),
        ("GET", "/api/v1/documents/1/file", "/api/v1/registry/documents/1/file"),
        ("GET", "/api/v1/documents/1/history", "/api/v1/registry/documents/1/history"),
        ("GET", "/api/v1/documents/1/parameters", "/api/v1/registry/documents/1/parameters"),
        ("GET", "/api/v1/documents/1/versions", "/api/v1/registry/documents/1/versions"),
        ("GET", "/api/v1/documents/1/succession", "/api/v1/registry/documents/1/succession"),
    ])
    def test_document_to_registry(self, method: str, path: str, expected_target: str):
        """#12-24 Document CRUD/sub-resources → registry."""
        svc, target = _resolve(method, path)
        assert svc == "registry"
        assert target == expected_target, f"Expected {expected_target}, got {target}"


class TestDocumentSpecialOpsToRegistry:
    """Search, export, import, check-uniqueness — Registry."""

    def test_search_post(self):
        """#25 POST /api/v1/documents/search → registry, target=/api/v1/registry/search."""
        svc, target = _resolve("POST", "/api/v1/documents/search")
        assert svc == "registry"
        assert target == "/api/v1/registry/search"

    def test_search_get(self):
        """#26 GET /api/v1/documents/search → registry, target=/api/v1/registry/search."""
        svc, target = _resolve("GET", "/api/v1/documents/search")
        assert svc == "registry"
        assert target == "/api/v1/registry/search"

    def test_export(self):
        """#27 GET /api/v1/documents/export → registry, target=/api/v1/registry/documents/export."""
        svc, target = _resolve("GET", "/api/v1/documents/export")
        assert svc == "registry"
        assert target == "/api/v1/registry/documents/export"

    def test_import(self):
        """#28 POST /api/v1/documents/import → registry."""
        svc, target = _resolve("POST", "/api/v1/documents/import")
        assert svc == "registry"
        assert target == "/api/v1/registry/documents/import"

    def test_check_uniqueness(self):
        """#29 POST /api/v1/documents/check-uniqueness → registry."""
        svc, target = _resolve("POST", "/api/v1/documents/check-uniqueness")
        assert svc == "registry"
        assert target == "/api/v1/registry/documents/check-uniqueness"


class TestDocumentPipelineToOrchestrator:
    """Pipeline ops, deprecated POST /documents — Orchestrator."""

    @pytest.mark.parametrize("method,path", [
        ("POST", "/api/v1/documents"),
        ("GET",  "/api/v1/documents/1/status"),
        ("GET",  "/api/v1/documents/queue"),
        ("GET",  "/api/v1/documents/1/errors"),
        ("POST", "/api/v1/documents/1/versions"),
        ("POST", "/api/v1/documents/1/reprocess"),
        ("GET",  "/api/v1/documents/1/tasks"),
    ])
    def test_pipeline_to_orchestrator(self, method: str, path: str):
        """#30-36 Document pipeline → orchestrator."""
        svc, target = _resolve(method, path)
        assert svc == "orchestrator"
        assert target == path.rstrip("/")


class TestDirectServicePrefixes:
    """All methods to /api/v1/registry/*, /api/v1/tasks/*, etc."""

    @pytest.mark.parametrize("prefix,expected_service", [
        ("/api/v1/registry",        "registry"),
        ("/api/v1/tasks",           "orchestrator"),
        ("/api/v1/auth",            "auth"),
        ("/api/v1/admin",           "auth"),
        ("/api/v1/chat",            "query"),
        ("/api/v1/text",            "query"),
        ("/api/v1/analyse",         "analyse"),
    ])
    def test_direct_prefix(self, prefix: str, expected_service: str):
        """#37-43 All-methods prefix routes."""
        for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            svc = _service(method, f"{prefix}/some/resource")
            assert svc == expected_service, (
                f"{method} {prefix}/some/resource → {svc}, expected {expected_service}"
            )

    def test_rag_prefix(self):
        """#44 /api/v1/rag/* → rag_search (путь как есть, без transform)."""
        svc, target = _resolve("GET", "/api/v1/rag/search")
        assert svc == "rag_search"
        assert target == "/api/v1/rag/search"

        svc, target = _resolve("POST", "/api/v1/rag/query")
        assert svc == "rag_search"
        assert target == "/api/v1/rag/query"


class TestDeprecatedIntegrationRoutes:
    """Legacy routes должны возвращать 410."""

    @pytest.mark.parametrize("path", [
        "/api/v1/meridian/test",
        "/api/v1/files/123",
        "/api/v1/external/sync",
        "/api/v1/meridian",
        "/api/v1/files",
        "/api/v1/external",
    ])
    def test_deprecated_routes(self, path: str):
        """#45-47 is_deprecated_integration_route → True."""
        assert is_deprecated_integration_route(path), f"{path} should be deprecated"


class TestInvalidDraftId:
    """Нечисловой draft_id не матчится ни одним правилом → None."""

    @pytest.mark.parametrize("path", [
        "/api/v1/drafts/abc",
        "/api/v1/drafts/abc/tasks",
        "/api/v1/drafts/abc/preview",
        "/api/v1/drafts/abc/decide",
        "/api/v1/drafts/abc/metadata",
    ])
    def test_non_numeric_draft_id(self, path: str):
        """#48 GET /api/v1/drafts/abc → None."""
        assert _resolve("GET", path) is None


class TestUnknownPath:
    """Полностью неизвестный путь — None."""

    @pytest.mark.parametrize("path", [
        "/api/v1/unknown/path",
        "/api/v1/drafts/123/nonexistent",
        "/api/v1/documents/999/nonexistent",
    ])
    def test_unknown_path(self, path: str):
        """#49 Unknown path → None."""
        assert _resolve("GET", path) is None

    def test_registry_exact_match_not_unknown(self):
        """/api/v1/registry (без слеша) матчится как registry."""
        svc, _ = _resolve("GET", "/api/v1/registry")
        assert svc == "registry"


class TestTrailingSlash:
    """resolve_service нормализует trailing slash."""

    @pytest.mark.parametrize("method,path,expected_service", [
        ("GET",  "/api/v1/drafts/",    "registry"),
        ("GET",  "/api/v1/drafts",     "registry"),
        ("POST", "/api/v1/drafts/",    "orchestrator"),
        ("POST", "/api/v1/drafts",     "orchestrator"),
    ])
    def test_trailing_slash_normalized(self, method: str, path: str, expected_service: str):
        """#50 Trailing slash — normalize before matching."""
        svc = _service(method, path)
        assert svc == expected_service


class TestPrioritySpecificOverGeneric:
    """Специфичные правила имеют приоритет над общими."""

    def test_draft_detail_precedes_registry_prefix(self):
        """#51 GET /api/v1/drafts/123 → orchestrator (specific), not registry."""
        svc = _service("GET", "/api/v1/drafts/123")
        assert svc == "orchestrator"

    def test_document_status_precedes_registry_crud(self):
        """GET /api/v1/documents/1/status → orchestrator (specific)."""
        svc = _service("GET", "/api/v1/documents/1/status")
        assert svc == "orchestrator"

    def test_document_crud_precedes_registry_prefix(self):
        """GET /api/v1/documents/1 → registry (via transform)."""
        svc = _service("GET", "/api/v1/documents/1")
        assert svc == "registry"

    def test_registry_prefix_fallback(self):
        """Любой /api/v1/registry/* → registry (fallback)."""
        svc = _service("GET", "/api/v1/registry/custom/endpoint")
        assert svc == "registry"
        svc = _service("POST", "/api/v1/registry/custom")
        assert svc == "registry"


class TestGatewayOwnEndpoints:
    """Эндпоинты Gateway не должны проксироваться."""

    @pytest.mark.parametrize("path", [
        "/api/v1/system/health",
        "/api/v1/system/mode",
        "/api/v1/health",
        "/api/v1/system/health/live",
        "/api/v1/system/health/ready",
    ])
    def test_gateway_endpoints_return_none(self, path: str):
        """Gateway-owned endpoints → None (не проксируются)."""
        assert _resolve("GET", path) is None


class TestMethodSpecificity:
    """Разные методы на одном пути ведут к разным сервисам."""

    def test_drafts_get_vs_post(self):
        """GET /api/v1/drafts → registry, POST → orchestrator."""
        assert _service("GET", "/api/v1/drafts") == "registry"
        assert _service("POST", "/api/v1/drafts") == "orchestrator"

    def test_documents_get_vs_post(self):
        """GET /api/v1/documents → registry, POST → orchestrator (deprecated)."""
        assert _service("GET", "/api/v1/documents") == "registry"
        assert _service("POST", "/api/v1/documents") == "orchestrator"
