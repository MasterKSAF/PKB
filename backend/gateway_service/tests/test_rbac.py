"""
Тесты RBACMiddleware — безопасность (CM-1).

Все тесты используют mock_auth_validate для изоляции от реального Auth Service.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


BASE = "/api/v1"


class TestRBACNoAuth:
    """Запросы без аутентификации (ALLOW_ANONYMOUS=True — пропускаются до прокси)."""

    def test_no_auth_passes_through_middleware(self, client):
        """Без Authorization header — запрос проходит middleware (не 401/403)."""
        resp = client.post(f"{BASE}/drafts", json={"title": "test"})
        assert resp.status_code not in (401, 403), f"Unexpected {resp.status_code}"

    def test_health_public(self, client):
        """GET /api/v1/health без токена → 200 (публичный)."""
        resp = client.get(f"{BASE}/health")
        assert resp.status_code == 200

    def test_auth_token_public(self, client):
        """POST /api/v1/auth/token без токена → проходит middleware (не 403)."""
        resp = client.post(
            f"{BASE}/auth/token",
            json={"username": "admin", "password": "admin123"},
        )
        assert resp.status_code not in (403,), f"Unexpected {resp.status_code}"


class TestRBACAdminAccess:
    """Доступ к /api/v1/admin/*."""

    def test_admin_get_system_admin_allowed(self, client, mock_auth_validate, system_admin_user):
        """GET /api/v1/admin/* для system_admin — middleware не блокирует."""
        mock_auth_validate(system_admin_user)
        resp = client.get(
            f"{BASE}/admin/users",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code != 403, f"RBAC blocked admin access: {resp.status_code}"

    def test_admin_get_engineer_forbidden(self, client, mock_auth_validate, engineer_user):
        """GET /api/v1/admin/* для engineer → 403."""
        mock_auth_validate(engineer_user)
        resp = client.get(
            f"{BASE}/admin/users",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403

    def test_admin_post_engineer_forbidden(self, client, mock_auth_validate, engineer_user):
        """POST /api/v1/admin/* для engineer → 403."""
        mock_auth_validate(engineer_user)
        resp = client.post(
            f"{BASE}/admin/users",
            json={},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACDraftPermissions:
    """Права на создание черновиков."""

    def test_post_draft_with_permission_allowed(self, client, mock_auth_validate, knowledge_admin_user):
        """POST /api/v1/drafts c can_upload_documents=true → 200/202 (прокси)."""
        mock_auth_validate(knowledge_admin_user)
        resp = client.post(
            f"{BASE}/drafts",
            json={"title": "test"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code not in (401, 403)

    def test_post_draft_without_permission_forbidden(self, client, mock_auth_validate, engineer_user):
        """POST /api/v1/drafts c can_upload_documents=false → 403."""
        mock_auth_validate(engineer_user)
        resp = client.post(
            f"{BASE}/drafts",
            json={"title": "test"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACClassifiers:
    """Права на управление классификаторами."""

    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
    def test_classifiers_with_permission_allowed(self, method, client, mock_auth_validate, system_admin_user):
        """POST/PUT/DELETE /api/v1/registry/classifiers c правом → не 403."""
        mock_auth_validate(system_admin_user)
        resp = client.request(
            method,
            f"{BASE}/registry/classifiers",
            json={"code": "TEST"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code not in (401, 403)

    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
    def test_classifiers_without_permission_forbidden(self, method, client, mock_auth_validate, engineer_user):
        """POST/PUT/DELETE /registry/classifiers без права → 403."""
        mock_auth_validate(engineer_user)
        resp = client.request(
            method,
            f"{BASE}/registry/classifiers",
            json={"code": "TEST"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACTerminology:
    """Права на управление терминологией."""

    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
    def test_terminology_with_permission_allowed(self, method, client, mock_auth_validate, system_admin_user):
        """POST/PUT/DELETE /api/v1/registry/terminology c правом → не 403."""
        mock_auth_validate(system_admin_user)
        resp = client.request(
            method,
            f"{BASE}/registry/terminology",
            json={"term": "test"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code not in (401, 403)

    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
    def test_terminology_without_permission_forbidden(self, method, client, mock_auth_validate, engineer_user):
        """POST/PUT/DELETE /registry/terminology без права → 403."""
        mock_auth_validate(engineer_user)
        resp = client.request(
            method,
            f"{BASE}/registry/terminology",
            json={"term": "test"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACRegistryDocuments:
    """Права на управление реестром документов."""

    @pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
    def test_registry_documents_with_permission_allowed(self, method, client, mock_auth_validate, system_admin_user):
        """POST/PUT/PATCH /api/v1/registry/documents c правом → не 403."""
        mock_auth_validate(system_admin_user)
        resp = client.request(
            method,
            f"{BASE}/registry/documents",
            json={"title": "test"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code not in (401, 403)

    @pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
    def test_registry_documents_without_permission_forbidden(self, method, client, mock_auth_validate, engineer_user):
        """POST/PUT/PATCH /registry/documents без права → 403."""
        mock_auth_validate(engineer_user)
        resp = client.request(
            method,
            f"{BASE}/registry/documents",
            json={"title": "test"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACDeleteDocument:
    """Права на удаление документов."""

    def test_delete_document_with_permission(self, client, mock_auth_validate, system_admin_user):
        """DELETE /api/v1/documents/1 c правом → не 403."""
        mock_auth_validate(system_admin_user)
        resp = client.delete(
            f"{BASE}/documents/1",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code not in (401, 403)

    def test_delete_document_without_permission(self, client, mock_auth_validate, engineer_user):
        """DELETE /api/v1/documents/1 без права → 403."""
        mock_auth_validate(engineer_user)
        resp = client.delete(
            f"{BASE}/documents/1",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACDeleteDraft:
    """Права на удаление черновиков."""

    def test_delete_draft_with_permission(self, client, mock_auth_validate, system_admin_user):
        """DELETE /api/v1/drafts/1 c правом → не 403."""
        mock_auth_validate(system_admin_user)
        resp = client.delete(
            f"{BASE}/drafts/1",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code not in (401, 403)

    def test_delete_draft_without_permission(self, client, mock_auth_validate, engineer_user):
        """DELETE /api/v1/drafts/1 без права → 403."""
        mock_auth_validate(engineer_user)
        resp = client.delete(
            f"{BASE}/drafts/1",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACReprocess:
    """Права на переобработку документов."""

    def test_reprocess_with_permission(self, client, mock_auth_validate, system_admin_user):
        """POST /api/v1/documents/1/reprocess c правом → не 403."""
        mock_auth_validate(system_admin_user)
        resp = client.post(
            f"{BASE}/documents/1/reprocess",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code not in (401, 403)

    def test_reprocess_without_permission(self, client, mock_auth_validate, engineer_user):
        """POST /api/v1/documents/1/reprocess без права → 403."""
        mock_auth_validate(engineer_user)
        resp = client.post(
            f"{BASE}/documents/1/reprocess",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACMetrics:
    """Доступ к метрикам."""

    def test_metrics_system_admin_allowed(self, client, mock_auth_validate, system_admin_user):
        """GET /api/v1/monitor/metrics для system_admin → 200."""
        mock_auth_validate(system_admin_user)
        resp = client.get(
            f"{BASE}/monitor/metrics",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code in (200, 502)

    def test_metrics_engineer_forbidden(self, client, mock_auth_validate, engineer_user):
        """GET /api/v1/monitor/metrics для engineer → 403."""
        mock_auth_validate(engineer_user)
        resp = client.get(
            f"{BASE}/monitor/metrics",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403


class TestRBACSearch:
    """Доступ к поиску по реестру."""

    def test_search_knowledge_admin_allowed(self, client, mock_auth_validate, knowledge_admin_user):
        """GET /api/v1/registry/search для knowledge_admin → не 403."""
        mock_auth_validate(knowledge_admin_user)
        resp = client.get(
            f"{BASE}/registry/search?q=test",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code not in (401, 403)

    def test_search_engineer_forbidden(self, client, mock_auth_validate, engineer_user):
        """GET /api/v1/registry/search для engineer → 403."""
        mock_auth_validate(engineer_user)
        resp = client.get(
            f"{BASE}/registry/search?q=test",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403
