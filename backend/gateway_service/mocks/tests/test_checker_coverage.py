"""
Checker-coverage tests — эмулирует запросы внешнего checker'а.

Проверяет, что mock-сервисы отвечают так, как checker ожидает.
Каждый тест — один эндпоинт из списка 47 failures.
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import uuid
import pytest
from fastapi.testclient import TestClient

from mocks.common import _rate_limits

# Сбросим rate limiter перед тестами
_rate_limits.clear()

import mocks.gateway

mocks.gateway.ALLOW_ANONYMOUS = True
from mocks.gateway import app

client = TestClient(app, raise_server_exceptions=False)

BASE = "/api/v1"
REG = f"{BASE}/registry"
ADMIN = f"{BASE}/admin"


# ── helpers ──────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_token():
    """Свежий токен администратора."""
    _rate_limits.clear()
    r = client.post(
        f"{BASE}/auth/token",
        json={"username": "admin@example.com", "password": "admin123"},
    )
    assert r.status_code == 200, f"Login failed: {r.text[:200]}"
    return r.json()["access_token"]


def auth_h(token):
    return {"Authorization": f"Bearer {token}"}


def assert_200(resp, msg=""):
    assert resp.status_code == 200, f"{msg} Expected 200, got {resp.status_code}: {resp.text[:200]}"


def assert_201(resp, msg=""):
    assert resp.status_code == 201, f"{msg} Expected 201, got {resp.status_code}: {resp.text[:200]}"


# ===========================================================================
# 1. admin/roles POST
# ===========================================================================

class TestAdminRoles:
    """POST /admin/roles — checker шлёт создание роли."""

    def test_create_role(self, admin_token):
        """POST /admin/roles → 201."""
        resp = client.post(
            f"{ADMIN}/roles",
            json={"name": "Test Role", "permissions": ["test:read"]},
            headers=auth_h(admin_token),
        )
        assert_201(resp, "create_role")
        body = resp.json()
        assert "role_id" in body, f"Missing role_id: {body}"
        assert body.get("name") == "Test Role"


# ===========================================================================
# 2. admin/users POST
# ===========================================================================

class TestAdminUsers:
    """POST /admin/users — checker создаёт пользователя и ждёт id."""

    def test_create_user_has_id(self, admin_token):
        """POST /admin/users → 201 + id в ответе."""
        unique = uuid.uuid4().hex[:6]
        resp = client.post(
            f"{ADMIN}/users",
            json={
                "email": f"test.{unique}@example.com",
                "full_name": f"Test User {unique}",
                "password": "test123",
                "roles": ["engineer"],
            },
            headers=auth_h(admin_token),
        )
        assert_201(resp, "create_user")
        body = resp.json()
        assert "id" in body or "user_id" in body, f"No id field: {body}"
        if "id" in body:
            assert body["id"] is not None
        if "user_id" in body:
            assert body["user_id"] is not None


# ===========================================================================
# 3. chat/projects POST
# ===========================================================================

class TestChatProjects:
    """POST /chat/projects — checker создаёт проект."""

    def test_create_project(self, admin_token):
        """POST /chat/projects → 201."""
        resp = client.post(
            f"{BASE}/chat/projects",
            json={
                "code": f"PRJ-{uuid.uuid4().hex[:4]}",
                "name": "Test Project",
                "description": "Test description",
                "status": "active",
            },
            headers=auth_h(admin_token),
        )
        assert resp.status_code in (200, 201), (
            f"Expected 200/201, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        assert "project_id" in body, f"Missing project_id: {body}"


# ===========================================================================
# 4. chat/sessions/{id}/context/export
# ===========================================================================

class TestChatSessionContextExport:
    """POST /chat/sessions/{id}/context/export — экспорт контекста."""

    def test_context_export(self, admin_token):
        """POST /chat/sessions/1/context/export → 200."""
        resp = client.post(
            f"{BASE}/chat/sessions/1/context/export",
            json={"format": "pdf"},
            headers=auth_h(admin_token),
        )
        assert resp.status_code != 404, f"Endpoint not implemented: {resp.text[:200]}"
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text[:200]}"


# ===========================================================================
# 5. orchestrator documents
# ===========================================================================

class TestOrchestratorDocuments:
    """GET /documents/{doc_id} — checker создаёт doc в registry и ищет в orchestrator."""

    def test_get_document_with_auth(self, admin_token):
        """GET /documents/1 с токеном → 200."""
        resp = client.get(f"{BASE}/documents/1", headers=auth_h(admin_token))
        assert_200(resp, "get_document")

    def test_get_document_unknown_id(self, admin_token):
        """GET /documents/999 — несуществующий ID, mock создаёт авто-заглушку → 200."""
        resp = client.get(f"{BASE}/documents/999", headers=auth_h(admin_token))
        assert_200(resp, "get_document_unknown")


# ===========================================================================
# 6. registry history, succession, sections
# ===========================================================================

class TestRegistryDocSubEndpoints:
    """history, succession, sections для registry docs."""

    def test_doc_history(self, admin_token):
        """GET /registry/documents/1/history → 200."""
        resp = client.get(f"{REG}/documents/1/history", headers=auth_h(admin_token))
        assert_200(resp, "doc_history")

    def test_doc_succession(self, admin_token):
        """GET /registry/documents/1/succession → 200."""
        resp = client.get(f"{REG}/documents/1/succession", headers=auth_h(admin_token))
        assert_200(resp, "doc_succession")

    def test_doc_sections(self, admin_token):
        """GET /registry/documents/1/sections → 200."""
        resp = client.get(f"{REG}/documents/1/sections", headers=auth_h(admin_token))
        assert_200(resp, "doc_sections")


# ===========================================================================
# 7. drafts POST
# ===========================================================================

class TestDrafts:
    """POST /drafts — checker шлёт JSON, mock ждёт файл."""

    def test_drafts_json_fallback(self, admin_token):
        """POST /drafts с JSON-телом → 202 (fallback)."""
        resp = client.post(
            f"{BASE}/drafts",
            json={"file_key": "test.pdf", "document_key": "doc-001"},
            headers=auth_h(admin_token),
        )
        assert resp.status_code == 202, (
            f"Expected 202, got {resp.status_code}: {resp.text[:200]}"
        )


# ===========================================================================
# 8. search GET
# ===========================================================================

class TestSearch:
    """GET /documents/search — c q параметром."""

    def test_search_with_q(self, admin_token):
        """GET /documents/search?q=test → 200."""
        resp = client.get(
            f"{BASE}/documents/search",
            params={"q": "test"},
            headers=auth_h(admin_token),
        )
        assert_200(resp, "search_with_q")


# ===========================================================================
# 9. registry documents import, check-uniqueness
# ===========================================================================

class TestRegistryImportUnique:
    """POST /registry/documents/import, POST /registry/documents/check-uniqueness."""

    def test_import_docs(self, admin_token):
        """POST /registry/documents/import → 200."""
        resp = client.post(
            f"{REG}/documents/import",
            json=[{"title": "Test Doc", "doc_code": "TEST-001"}],
            headers=auth_h(admin_token),
        )
        assert_200(resp, "import_docs")
        body = resp.json()
        assert "data" in body

    def test_check_uniqueness(self, admin_token):
        """POST /registry/documents/check-uniqueness → 200."""
        resp = client.post(
            f"{REG}/documents/check-uniqueness",
            json={"title": "Test Doc", "doc_code": "TEST-001"},
            headers=auth_h(admin_token),
        )
        assert_200(resp, "check_uniqueness")
        body = resp.json()
        assert "data" in body
