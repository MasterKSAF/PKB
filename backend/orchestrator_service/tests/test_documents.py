"""
Tests for Documents API endpoints.

Covers:
  - Upload, list, get, delete documents
  - Status, queue, errors
  - Pages, page view, page text, page preview
  - Parameters, reprocess

NOTE: These tests run against the app in mock mode. In mock mode:
  - Auth dependency returns MOCK_USER for any request (no token validation)
  - All endpoints accept any document_id (no 404)
  - See conftest.py for mock configuration
"""

import io
import json
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestUploadDocument:
    """Tests for POST /api/v1/documents/"""

    def test_upload_pdf_document(self, client: TestClient, auth_header: dict):
        """Upload a PDF document successfully."""
        file_content = b"%PDF-1.4 mock pdf content"
        response = client.post(
            "/api/v1/documents/",
            files={
                "file": ("test_doc.pdf", io.BytesIO(file_content), "application/pdf")
            },
            data={"document_type": "normative"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        # DocumentCreateResponse does NOT include document_type
        assert data["document_id"].startswith("doc-")
        assert data["status"] == "queued"
        assert data["user_id"] == "u-mock-001"
        assert data["task_id"].startswith("task-ocr-")
        assert "created_at" in data

    def test_upload_with_metadata(self, client: TestClient, auth_header: dict):
        """Upload with JSON metadata string."""
        metadata = json.dumps({"project": "Проект А", "author": "Иванов"})
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("drawing.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"document_type": "drawing", "metadata": metadata},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert "document_id" in data
        assert data["status"] == "queued"

    def test_upload_unsupported_type(self, client: TestClient, auth_header: dict):
        """Upload with invalid document type should fail (Pydantic validation)."""
        # In mock mode, the file content-type is checked first (returns 400 for
        # text/plain), but an invalid document_type value may also trigger 422
        # via Pydantic validation on the Form field (depends on strict mode).
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("doc.txt", io.BytesIO(b"data"), "text/plain")},
            data={"document_type": "invalid_type"},
            headers=auth_header,
        )
        assert response.status_code in (400, 422)
        data = response.json()
        assert "error" in data or "detail" in data

    def test_upload_without_file(self, client: TestClient, auth_header: dict):
        """Request without file should fail."""
        response = client.post(
            "/api/v1/documents/",
            data={"document_type": "normative"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_upload_without_auth(self, client: TestClient):
        """Upload without auth works in mock mode (MOCK_USER is used)."""
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("doc.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"document_type": "normative"},
        )
        # In mock mode, auth dependency returns MOCK_USER for any request
        assert response.status_code == 202
        data = response.json()
        assert data["user_id"] == "u-mock-001"


class TestListDocuments:
    """Tests for GET /api/v1/documents/"""

    def test_list_documents_default(self, client: TestClient, auth_header: dict):
        """List documents with default pagination."""
        response = client.get("/api/v1/documents/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "items" in data
        assert "meta" in data
        assert isinstance(data["items"], list)
        # Default limit=20, offset=0 → page = (0//20)+1 = 1, page_size = 20
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 20

    def test_list_documents_with_pagination(
        self, client: TestClient, auth_header: dict
    ):
        """List documents with custom offset and limit."""
        response = client.get(
            "/api/v1/documents/?offset=10&limit=10",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        # page = (10 // 10) + 1 = 2, page_size = 10
        assert data["meta"]["page"] == 2
        assert data["meta"]["page_size"] == 10

    def test_list_documents_summary_fields(self, client: TestClient, auth_header: dict):
        """Summary should contain expected statistics."""
        response = client.get("/api/v1/documents/", headers=auth_header)
        data = response.json()
        summary = data["summary"]
        for key in ("total", "ocr_completed", "indexed", "need_attention"):
            assert key in summary
            assert isinstance(summary[key], int)

    def test_list_documents_item_structure(self, client: TestClient, auth_header: dict):
        """Each list item should have required fields."""
        response = client.get("/api/v1/documents/", headers=auth_header)
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            for field in (
                "document_id",
                "title",
                "document_type",
                "pages",
                "ocr_status",
                "index_status",
                "user_id",
                "uploaded_by",
                "created_at",
                "updated_at",
            ):
                assert field in item, f"Missing field: {field}"

    def test_list_documents_invalid_limit(self, client: TestClient, auth_header: dict):
        """Limit=0 should fail (ge=1 constraint)."""
        response = client.get(
            "/api/v1/documents/?limit=0",
            headers=auth_header,
        )
        assert response.status_code == 422


class TestGetDocument:
    """Tests for GET /api/v1/documents/{doc_id}"""

    def test_get_existing_document(self, client: TestClient, auth_header: dict):
        """Get document by ID should return details with doc_id echoed back."""
        doc_id = "doc-mock-001"
        response = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert data["filename"] == "21900M2_spec.pdf"
        assert "document_type" in data
        assert "status" in data
        assert "file_size" in data
        assert "pages_total" in data

    def test_get_document_full_schema(self, client: TestClient, auth_header: dict):
        """Document detail should contain all fields from DocumentDetailResponse."""
        response = client.get("/api/v1/documents/doc-mock-001", headers=auth_header)
        data = response.json()
        for field in (
            "document_id",
            "filename",
            "document_type",
            "status",
            "file_size",
            "pages_total",
            "pages_processed",
            "pages_failed",
            "user_id",
            "uploaded_by",
            "created_at",
            "updated_at",
        ):
            assert field in data, f"Missing field: {field}"
        # Mock mode always returns PROCESSED status
        assert data["status"] == "processed"
        assert data["document_type"] == "specification"

    def test_get_nonexistent_document(self, client: TestClient, auth_header: dict):
        """Non-existent document returns data (mock mode — no 404)."""
        response = client.get(
            "/api/v1/documents/doc-nonexistent",
            headers=auth_header,
        )
        # Mock mode always returns 200 with the given doc_id
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-nonexistent"

    def test_get_document_without_auth(self, client: TestClient):
        """Request without auth works in mock mode."""
        response = client.get("/api/v1/documents/doc-mock-001")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"


class TestDocumentStatus:
    """Tests for GET /api/v1/documents/{doc_id}/status"""

    @pytest.mark.parametrize(
        "doc_id",
        [
            "doc-mock-queued",
            "doc-mock-processing",
            "doc-mock-completed",
            "doc-mock-failed",
        ],
    )
    def test_document_status_various_states(
        self, client: TestClient, auth_header: dict, doc_id: str
    ):
        """Status endpoint accepts any document ID and returns processing status."""
        response = client.get(
            f"/api/v1/documents/{doc_id}/status",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        # Mock always returns DocumentStatusProcessing
        assert data["document_id"] == doc_id
        assert data["status"] == "processing"

    def test_document_status_has_progress(self, client: TestClient, auth_header: dict):
        """Status should include progress percentage and steps."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/status",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert data["status"] == "processing"
        assert "progress_percent" in data
        assert isinstance(data["progress_percent"], (int, float))
        assert "steps" in data
        steps = data["steps"]
        for step in ("ocr", "layout_parsing", "indexing"):
            assert step in steps, f"Missing step: {step}"
        assert steps["ocr"] == "in_progress"

    def test_document_status_nonexistent(self, client: TestClient, auth_header: dict):
        """Status for non-existent doc works (mock mode — no 404)."""
        response = client.get(
            "/api/v1/documents/bad-doc/status",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "bad-doc"
        assert data["status"] == "processing"


class TestDeleteDocument:
    """Tests for DELETE /api/v1/documents/{doc_id}"""

    def test_delete_document(self, client: TestClient, auth_header: dict):
        """Delete an existing document."""
        response = client.delete(
            "/api/v1/documents/doc-mock-001",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert "deleted_at" in data

    def test_delete_nonexistent_document(self, client: TestClient, auth_header: dict):
        """Delete non-existent document works (mock mode — no 404)."""
        response = client.delete(
            "/api/v1/documents/doc-nonexistent",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-nonexistent"
        assert "deleted_at" in data

    def test_delete_without_auth(self, client: TestClient):
        """Delete without auth works in mock mode."""
        response = client.delete("/api/v1/documents/doc-mock-001")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"


class TestReprocessDocument:
    """Tests for POST /api/v1/documents/{doc_id}/reprocess"""

    def test_reprocess_document_standard(self, client: TestClient, auth_header: dict):
        """Reprocess in standard mode."""
        response = client.post(
            "/api/v1/documents/doc-mock-001/reprocess",
            json={"mode": "standard"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert data["mode"] == "standard"
        # ReprocessResponse.status is "reprocessing_queued"
        assert data["status"] == "reprocessing_queued"
        assert data["user_id"] == "u-mock-001"
        assert data["task_id"].startswith("task-ocr-")
        assert "created_at" in data

    @pytest.mark.parametrize("mode", ["enhanced_preprocess", "fallback_ocr"])
    def test_reprocess_alternative_modes(
        self, client: TestClient, auth_header: dict, mode: str
    ):
        """Reprocess with alternative modes."""
        response = client.post(
            "/api/v1/documents/doc-mock-001/reprocess",
            json={"mode": mode},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["mode"] == mode
        assert data["status"] == "reprocessing_queued"

    def test_reprocess_invalid_mode(self, client: TestClient, auth_header: dict):
        """Invalid reprocess mode should fail (Pydantic validation)."""
        response = client.post(
            "/api/v1/documents/doc-mock-001/reprocess",
            json={"mode": "invalid_mode"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_reprocess_nonexistent_doc(self, client: TestClient, auth_header: dict):
        """Reprocess non-existent document works (mock mode — no 404)."""
        response = client.post(
            "/api/v1/documents/bad-doc/reprocess",
            json={"mode": "standard"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["document_id"] == "bad-doc"
        assert data["status"] == "reprocessing_queued"


class TestDocumentErrors:
    """Tests for GET /api/v1/documents/{doc_id}/errors"""

    def test_get_document_errors(self, client: TestClient, auth_header: dict):
        """Get error log for a document."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/errors",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data
        assert "meta" in data
        assert isinstance(data["errors"], list)

    def test_document_error_item_structure(self, client: TestClient, auth_header: dict):
        """Each error item should have required fields."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/errors",
            headers=auth_header,
        )
        data = response.json()
        if data["errors"]:
            error = data["errors"][0]
            for field in (
                "error_id",
                "document_id",
                "stage",
                "error_code",
                "error_message",
                "severity",
                "retry_attempt",
                "timestamp",
            ):
                assert field in error, f"Missing field: {field}"

    def test_get_errors_for_any_document(self, client: TestClient, auth_header: dict):
        """Mock mode always returns at least one error for any document ID."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/errors",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        # Mock endpoint always returns an OCR error when stage is not specified
        assert len(data["errors"]) >= 1
        assert data["errors"][0]["document_id"] == "doc-mock-001"
        assert data["errors"][0]["stage"] == "ocr"

    def test_errors_nonexistent_doc(self, client: TestClient, auth_header: dict):
        """Errors for non-existent doc works (mock mode — no 404)."""
        response = client.get(
            "/api/v1/documents/bad-doc/errors",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["errors"]) >= 1
        assert data["errors"][0]["document_id"] == "bad-doc"


class TestDocumentPages:
    """Tests for page-related endpoints."""

    def test_list_pages(self, client: TestClient, auth_header: dict):
        """List all pages of a document."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert "pages_total" in data
        assert "pages" in data
        assert "meta" in data
        if data["pages"]:
            page = data["pages"][0]
            for field in (
                "page",
                "width",
                "height",
                "ocr_status",
                "confidence",
                "has_text_layer",
            ):
                assert field in page, f"Missing field: {field}"

    def test_get_page_view(self, client: TestClient, auth_header: dict):
        """Get a specific page view with blocks."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages/1",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
        assert data["page"] == 1
        assert "width" in data
        assert "height" in data
        assert "blocks" in data
        if data["blocks"]:
            block = data["blocks"][0]
            for field in ("block_id", "type", "coordinates", "text"):
                assert field in block, f"Missing field: {field}"

    def test_get_page_text(self, client: TestClient, auth_header: dict):
        """Get OCR text for a specific page."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages/1/text",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert "full_text" in data
        assert "blocks" in data
        if data["blocks"]:
            block = data["blocks"][0]
            for field in ("block_id", "type", "coordinates", "text", "confidence"):
                assert field in block, f"Missing field: {field}"

    def test_get_page_preview(self, client: TestClient, auth_header: dict):
        """Get a page preview image URL."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages/1/preview",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert "document_title" in data
        assert data["page"] == 1
        assert "preview_url" in data
        assert "content_type" in data

    def test_page_view_out_of_range(self, client: TestClient, auth_header: dict):
        """Page number out of range still returns data (mock mode — no 404)."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages/9999",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 9999
        assert "image_url" in data
        assert "width" in data
        assert "height" in data
        assert "blocks" in data

    def test_page_text_out_of_range(self, client: TestClient, auth_header: dict):
        """Page text for out-of-range page works (mock mode — no 404)."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages/9999/text",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 9999
        assert "full_text" in data
        assert "blocks" in data


class TestDocumentParameters:
    """Tests for GET /api/v1/documents/{doc_id}/parameters"""

    def test_get_document_parameters(self, client: TestClient, auth_header: dict):
        """Get extracted parameters from a document."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/parameters",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert "document_type" in data
        assert data["document_type"] == "specification"
        assert "parameters" in data
        assert "extraction_confidence" in data
        assert "unconfirmed_fields" in data
        assert "updated_at" in data
        # Mock Validation Service returns empty unconfirmed_fields by default
        assert data["unconfirmed_fields"] == []

    def test_parameters_structure(self, client: TestClient, auth_header: dict):
        """Parameters should contain expected sub-fields."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/parameters",
            headers=auth_header,
        )
        data = response.json()["parameters"]
        for field in (
            "designation",
            "title",
            "materials",
            "dimensions",
            "references",
            "specification_items",
        ):
            assert field in data, f"Missing field: {field}"
        # Check mock data values
        assert data["designation"] == "21900M2.362135.0903"
        assert "сталь 09Г2С" in data["materials"]
        assert len(data["specification_items"]) >= 1

    def test_parameters_specification_items(
        self, client: TestClient, auth_header: dict
    ):
        """Specification items should have proper structure."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/parameters",
            headers=auth_header,
        )
        items = response.json()["parameters"]["specification_items"]
        assert len(items) >= 1
        item = items[0]
        for field in (
            "position",
            "name",
            "quantity",
            "dimensions",
            "weight",
            "material",
            "note",
        ):
            assert field in item, f"Missing field: {field}"
        # Verify mock data
        assert item["position"] == "1"
        assert item["name"] == "Кница"

    def test_parameters_nonexistent_doc(self, client: TestClient, auth_header: dict):
        """Parameters for non-existent doc works (mock mode — no 404)."""
        response = client.get(
            "/api/v1/documents/bad-doc/parameters",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "bad-doc"
        assert "parameters" in data

    def test_unconfirmed_fields_value(self, client: TestClient, auth_header: dict):
        """Unconfirmed fields should contain the expected mock value."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/parameters",
            headers=auth_header,
        )
        data = response.json()
        assert isinstance(data["unconfirmed_fields"], list)
        # Mock Validation Service returns empty unconfirmed_fields by default
        assert data["unconfirmed_fields"] == []


class TestDocumentQueue:
    """Tests for GET /api/v1/documents/queue"""

    def test_get_queue(self, client: TestClient, auth_header: dict):
        """Get document processing queue."""
        response = client.get(
            "/api/v1/documents/queue",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "queue" in data
        assert "meta" in data
        assert isinstance(data["queue"], list)

    def test_queue_item_structure(self, client: TestClient, auth_header: dict):
        """Each queue item should have required fields."""
        response = client.get("/api/v1/documents/queue", headers=auth_header)
        data = response.json()
        if data["queue"]:
            item = data["queue"][0]
            for field in (
                "document_id",
                "title",
                "document_type",
                "status",
                "progress_percent",
                "steps",
                "user_id",
                "uploaded_by",
                "created_at",
            ):
                assert field in item, f"Missing field: {field}"
            # Verify mock data values
            assert item["status"] == "processing"
            assert "ocr" in item["steps"]
            assert "layout_parsing" in item["steps"]
            assert "indexing" in item["steps"]

    def test_queue_meta_structure(self, client: TestClient, auth_header: dict):
        """Queue metadata should contain expected fields."""
        response = client.get("/api/v1/documents/queue", headers=auth_header)
        data = response.json()["meta"]
        for field in ("total_in_queue", "page", "page_size"):
            assert field in data, f"Missing field: {field}"


class TestDocumentFile:
    """Tests for GET /api/v1/documents/{doc_id}/file"""

    def test_get_document_file(self, client: TestClient, auth_header: dict):
        """Get document file download info."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/file",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert "document_title" in data
        assert "content_type" in data
        assert "file_url" in data
        assert data["content_type"] == "application/pdf"

    def test_file_nonexistent_doc(self, client: TestClient, auth_header: dict):
        """File info for non-existent doc works (mock mode — no 404)."""
        response = client.get(
            "/api/v1/documents/bad-doc/file",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "bad-doc"
        assert "file_url" in data
