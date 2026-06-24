"""
Tests for Documents API endpoints.

В оркестраторе остались:
- `POST /api/v1/documents/{doc_id}/reprocess` (P2I-9, pipeline-операция переиндексации)
- `GET /api/v1/documents/{doc_id}/tasks` — список pipeline-задач документа

Все остальные GET /documents/*, POST /documents/{id}/versions, POST /documents/{id}/approve,
DELETE /documents/{id} перенесены в registry-service
(см. docs/api/registry_service_api.md, группа documents).
"""

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
#  POST /api/v1/documents/{doc_id}/reprocess
# ---------------------------------------------------------------------------


class TestDocumentReprocess:
    """Tests for POST /api/v1/documents/{doc_id}/reprocess."""

    REPROCESS_URL = "/api/v1/documents/{doc_id}/reprocess"

    def test_reprocess_full_mode(self, client: TestClient, auth_header: dict):
        """Reprocess with mode=full returns 202."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "full"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_reprocess_ocr_only(self, client: TestClient, auth_header: dict):
        """Reprocess with mode=ocr_only returns 202."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "ocr_only"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_reprocess_invalid_mode(self, client: TestClient, auth_header: dict):
        """Reprocess with invalid mode returns 422."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "invalid"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_reprocess_response_structure(self, client: TestClient, auth_header: dict):
        """Response has mode, document_id, task_id, status, created_at."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "full"},
            headers=auth_header,
        )
        data = response.json()
        assert "mode" in data
        assert "document_id" in data
        assert "task_id" in data
        assert "status" in data
        assert "created_at" in data
        assert data["document_id"] == "doc-test-001"
        assert data["mode"] == "full"
        assert isinstance(data["task_id"], str)
        assert isinstance(data["status"], str)

    def test_reprocess_without_auth(self, client: TestClient):
        """Reprocess works in mock mode (mock auth always returns mock user)."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "full"},
        )
        assert response.status_code == 202


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/tasks
# ---------------------------------------------------------------------------


class TestDocumentTasks:
    """Tests for GET /api/v1/documents/{doc_id}/tasks."""

    TASKS_URL = "/api/v1/documents/{doc_id}/tasks"

    def test_document_tasks_success(self, client: TestClient, auth_header: dict):
        """Returns document tasks list with expected structure."""
        response = client.get(
            self.TASKS_URL.format(doc_id=1),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert "tasks" in data
        assert data["document_id"] == 1
        assert isinstance(data["tasks"], list)

    def test_document_tasks_without_auth(self, client: TestClient):
        """Returns 200 in mock mode."""
        response = client.get(
            self.TASKS_URL.format(doc_id=1),
        )
        assert response.status_code == 200
