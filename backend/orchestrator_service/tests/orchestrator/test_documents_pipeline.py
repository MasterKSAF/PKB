"""
Тесты pipeline-операций с документами.

Покрывает:
  - POST /documents/{id}/reprocess — full / partial mode
  - POST /documents/{id}/reprocess — несуществующий документ
  - GET /documents/{id}/tasks — задачи документа

Внимание:
  - POST /documents (deprecated) — эндпоинт удалён из оркестратора
  - POST/GET /documents/{id}/versions — управление версиями в Registry
  - Большая часть reprocess тестов уже в tests/test_documents_api.py
"""

from fastapi.testclient import TestClient


class TestReprocessDocumentExtended:
    """POST /api/v1/documents/{doc_id}/reprocess — расширенные сценарии."""

    URL = "/api/v1/documents/{doc_id}/reprocess"

    def test_reprocess_full_mode_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Response для full mode содержит все поля."""
        response = client.post(
            self.URL.format(doc_id="doc-test-001"),
            json={"mode": "full"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["mode"] == "full"
        assert data["document_id"] == "doc-test-001"
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "reprocessing_queued"
        assert "created_at" in data

    def test_reprocess_partial_mode(
        self, client: TestClient, auth_header: dict
    ):
        """Reprocess с mode=ocr_only."""
        response = client.post(
            self.URL.format(doc_id="doc-test-002"),
            json={"mode": "ocr_only"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["mode"] == "ocr_only"

    def test_reprocess_nonexistent_document(
        self, client: TestClient, auth_header: dict
    ):
        """Reprocess для несуществующего документа → 202 (создаётся задача)."""
        response = client.post(
            self.URL.format(doc_id="nonexistent-doc"),
            json={"mode": "full"},
            headers=auth_header,
        )
        # Orchestrator doesn't validate document existence at this level
        assert response.status_code == 202
        # Task is created even for non-existent doc (registry check is downstream)
        data = response.json()
        assert data["document_id"] == "nonexistent-doc"


class TestDocumentTasksExtended:
    """GET /api/v1/documents/{doc_id}/tasks — задачи документа."""

    URL = "/api/v1/documents/{doc_id}/tasks"

    def test_document_tasks_existing(
        self, client: TestClient, auth_header: dict
    ):
        """Существующий документ → 200."""
        response = client.get(
            self.URL.format(doc_id=1), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == 1
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    def test_document_tasks_nonexistent(
        self, client: TestClient, auth_header: dict
    ):
        """Несуществующий документ → 200, пустой список."""
        response = client.get(
            self.URL.format(doc_id=99999), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == 99999
        assert data["tasks"] == []

    def test_document_tasks_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Структура элемента tasks."""
        response = client.get(
            self.URL.format(doc_id=1), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        if data["tasks"]:
            t = data["tasks"][0]
            assert "task_id" in t
            assert "status" in t
            assert "pipeline_stage" in t
            assert "created_at" in t
