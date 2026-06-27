"""
Тесты resolve_service() — таблица маршрутов ROUTE_TABLE.

51 сценарий: проверка соответствия (method, path) → (service, target_path).
Все тесты — unit, не требуют Docker.
"""

from __future__ import annotations

import os
import sys
import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.client import resolve_service, is_deprecated_integration_route


# ===================================================================
# Registry: черновики (только список GET /api/v1/drafts)
# ===================================================================


def test_drafts_get_goes_to_registry_with_transform():
    """GET /api/v1/drafts → registry, path: /api/v1/registry/drafts."""
    result = resolve_service("GET", "/api/v1/drafts")
    assert result is not None
    svc, target = result
    assert svc == "registry"
    assert target == "/api/v1/registry/drafts"


# ===================================================================
# Orchestrator: детали черновика
# ===================================================================


def test_draft_detail_get_goes_to_orchestrator():
    """GET /api/v1/drafts/123 → orchestrator (без transform)."""
    result = resolve_service("GET", "/api/v1/drafts/123")
    assert result is not None
    svc, target = result
    assert svc == "orchestrator"
    assert target == "/api/v1/drafts/123"


def test_draft_detail_another_id():
    """GET /api/v1/drafts/456 → orchestrator."""
    result = resolve_service("GET", "/api/v1/drafts/456")
    assert result is not None
    assert result[0] == "orchestrator"


# ===================================================================
# Preview — только POST, GET отсутствует
# ===================================================================


def test_draft_preview_get_returns_none():
    """GET /api/v1/drafts/5/preview → None (нет GET-маршрута)."""
    result = resolve_service("GET", "/api/v1/drafts/5/preview")
    assert result is None, "GET preview не должен быть разрешён"


# ===================================================================
# Orchestrator: создание/управление черновиком
# ===================================================================


def test_drafts_post_goes_to_orchestrator():
    """POST /api/v1/drafts → orchestrator."""
    result = resolve_service("POST", "/api/v1/drafts")
    assert result is not None
    assert result[0] == "orchestrator"


def test_draft_preview_post_goes_to_orchestrator():
    """POST /api/v1/drafts/123/preview → orchestrator."""
    result = resolve_service("POST", "/api/v1/drafts/123/preview")
    assert result is not None
    assert result[0] == "orchestrator"


def test_draft_preview_status_get_goes_to_orchestrator():
    """GET /api/v1/drafts/123/preview/status → orchestrator."""
    result = resolve_service("GET", "/api/v1/drafts/123/preview/status")
    assert result is not None
    assert result[0] == "orchestrator"


def test_draft_decide_patch_goes_to_orchestrator():
    """PATCH /api/v1/drafts/123/decide → orchestrator."""
    result = resolve_service("PATCH", "/api/v1/drafts/123/decide")
    assert result is not None
    assert result[0] == "orchestrator"


def test_draft_metadata_patch_goes_to_orchestrator():
    """PATCH /api/v1/drafts/123/metadata → orchestrator."""
    result = resolve_service("PATCH", "/api/v1/drafts/123/metadata")
    assert result is not None
    assert result[0] == "orchestrator"


def test_draft_delete_goes_to_orchestrator():
    """DELETE /api/v1/drafts/123 → orchestrator."""
    result = resolve_service("DELETE", "/api/v1/drafts/123")
    assert result is not None
    assert result[0] == "orchestrator"


def test_draft_tasks_get_goes_to_orchestrator():
    """GET /api/v1/drafts/123/tasks → orchestrator."""
    result = resolve_service("GET", "/api/v1/drafts/123/tasks")
    assert result is not None
    assert result[0] == "orchestrator"


# ===================================================================
# Registry: документы CRUD
# ===================================================================


def test_documents_list_goes_to_registry():
    """GET /api/v1/documents → registry c transform."""
    result = resolve_service("GET", "/api/v1/documents")
    assert result is not None
    svc, target = result
    assert svc == "registry"
    assert "/api/v1/registry/documents" in target


def test_document_detail_get_goes_to_registry():
    """GET /api/v1/documents/1 → registry c transform."""
    result = resolve_service("GET", "/api/v1/documents/1")
    assert result is not None
    svc, target = result
    assert svc == "registry"
    assert target == "/api/v1/registry/documents/1"


def test_document_put_goes_to_registry():
    """PUT /api/v1/documents/1 → registry."""
    result = resolve_service("PUT", "/api/v1/documents/1")
    assert result is not None
    assert result[0] == "registry"


def test_document_patch_goes_to_registry():
    """PATCH /api/v1/documents/1 → registry."""
    result = resolve_service("PATCH", "/api/v1/documents/1")
    assert result is not None
    assert result[0] == "registry"


def test_document_delete_goes_to_registry():
    """DELETE /api/v1/documents/1 → registry."""
    result = resolve_service("DELETE", "/api/v1/documents/1")
    assert result is not None
    assert result[0] == "registry"


# ===================================================================
# Registry: подресурсы документа
# ===================================================================


def test_document_sections_goes_to_registry():
    """GET /api/v1/documents/1/sections → registry."""
    result = resolve_service("GET", "/api/v1/documents/1/sections")
    assert result is not None
    assert result[0] == "registry"


def test_document_pages_goes_to_registry():
    """GET /api/v1/documents/1/pages → registry."""
    result = resolve_service("GET", "/api/v1/documents/1/pages")
    assert result is not None
    assert result[0] == "registry"


def test_document_page_detail_goes_to_registry():
    """GET /api/v1/documents/1/pages/1 → registry."""
    result = resolve_service("GET", "/api/v1/documents/1/pages/1")
    assert result is not None
    assert result[0] == "registry"


def test_document_file_goes_to_registry():
    """GET /api/v1/documents/1/file → registry."""
    result = resolve_service("GET", "/api/v1/documents/1/file")
    assert result is not None
    assert result[0] == "registry"


def test_document_history_goes_to_registry():
    """GET /api/v1/documents/1/history → registry."""
    result = resolve_service("GET", "/api/v1/documents/1/history")
    assert result is not None
    assert result[0] == "registry"


def test_document_parameters_goes_to_registry():
    """GET /api/v1/documents/1/parameters → registry."""
    result = resolve_service("GET", "/api/v1/documents/1/parameters")
    assert result is not None
    assert result[0] == "registry"


def test_document_versions_goes_to_registry():
    """GET /api/v1/documents/1/versions → registry."""
    result = resolve_service("GET", "/api/v1/documents/1/versions")
    assert result is not None
    assert result[0] == "registry"


def test_document_succession_goes_to_registry():
    """GET /api/v1/documents/1/succession → registry."""
    result = resolve_service("GET", "/api/v1/documents/1/succession")
    assert result is not None
    assert result[0] == "registry"


# ===================================================================
# Registry: массовые/спец. операции
# ===================================================================


def test_document_search_post_goes_to_registry():
    """POST /api/v1/documents/search → registry, target /api/v1/registry/search."""
    result = resolve_service("POST", "/api/v1/documents/search")
    assert result is not None
    svc, target = result
    assert svc == "registry"
    assert target == "/api/v1/registry/search"


def test_document_search_get_goes_to_registry():
    """GET /api/v1/documents/search → registry."""
    result = resolve_service("GET", "/api/v1/documents/search")
    assert result is not None
    assert result[0] == "registry"


def test_document_export_goes_to_registry():
    """GET /api/v1/documents/export → registry."""
    result = resolve_service("GET", "/api/v1/documents/export")
    assert result is not None
    assert result[0] == "registry"


def test_document_import_goes_to_registry():
    """POST /api/v1/documents/import → registry."""
    result = resolve_service("POST", "/api/v1/documents/import")
    assert result is not None
    assert result[0] == "registry"


def test_document_check_uniqueness_goes_to_registry():
    """POST /api/v1/documents/check-uniqueness → registry."""
    result = resolve_service("POST", "/api/v1/documents/check-uniqueness")
    assert result is not None
    assert result[0] == "registry"


# ===================================================================
# Orchestrator: документы — deprecated + пайплайн
# ===================================================================


def test_documents_post_deprecated_goes_to_orchestrator():
    """POST /api/v1/documents → orchestrator (deprecated OR-11)."""
    result = resolve_service("POST", "/api/v1/documents")
    assert result is not None
    assert result[0] == "orchestrator"


def test_document_status_goes_to_orchestrator():
    """GET /api/v1/documents/1/status → orchestrator."""
    result = resolve_service("GET", "/api/v1/documents/1/status")
    assert result is not None
    assert result[0] == "orchestrator"


def test_document_queue_goes_to_orchestrator():
    """GET /api/v1/documents/queue → orchestrator."""
    result = resolve_service("GET", "/api/v1/documents/queue")
    assert result is not None
    assert result[0] == "orchestrator"


def test_document_errors_goes_to_orchestrator():
    """GET /api/v1/documents/1/errors → orchestrator."""
    result = resolve_service("GET", "/api/v1/documents/1/errors")
    assert result is not None
    assert result[0] == "orchestrator"


def test_document_versions_post_goes_to_orchestrator():
    """POST /api/v1/documents/1/versions → orchestrator."""
    result = resolve_service("POST", "/api/v1/documents/1/versions")
    assert result is not None
    assert result[0] == "orchestrator"


def test_document_reprocess_goes_to_orchestrator():
    """POST /api/v1/documents/1/reprocess → orchestrator."""
    result = resolve_service("POST", "/api/v1/documents/1/reprocess")
    assert result is not None
    assert result[0] == "orchestrator"


def test_document_tasks_goes_to_orchestrator():
    """GET /api/v1/documents/1/tasks → orchestrator."""
    result = resolve_service("GET", "/api/v1/documents/1/tasks")
    assert result is not None
    assert result[0] == "orchestrator"


# ===================================================================
# Прямой доступ к сервисам
# ===================================================================


def test_registry_prefix_all_methods():
    """ALL_METHODS /api/v1/registry/* → registry без transform."""
    result = resolve_service("GET", "/api/v1/registry/classifiers")
    assert result is not None
    assert result[0] == "registry"

    result = resolve_service("POST", "/api/v1/registry/classifiers")
    assert result is not None
    assert result[0] == "registry"


def test_tasks_prefix_goes_to_orchestrator():
    """ALL_METHODS /api/v1/tasks/* → orchestrator."""
    result = resolve_service("GET", "/api/v1/tasks/123")
    assert result is not None
    assert result[0] == "orchestrator"

    result = resolve_service("POST", "/api/v1/tasks")
    assert result is not None
    assert result[0] == "orchestrator"


def test_auth_prefix_goes_to_auth():
    """ALL_METHODS /api/v1/auth/* → auth."""
    result = resolve_service("POST", "/api/v1/auth/token")
    assert result is not None
    assert result[0] == "auth"


def test_admin_prefix_goes_to_auth():
    """ALL_METHODS /api/v1/admin/* → auth."""
    result = resolve_service("GET", "/api/v1/admin/users")
    assert result is not None
    assert result[0] == "auth"


def test_chat_prefix_goes_to_query():
    """ALL_METHODS /api/v1/chat/* → query."""
    result = resolve_service("POST", "/api/v1/chat/sessions")
    assert result is not None
    assert result[0] == "query"


def test_text_prefix_goes_to_query():
    """ALL_METHODS /api/v1/text/* → query."""
    result = resolve_service("POST", "/api/v1/text/search")
    assert result is not None
    assert result[0] == "query"


def test_analyse_prefix_goes_to_analyse():
    """ALL_METHODS /api/v1/analyse/* → analyse."""
    result = resolve_service("GET", "/api/v1/analyse/check")
    assert result is not None
    assert result[0] == "analyse"


def test_rag_prefix_goes_to_rag_search_with_transform():
    """ALL_METHODS /api/v1/rag/* → rag_search c transform /api/v1/..."""
    result = resolve_service("GET", "/api/v1/rag/search")
    assert result is not None
    svc, target = result
    assert svc == "rag_search"
    assert target == "/api/v1/search"


# ===================================================================
# Deprecated integration routes → None (410)
# ===================================================================


def test_deprecated_meridian_returns_none():
    """GET /api/v1/meridian/... → None (410)."""
    result = resolve_service("GET", "/api/v1/meridian/test")
    assert result is None


def test_deprecated_files_returns_none():
    """GET /api/v1/files/123 → None (410)."""
    result = resolve_service("GET", "/api/v1/files/123")
    assert result is None


def test_deprecated_external_returns_none():
    """GET /api/v1/external/sync → None (410)."""
    result = resolve_service("GET", "/api/v1/external/sync")
    assert result is None


# ===================================================================
# Нечисловой draft_id → None (400 INVALID_DRAFT_ID)
# ===================================================================


def test_non_numeric_draft_id_returns_none():
    """GET /api/v1/drafts/abc → None (400 INVALID_DRAFT_ID)."""
    result = resolve_service("GET", "/api/v1/drafts/abc")
    assert result is None


# ===================================================================
# Неизвестный путь → None (404)
# ===================================================================


def test_unknown_path_returns_none():
    """GET /api/v1/unknown/path → None (404)."""
    result = resolve_service("GET", "/api/v1/unknown/path")
    assert result is None


# ===================================================================
# Trailing slash — нормализация
# ===================================================================


def test_drafts_trailing_slash_goes_to_registry():
    """GET /api/v1/drafts/ → registry (нормализованный)."""
    result = resolve_service("GET", "/api/v1/drafts/")
    assert result is not None
    assert result[0] == "registry"


# ===================================================================
# Приоритет: специфичные правила перед общими
# ===================================================================


def test_specific_rule_before_generic():
    """GET /api/v1/drafts/123 → orchestrator (специфичный),
    а не registry (общий /api/v1/registry/* не должен перебивать)."""
    result = resolve_service("GET", "/api/v1/drafts/123")
    assert result is not None
    assert result[0] == "orchestrator", (
        "Специфичное правило /drafts/{id} должно иметь приоритет над registry/*"
    )


def test_registry_prefix_does_not_catch_drafts():
    """POST /api/v1/drafts → orchestrator, не registry."""
    result = resolve_service("POST", "/api/v1/drafts")
    assert result is not None
    assert result[0] == "orchestrator"


# ===================================================================
# is_deprecated_integration_route
# ===================================================================


def test_deprecated_integration_routes():
    """Проверка is_deprecated_integration_route()."""
    assert is_deprecated_integration_route("/api/v1/meridian/test") is True
    assert is_deprecated_integration_route("/api/v1/files/123") is True
    assert is_deprecated_integration_route("/api/v1/external/sync") is True
    assert is_deprecated_integration_route("/api/v1/documents/1") is False
    assert is_deprecated_integration_route("/api/v1/health") is False
