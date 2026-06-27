"""
Tests for Documents API endpoints.

В оркестраторе остались:
- `POST /api/v1/documents/{doc_id}/reprocess` (P2I-9, pipeline-операция переиндексации)
- `POST /api/v1/documents/{doc_id}/versions` — загрузка версии файла
- `GET /api/v1/documents/{doc_id}/status` — статус обработки
- `GET /api/v1/documents/{doc_id}/tasks` — список pipeline-задач документа
- `GET /api/v1/documents/{doc_id}/errors` — журнал ошибок обработки

Все остальные GET /documents/*, POST /documents/{id}/approve,
DELETE /documents/{id} перенесены в registry-service
(см. docs/api/registry_service_api.md, группа documents).
"""

import io

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


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/errors
# ---------------------------------------------------------------------------


class TestDocumentErrors:
    """Tests for GET /api/v1/documents/{doc_id}/errors."""

    ERRORS_URL = "/api/v1/documents/{doc_id}/errors"

    def test_errors_success(self, client: TestClient, auth_header: dict):
        """Returns errors with expected structure."""
        response = client.get(
            self.ERRORS_URL.format(doc_id=1),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data
        assert "meta" in data
        assert isinstance(data["errors"], list)
        assert "total" in data["meta"]
        assert "page" in data["meta"]
        assert "page_size" in data["meta"]

    def test_errors_pagination(self, client: TestClient, auth_header: dict):
        """Page and page_size params are applied."""
        response = client.get(
            self.ERRORS_URL.format(doc_id=1),
            params={"page": 2, "page_size": 10},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page"] == 2
        assert data["meta"]["page_size"] == 10

    def test_errors_filter_stage(self, client: TestClient, auth_header: dict):
        """Stage filter is accepted."""
        response = client.get(
            self.ERRORS_URL.format(doc_id=1),
            params={"stage": "ocr"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_errors_filter_severity(self, client: TestClient, auth_header: dict):
        """Severity filter is accepted."""
        response = client.get(
            self.ERRORS_URL.format(doc_id=1),
            params={"severity": "warning"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_errors_without_auth(self, client: TestClient):
        """Returns 200 in mock mode."""
        response = client.get(
            self.ERRORS_URL.format(doc_id=1),
        )
        assert response.status_code == 200

    def test_errors_page_size_max_clamped(self, client: TestClient, auth_header: dict):
        """page_size above 100 is clamped to 100."""
        response = client.get(
            self.ERRORS_URL.format(doc_id=1),
            params={"page_size": 999},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page_size"] <= 100


# ---------------------------------------------------------------------------
#  POST /api/v1/documents/{doc_id}/versions
# ---------------------------------------------------------------------------


class TestDocumentCreateVersion:
    """Tests for POST /api/v1/documents/{doc_id}/versions."""

    VERSIONS_URL = "/api/v1/documents/{doc_id}/versions"

    def test_create_version_success(self, client: TestClient, auth_header: dict):
        """Upload version returns 202."""
        file_content = b"%PDF-1.4 test content for version upload"
        response = client.post(
            self.VERSIONS_URL.format(doc_id=1),
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["document_id"] == 1
        assert "version_id" in data
        assert "version_number" in data
        assert data["status"] == "uploaded"
        assert "task_id" in data
        assert "file_hash_sha256" in data

    def test_create_version_invalid_type(self, client: TestClient, auth_header: dict):
        """Invalid file type returns 422."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id=1),
            files={"file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_create_version_without_auth(self, client: TestClient):
        """Returns 202 in mock mode (mock auth works without header)."""
        file_content = b"%PDF-1.4 test"
        response = client.post(
            self.VERSIONS_URL.format(doc_id=1),
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )
        assert response.status_code == 202


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/status
# ---------------------------------------------------------------------------


class TestDocumentStatus:
    """Tests for GET /api/v1/documents/{doc_id}/status."""

    STATUS_URL = "/api/v1/documents/{doc_id}/status"

    def test_status_success(self, client: TestClient, auth_header: dict):
        """Returns status with expected structure."""
        response = client.get(
            self.STATUS_URL.format(doc_id=1),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert "status" in data
        assert "progress_percent" in data
        assert "steps" in data
        assert "pipeline" in data["steps"]

    def test_status_unknown_document(self, client: TestClient, auth_header: dict):
        """Unknown document returns 200 with pending status."""
        response = client.get(
            self.STATUS_URL.format(doc_id=99999),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == 99999
        assert data["status"] == "processing"

    def test_status_supports_longpoll_param(self, client: TestClient, auth_header: dict):
        """longpoll param is accepted."""
        response = client.get(
            self.STATUS_URL.format(doc_id=1),
            params={"longpoll": 30},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_status_without_auth(self, client: TestClient):
        """Returns 200 in mock mode."""
        response = client.get(
            self.STATUS_URL.format(doc_id=1),
        )
        assert response.status_code == 200
