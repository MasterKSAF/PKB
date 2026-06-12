"""
Gateway Mock — тесты на 43 падающих эндпоинта (checker coverage 2026-06-12).

Каждый тест проверяет один эндпоинт из списка failures.
Цель: зафиксировать текущее состояние и документировать ожидаемое поведение.
Когда mock чинят — тест начинает проходить.

Используется TestClient напрямую, ALLOW_ANONYMOUS=True для упрощения.
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import uuid
import pytest
from fastapi.testclient import TestClient

import mocks.gateway

mocks.gateway.ALLOW_ANONYMOUS = True
from mocks.gateway import app

client = TestClient(app, raise_server_exceptions=False)

BASE = "/api/v1"
REG = f"{BASE}/registry"
ADMIN = f"{BASE}/admin"

# ── helpers ──────────────────────────────────────────────────────────────────


def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def admin_token():
    """Свежий токен администратора."""
    r = client.post(
        f"{BASE}/auth/token",
        json={"username": "admin@example.com", "password": "admin123"},
    )
    assert r.status_code == 200, f"Login failed: {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def engineer_token():
    """Токен инженера."""
    r = client.post(
        f"{BASE}/auth/token",
        json={"username": "ivanov@example.com", "password": "user123"},
    )
    assert r.status_code == 200, f"Login failed: {r.text[:200]}"
    return r.json()["access_token"]


# =====================================================================
# 1. AUTH
# =====================================================================

class TestAuthRevoke:
    """POST /auth/revoke → 200. Падает с 422, если нет refresh_token."""

    def test_revoke_valid_token(self, admin_token):
        """Шлём валидный refresh_token → 200."""
        # Сначала получим токен с refresh_token
        r = client.post(
            f"{BASE}/auth/token",
            json={"username": "admin@example.com", "password": "admin123"},
        )
        assert r.status_code == 200
        refresh = r.json()["refresh_token"]

        resp = client.post(
            f"{BASE}/auth/revoke",
            json={"refresh_token": refresh},
            headers=_auth_header(admin_token),
        )
        # Ожидаем 200. Сейчас 422 — модель RevokeRequest требует refresh_token.
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "message" in resp.json()

    def test_revoke_missing_token(self, admin_token):
        """Пустое тело → 200 (поля token/refresh_token необязательны с пустым default)."""
        resp = client.post(
            f"{BASE}/auth/revoke",
            json={},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_revoke_with_token_field(self, admin_token):
        """Поле token вместо refresh_token → 200."""
        resp = client.post(
            f"{BASE}/auth/revoke",
            json={"token": "rt-mock-nonexistent"},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "message" in resp.json()


# =====================================================================
# 2. CHAT: /chat POST
# =====================================================================

class TestChatAsk:
    """POST /chat → 200. Модель ChatRequest требует question."""

    def test_chat_ask_with_question(self):
        """С полем question → 200."""
        resp = client.post(
            f"{BASE}/chat",
            json={"question": "Какой материал используется?"},
        )
        # Ожидаем 200. Сейчас 422 — если что-то не так с моделью.
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        assert "scenario" in body

    def test_chat_ask_empty(self):
        """Без обязательного поля question → 422."""
        resp = client.post(f"{BASE}/chat", json={})
        assert resp.status_code == 422


# =====================================================================
# 3. CHAT: Projects CRUD
# =====================================================================

class TestChatProjects:
    """POST/GET/PUT/DELETE /chat/projects — проверяем, что проекты работают."""

    PROJECT_ID = None

    def test_1_create_project(self):
        """POST /chat/projects → 201. Модель: code, name, status."""
        resp = client.post(
            f"{BASE}/chat/projects",
            json={
                "code": f"TEST-{uuid.uuid4().hex[:4]}",
                "name": "Test Project",
                "status": "active",
            },
        )
        # Ожидаем 201. Сейчас 422 — если модель не проходит.
        assert resp.status_code == 201, (
            f"Expected 201, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        assert "project_id" in body
        TestChatProjects.PROJECT_ID = body["project_id"]

    def test_2_get_project(self):
        """GET /chat/projects/{id} → 200."""
        pid = TestChatProjects.PROJECT_ID
        if pid is None:
            pytest.skip("Нет project_id (предыдущий тест не прошёл)")
        resp = client.get(f"{BASE}/chat/projects/{pid}")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert resp.json()["project_id"] == pid

    def test_3_get_project_not_found(self):
        """GET /chat/projects/99999 → 404."""
        resp = client.get(f"{BASE}/chat/projects/99999")
        assert resp.status_code == 404

    def test_4_update_project(self):
        """PUT /chat/projects/{id} → 200."""
        pid = TestChatProjects.PROJECT_ID
        if pid is None:
            pytest.skip("Нет project_id")
        resp = client.put(
            f"{BASE}/chat/projects/{pid}",
            json={"name": "Updated Project", "status": "archived"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert resp.json()["name"] == "Updated Project"

    def test_5_update_project_not_found(self):
        """PUT /chat/projects/99999 → 404."""
        resp = client.put(
            f"{BASE}/chat/projects/99999",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404

    def test_6_delete_project(self):
        """DELETE /chat/projects/{id} → 204."""
        pid = TestChatProjects.PROJECT_ID
        if pid is None:
            pytest.skip("Нет project_id")
        resp = client.delete(f"{BASE}/chat/projects/{pid}")
        assert resp.status_code == 204, (
            f"Expected 204, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_7_delete_project_not_found(self):
        """DELETE /chat/projects/99999 → 404."""
        resp = client.delete(f"{BASE}/chat/projects/99999")
        assert resp.status_code == 404

    def test_8_list_projects(self):
        """GET /chat/projects → 200."""
        resp = client.get(f"{BASE}/chat/projects")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "meta" in body


# =====================================================================
# 4. CHAT: Session sub-resources (messages, context, export)
# =====================================================================

class TestChatSessionResources:
    """Sub-resources чат-сессии: messages, context, export.
    Падают с 404, если сессия не найдена или ресурс не реализован.
    """

    SESSION_ID = None

    def test_0_create_session(self):
        """Создаём сессию для тестов."""
        resp = client.post(
            f"{BASE}/chat/sessions",
            json={"title": "Test Session", "project_id": 1},
        )
        assert resp.status_code == 201
        TestChatSessionResources.SESSION_ID = resp.json()["session_id"]

    def test_1_send_message(self):
        """POST /chat/sessions/{id}/messages → 200."""
        sid = TestChatSessionResources.SESSION_ID
        if sid is None:
            pytest.skip("Нет session_id")
        # send_message ожидает SendMessageRequest
        resp = client.post(
            f"{BASE}/chat/sessions/{sid}/messages",
            json={"content": "Hello", "role": "user"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_2_list_messages(self):
        """GET /chat/sessions/{id}/messages → 200."""
        sid = TestChatSessionResources.SESSION_ID
        if sid is None:
            pytest.skip("Нет session_id")
        resp = client.get(f"{BASE}/chat/sessions/{sid}/messages")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "messages" in resp.json()

    def test_3_get_last_message(self):
        """GET /chat/sessions/{id}/messages/last → 200."""
        sid = TestChatSessionResources.SESSION_ID
        if sid is None:
            pytest.skip("Нет session_id")
        resp = client.get(f"{BASE}/chat/sessions/{sid}/messages/last")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_4_get_message_by_id(self):
        """GET /chat/sessions/{id}/messages/{msg_id} → 200."""
        sid = TestChatSessionResources.SESSION_ID
        if sid is None:
            pytest.skip("Нет session_id")
        # Сначала отправим сообщение, чтобы получить его id
        r = client.post(
            f"{BASE}/chat/sessions/{sid}/messages",
            json={"content": "Test", "role": "user"},
        )
        assert r.status_code == 200
        msg_id = r.json().get("message_id")
        if not msg_id:
            pytest.skip("Нет message_id в ответе")
        resp = client.get(f"{BASE}/chat/sessions/{sid}/messages/{msg_id}")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_5_manage_context(self):
        """POST /chat/sessions/{id}/context → 200."""
        sid = TestChatSessionResources.SESSION_ID
        if sid is None:
            pytest.skip("Нет session_id")
        resp = client.post(
            f"{BASE}/chat/sessions/{sid}/context",
            json={"action": "add", "document_ids": [1]},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_6_export_session(self):
        """POST /chat/sessions/{id}/export → 200."""
        sid = TestChatSessionResources.SESSION_ID
        if sid is None:
            pytest.skip("Нет session_id")
        resp = client.post(
            f"{BASE}/chat/sessions/{sid}/export",
            json={"format": "pdf"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )


# =====================================================================
# 5. REGISTRY: Classifiers import
# =====================================================================

class TestRegistryClassifiersImport:
    """POST /registry/classifiers/import → 200."""

    def test_import_classifiers(self):
        """POST /registry/classifiers/import с массивом → 200."""
        resp = client.post(
            f"{REG}/classifiers/import",
            json=[
                {"classifier_system": "MKS", "code": "IMP.TEST", "full_name": "Import Test"}
            ],
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "data" in resp.json()


# =====================================================================
# 6. REGISTRY: Documents sub-endpoints
# =====================================================================

class TestRegistryDocSubEndpoints:
    """Подресурсы registry documents: status, history, succession, sections."""

    DOC_ID = None

    def test_0_create_doc(self):
        """Создаём документ для тестов."""
        resp = client.post(
            f"{REG}/documents",
            json={
                "title": "Sub-resource Test Doc",
                "doc_code": f"SUB-{uuid.uuid4().hex[:4]}",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        # registry возвращает {"data": {"id": ...}}
        data = body.get("data", {})
        TestRegistryDocSubEndpoints.DOC_ID = data.get("id") or body.get("data", {}).get("document_id")

    def test_1_patch_status(self):
        """PATCH /registry/documents/{id}/status → 200."""
        doc_id = TestRegistryDocSubEndpoints.DOC_ID
        if doc_id is None:
            pytest.skip("Нет doc_id")
        resp = client.patch(
            f"{REG}/documents/{doc_id}/status",
            json={"status": "approved"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_2_doc_history(self):
        """GET /registry/documents/{id}/history → 200."""
        doc_id = TestRegistryDocSubEndpoints.DOC_ID
        if doc_id is None:
            pytest.skip("Нет doc_id")
        resp = client.get(f"{REG}/documents/{doc_id}/history")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "data" in resp.json() or "history" in resp.json()

    def test_3_doc_succession(self):
        """GET /registry/documents/{id}/succession → 200."""
        doc_id = TestRegistryDocSubEndpoints.DOC_ID
        if doc_id is None:
            pytest.skip("Нет doc_id")
        resp = client.get(f"{REG}/documents/{doc_id}/succession")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_4_doc_sections(self):
        """GET /registry/documents/{id}/sections → 200."""
        doc_id = TestRegistryDocSubEndpoints.DOC_ID
        if doc_id is None:
            pytest.skip("Нет doc_id")
        resp = client.get(f"{REG}/documents/{doc_id}/sections")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )


# =====================================================================
# 7. REGISTRY: Documents import & check-uniqueness
# =====================================================================

class TestRegistryDocImportUniqueness:
    """POST /registry/documents/import и /check-uniqueness → 200."""

    def test_1_import_docs(self):
        """POST /registry/documents/import с массивом → 200."""
        resp = client.post(
            f"{REG}/documents/import",
            json=[
                {"title": "Imported Doc", "doc_code": "IMP-DOC"}
            ],
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "data" in resp.json()

    def test_2_check_uniqueness(self):
        """POST /registry/documents/check-uniqueness → 200."""
        resp = client.post(
            f"{REG}/documents/check-uniqueness",
            json={"title": "Unique Doc", "doc_code": "UNIQUE-001"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )


# =====================================================================
# 8. REGISTRY: Drafts
# =====================================================================

class TestRegistryDrafts:
    """POST/GET/DELETE/PATCH /registry/drafts."""

    DRAFT_ID = None

    def test_1_create_draft(self):
        """POST /registry/drafts → 201."""
        resp = client.post(
            f"{REG}/drafts",
            json={
                "file_key": "test-file.pdf",
                "document_key": f"DRF-{uuid.uuid4().hex[:4]}",
            },
        )
        assert resp.status_code == 201, (
            f"Expected 201, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        # registry возвращает {"data": {"id": ...}}
        data = body.get("data", {})
        TestRegistryDrafts.DRAFT_ID = data.get("id")

    def test_2_list_drafts(self):
        """GET /registry/drafts → 200."""
        resp = client.get(f"{REG}/drafts")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "data" in resp.json() or "drafts" in resp.json()

    def test_3_get_draft(self):
        """GET /registry/drafts/{id} → 200."""
        did = TestRegistryDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.get(f"{REG}/drafts/{did}")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_4_get_draft_preview(self):
        """GET /registry/drafts/{id}/preview → 200."""
        did = TestRegistryDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.get(f"{REG}/drafts/{did}/preview")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_5_patch_draft_status(self):
        """PATCH /registry/drafts/{id}/status → 200."""
        did = TestRegistryDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.patch(
            f"{REG}/drafts/{did}/status",
            json={"status": "approved"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_6_delete_draft(self):
        """DELETE /registry/drafts/{id} → 200/204."""
        did = TestRegistryDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.delete(f"{REG}/drafts/{did}")
        assert resp.status_code in (200, 204), (
            f"Expected 200/204, got {resp.status_code}: {resp.text[:200]}"
        )


# =====================================================================
# 9. TERMINOLOGY: Import
# =====================================================================

class TestTerminologyImport:
    """POST /registry/terminology/import → 200."""

    def test_import_terms(self):
        """POST /registry/terminology/import с массивом → 200."""
        resp = client.post(
            f"{REG}/terminology/import",
            json=[
                {"raw_term": "Test Term", "definition": "Test definition", "term_type": "preferred"}
            ],
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "data" in resp.json()


# =====================================================================
# 10. ADMIN: Roles create
# =====================================================================

class TestAdminCreateRole:
    """POST /admin/roles → 201."""

    def test_create_role(self, admin_token):
        """POST /admin/roles с name + permissions → 201."""
        resp = client.post(
            f"{ADMIN}/roles",
            json={"name": "Test Role", "permissions": ["test:read"]},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 201, (
            f"Expected 201, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        assert "role_id" in body
        assert body["name"] == "Test Role"

    def test_create_role_missing_name(self, admin_token):
        """POST /admin/roles без name → 422."""
        resp = client.post(
            f"{ADMIN}/roles",
            json={"permissions": []},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 422


# =====================================================================
# 11. DOCUMENTS: Add version
# =====================================================================

class TestDocumentAddVersion:
    """POST /documents/{id}/versions → 202 (ожидает UploadFile)."""

    def test_add_version(self):
        """POST /documents/{id}/versions с файлом → 202."""
        resp = client.post(
            f"{BASE}/documents/1/versions",
            files={"file": ("test.pdf", b"pdf content", "application/pdf")},
        )
        assert resp.status_code == 202, (
            f"Expected 202, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        assert "version_id" in body or "id" in body


# =====================================================================
# 12. DOCUMENTS: Search GET
# =====================================================================

class TestDocumentSearch:
    """GET /documents/search → 200."""

    def test_search_with_q(self):
        """GET /documents/search?q=test → 200."""
        resp = client.get(
            f"{BASE}/documents/search",
            params={"q": "test"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_search_without_q(self):
        """GET /documents/search без q → 200 (параметр необязателен, пустой результат)."""
        resp = client.get(f"{BASE}/documents/search")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total_found"] == 0


# =====================================================================
# 13. TASKS: Task status
# =====================================================================

class TestTaskStatus:
    """GET /tasks/{task_id}/status → 200.
    POST /documents возвращает task_id, но НЕ создаёт задачу в _tasks.
    POST /drafts — создаёт и draft, и task. Используем его.
    """

    TASK_ID = None

    def test_0_create_draft_with_task(self):
        """Создаём draft, который создаст и task."""
        resp = client.post(
            f"{BASE}/drafts",
            json={"file_key": "task-test.pdf", "document_key": "task-doc-001"},
        )
        assert resp.status_code == 202
        body = resp.json()
        TestTaskStatus.TASK_ID = body.get("task_id")
        assert TestTaskStatus.TASK_ID is not None, f"No task_id in response: {body}"

    def test_1_get_task_status(self):
        """GET /tasks/{task_id}/status → 200."""
        tid = TestTaskStatus.TASK_ID
        if tid is None:
            pytest.skip("Нет task_id")
        resp = client.get(f"{BASE}/tasks/{tid}/status")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "status" in resp.json()
        assert resp.json()["task_id"] == tid

    def test_2_get_task_status_not_found(self):
        """GET /tasks/99999/status → 404."""
        resp = client.get(f"{BASE}/tasks/99999/status")
        assert resp.status_code == 404


# =====================================================================
# 14. DRAFTS (orchestrator-style)
# =====================================================================

class TestOrchestratorDrafts:
    """POST/GET/DELETE/PATCH /drafts — orchestrator-style."""

    DRAFT_ID = None

    def test_1_create_draft(self):
        """POST /drafts → 202."""
        resp = client.post(
            f"{BASE}/drafts",
            json={"file_key": "test.pdf", "document_key": "doc-002"},
        )
        assert resp.status_code == 202, (
            f"Expected 202, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        TestOrchestratorDrafts.DRAFT_ID = body.get("draft_id") or body.get("id")

    def test_2_list_drafts(self):
        """GET /drafts → 200. Требует query-параметр document_key."""
        resp = client.get(
            f"{BASE}/drafts",
            params={"document_key": "doc-002"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert "items" in resp.json() or "data" in resp.json()

    def test_3_get_draft(self):
        """GET /drafts/{id} → 200."""
        did = TestOrchestratorDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.get(f"{BASE}/drafts/{did}")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_4_start_preview(self):
        """POST /drafts/{id}/preview → 202 (запуск preview, статус → previewing)."""
        did = TestOrchestratorDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.post(f"{BASE}/drafts/{did}/preview")
        # start_draft_preview возвращает 202, статус "previewing"
        assert resp.status_code == 202, (
            f"Expected 202, got {resp.status_code}: {resp.text[:200]}"
        )
        assert resp.json()["status"] == "previewing"

    def test_5_poll_preview_status(self):
        """GET /drafts/{id}/preview/status → 200 (меняет статус на ready_for_approve)."""
        did = TestOrchestratorDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.get(f"{BASE}/drafts/{did}/preview/status")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert resp.json()["status"] == "ready_for_approve"

    def test_6_decide_draft(self):
        """PATCH /drafts/{id}/decide → 200.
        Должен быть ДО delete, т.к. delete меняет статус на discarded."""
        did = TestOrchestratorDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.patch(
            f"{BASE}/drafts/{did}/decide",
            json={"action": "approve"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        assert resp.json()["status"] == "approved"

    def test_7_get_draft_preview(self):
        """GET /drafts/{id}/preview → 200."""
        did = TestOrchestratorDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.get(f"{BASE}/drafts/{did}/preview")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_8_delete_draft(self):
        """DELETE /drafts/{id} → 200/204."""
        did = TestOrchestratorDrafts.DRAFT_ID
        if did is None:
            pytest.skip("Нет draft_id")
        resp = client.delete(f"{BASE}/drafts/{did}")
        assert resp.status_code in (200, 204), (
            f"Expected 200/204, got {resp.status_code}: {resp.text[:200]}"
        )


# =====================================================================
# 15. TEXT: search and ask
# =====================================================================

class TestTextEndpoints:
    """POST /text/search и /text/ask → 200."""

    def test_text_search(self):
        """POST /text/search с текстом → 200."""
        resp = client.post(
            f"{BASE}/text/search",
            json={"text": "толщина стенки"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        assert "results" in body
        assert "total_found" in body

    def test_text_ask(self):
        """POST /text/ask с вопросом → 200."""
        resp = client.post(
            f"{BASE}/text/ask",
            json={"text": "Какая толщина стенки?"},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        assert "answer" in body
        assert "sources" in body

    def test_text_search_empty(self):
        """POST /text/search с пустым текстом → 200 (модель не валидирует empty)."""
        resp = client.post(
            f"{BASE}/text/search",
            json={"text": ""},
        )
        # Модель SearchRequest не валидирует text на не-пустоту
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_text_ask_empty(self):
        """POST /text/ask с пустым текстом → 200 (модель не валидирует empty)."""
        resp = client.post(
            f"{BASE}/text/ask",
            json={"text": ""},
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )


# =====================================================================
# 16. ORCHESTRATOR: document get (schema validation)
# =====================================================================

class TestOrchestratorGetDocument:
    """GET /documents/{id} — проверка обязательных полей."""

    def test_get_document_has_id_field(self):
        """GET /documents/1 → 200 + поле 'id'."""
        resp = client.get(f"{BASE}/documents/1")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        body = resp.json()
        # Поле 'id' или 'document_id' обязательно
        assert "id" in body or "document_id" in body, (
            f"Missing 'id' field in response: {body}"
        )


# =====================================================================
# 17. REGISTRY: duplicate classifier (409 — ожидаемо)
# =====================================================================

class TestRegistryClassifierDuplicate:
    """POST /registry/classifiers (duplicate) → 409."""

    def test_create_duplicate_classifier(self):
        """Создаём классификатор, потом такой же → 409."""
        code = f"DUP-{uuid.uuid4().hex[:4]}"
        # Первый — 201
        r1 = client.post(
            f"{REG}/classifiers",
            json={"classifier_system": "MKS", "code": code, "full_name": "First"},
        )
        assert r1.status_code == 201

        # Второй (дубликат) — 409
        r2 = client.post(
            f"{REG}/classifiers",
            json={"classifier_system": "MKS", "code": code, "full_name": "Second"},
        )
        assert r2.status_code == 409, (
            f"Expected 409 for duplicate, got {r2.status_code}: {r2.text[:200]}"
        )
        body = r2.json()
        # Должен быть error-формат
        assert "error" in body or "detail" in body


# =====================================================================
# 18. REGISTRY: Categories CRUD
# =====================================================================

class TestRegistryCategories:
    """CRUD для /registry/categories."""

    CAT_ID = None

    def test_1_list_categories(self):
        """GET /registry/categories → 200."""
        resp = client.get(f"{REG}/categories")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body

    def test_2_create_category(self):
        """POST /registry/categories → 201."""
        resp = client.post(
            f"{REG}/categories",
            json={"name": "Test Category", "description": "Test desc", "color": "#FF0000"},
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text[:200]}"
        body = resp.json()
        data = body.get("data", {})
        TestRegistryCategories.CAT_ID = data.get("id")
        assert data["name"] == "Test Category"
        assert data["color"] == "#FF0000"

    def test_3_duplicate_name(self):
        """POST /registry/categories с существующим именем → 409."""
        resp = client.post(
            f"{REG}/categories",
            json={"name": "Test Category"},
        )
        assert resp.status_code == 409

    def test_4_get_category(self):
        """GET /registry/categories/{id} → 200."""
        cid = TestRegistryCategories.CAT_ID
        if cid is None:
            pytest.skip("Нет category_id")
        resp = client.get(f"{REG}/categories/{cid}")
        assert resp.status_code == 200
        data = resp.json().get("data", {})
        assert data["id"] == cid

    def test_5_get_category_not_found(self):
        """GET /registry/categories/99999 → 404."""
        resp = client.get(f"{REG}/categories/99999")
        assert resp.status_code == 404

    def test_6_update_category(self):
        """PUT /registry/categories/{id} → 200."""
        cid = TestRegistryCategories.CAT_ID
        if cid is None:
            pytest.skip("Нет category_id")
        resp = client.put(
            f"{REG}/categories/{cid}",
            json={"name": "Updated Category", "color": "#00FF00"},
        )
        assert resp.status_code == 200
        data = resp.json().get("data", {})
        assert data["name"] == "Updated Category"
        assert data["color"] == "#00FF00"

    def test_7_delete_category(self):
        """DELETE /registry/categories/{id} → 200."""
        cid = TestRegistryCategories.CAT_ID
        if cid is None:
            pytest.skip("Нет category_id")
        resp = client.delete(f"{REG}/categories/{cid}")
        assert resp.status_code == 200
        data = resp.json().get("data", {})
        assert data["id"] == cid

    def test_8_delete_not_found(self):
        """DELETE /registry/categories/99999 → 404."""
        resp = client.delete(f"{REG}/categories/99999")
        assert resp.status_code == 404

    def test_9_seed_categories_exist(self):
        """Проверяем, что seed-категории загружены."""
        resp = client.get(f"{REG}/categories")
        assert resp.status_code == 200
        data = resp.json().get("data", [])
        names = [c["name"] for c in data]
        assert "Корпусные конструкции" in names
        assert "Электрооборудование" in names
        assert "Материалы" in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
