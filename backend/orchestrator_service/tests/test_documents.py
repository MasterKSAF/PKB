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
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        # DocumentCreateResponse: task_id (int), version_id, file_hash_sha256, file_size_bytes
        assert isinstance(data["task_id"], int)
        assert isinstance(data["version_id"], str)
        assert len(data["version_id"]) > 0
        assert data["status"] == "uploaded"
        assert isinstance(data["file_hash_sha256"], str)
        assert len(data["file_hash_sha256"]) == 64  # SHA-256 hex
        assert isinstance(data["file_size_bytes"], int)
        assert data["file_size_bytes"] == len(file_content)
        assert isinstance(data["is_duplicate_file"], bool)
        assert isinstance(data["is_duplicate_document"], bool)
        assert "title_hash_sha256" in data
        assert "created_at" in data

    def test_upload_with_metadata(self, client: TestClient, auth_header: dict):
        """Upload with JSON metadata string."""
        metadata = json.dumps({"project": "Проект А", "author": "Иванов"})
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("drawing.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"source_type": "GOST", "metadata": metadata},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert isinstance(data["task_id"], int)
        assert data["status"] == "uploaded"

    def test_upload_unsupported_type(self, client: TestClient, auth_header: dict):
        """Upload with invalid source_type should fail (400)."""
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("doc.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"source_type": "INVALID_TYPE"},
            headers=auth_header,
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data

    def test_upload_without_file(self, client: TestClient, auth_header: dict):
        """Request without file should fail."""
        response = client.post(
            "/api/v1/documents/",
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_upload_without_auth(self, client: TestClient):
        """Upload without auth works in mock mode (MOCK_USER is used)."""
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("doc.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"source_type": "GOST"},
        )
        # In mock mode, auth dependency returns MOCK_USER for any request
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "uploaded"


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
        # Default page=1, page_size=20
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 20

    def test_list_documents_with_pagination(
        self, client: TestClient, auth_header: dict
    ):
        """List documents with custom page and page_size."""
        response = client.get(
            "/api/v1/documents/?page=2&page_size=10",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page"] == 2
        assert data["meta"]["page_size"] == 10

    def test_list_documents_summary_fields(self, client: TestClient, auth_header: dict):
        """Summary should contain FSM status based statistics."""
        response = client.get("/api/v1/documents/", headers=auth_header)
        data = response.json()
        summary = data["summary"]
        for key in (
            "total",
            "uploaded",
            "previewing",
            "awaiting_decision",
            "parsing",
            "validation",
            "review_required",
            "ready_for_promotion",
            "approved",
            "failed",
            "archived",
        ):
            assert key in summary, f"Missing summary field: {key}"
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
                "doc_code",
                "source_type",
                "era",
                "validity_status",
                "jurisdiction",
                "issuing_body",
                "mks_oks_code",
                "okstu_code",
                "classification_status",
                "file_hash_sha256",
                "file_size_bytes",
                "status",
                "latest_version",
                "total_versions",
                "user_id",
                "uploaded_by",
                "created_at",
                "updated_at",
            ):
                assert field in item, f"Missing field: {field}"

    def test_list_documents_invalid_limit(self, client: TestClient, auth_header: dict):
        """page=0 should fail (ge=1 constraint)."""
        response = client.get(
            "/api/v1/documents/?page=0",
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
        assert data["title"] == "Стойки установочные"
        assert "doc_code" in data
        assert "source_type" in data
        assert "status" in data
        assert "title_hash_sha256" in data
        assert "era" in data
        assert "validity_status" in data
        assert "jurisdiction" in data
        assert "issuing_body" in data
        assert "mks_oks_code" in data
        assert "classification_status" in data
        assert "metadata" in data
        assert "latest_version" in data
        assert "total_versions" in data

    def test_get_document_full_schema(self, client: TestClient, auth_header: dict):
        """Document detail should contain all fields from DocumentDetailResponse."""
        response = client.get("/api/v1/documents/doc-mock-001", headers=auth_header)
        data = response.json()
        for field in (
            "document_id",
            "title",
            "doc_code",
            "source_type",
            "title_hash_sha256",
            "status",
            "era",
            "validity_status",
            "jurisdiction",
            "issuing_body",
            "industry_code",
            "enterprise_id",
            "mks_oks_code",
            "okstu_code",
            "classification_status",
            "metadata",
            "latest_version",
            "total_versions",
            "user_id",
            "uploaded_by",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ):
            assert field in data, f"Missing field: {field}"
        # Mock mode returns source_type == "GOST" and status == "approved"
        assert data["source_type"] == "GOST"
        assert data["status"] == "approved"
        # latest_version should have version_id, version_number, etc.
        lv = data["latest_version"]
        assert "version_id" in lv
        assert lv["version_number"] == 1
        assert "file_hash_sha256" in lv
        assert "size_bytes" in lv

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
            "doc-mock-001",
            "doc-mock-002",
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
        assert "progress_percent" in data
        # Steps should contain pipelines with formation and indexation
        assert "steps" in data
        steps = data["steps"]
        assert "pipeline" in steps, "Missing pipeline wrapper"
        assert "formation" in steps["pipeline"], "Missing formation pipeline"
        assert "indexation" in steps["pipeline"], "Missing indexation pipeline"

    def test_document_status_has_progress(self, client: TestClient, auth_header: dict):
        """Status should include progress percentage and pipeline steps."""
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
        # Formation pipeline is nested under 'pipeline' key
        assert "pipeline" in steps
        pipe = steps["pipeline"]
        # Check formation pipeline has sub-steps
        assert "formation" in pipe
        formation = pipe["formation"]
        assert "status" in formation
        assert "preview" in formation
        assert "parsing" in formation
        assert "validation" in formation
        assert "registry" in formation
        # Check indexation pipeline
        assert "indexation" in pipe
        indexation = pipe["indexation"]
        assert "status" in indexation
        assert "rag_indexing" in indexation

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

    def test_reprocess_document_full(self, client: TestClient, auth_header: dict):
        """Reprocess in full mode."""
        response = client.post(
            "/api/v1/documents/doc-mock-001/reprocess",
            json={"mode": "full"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert data["mode"] == "full"
        # ReprocessResponse.status is "reprocessing_queued"
        assert data["status"] == "reprocessing_queued"
        assert data["user_id"] == "u-mock-001"
        assert data["task_id"].startswith("task-repro-")
        assert "created_at" in data

    @pytest.mark.parametrize("mode", ["ocr_only", "chunking_only"])
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
            json={"mode": "full"},
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
        """Each error item should have required fields (no document_id)."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/errors",
            headers=auth_header,
        )
        data = response.json()
        if data["errors"]:
            error = data["errors"][0]
            for field in (
                "error_id",
                "stage",
                "error_code",
                "error_message",
                "severity",
                "retry_attempt",
                "timestamp",
            ):
                assert field in error, f"Missing field: {field}"
            # document_id is no longer part of ProcessingError

    def test_get_errors_for_any_document(self, client: TestClient, auth_header: dict):
        """Mock mode always returns at least one error for any document ID."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/errors",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        # Mock endpoint returns an OCR error when stage is not specified
        assert len(data["errors"]) >= 1
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
        """Get a specific page view with blocks (returns JSONResponse)."""
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
        # Page view returns blocks with minimal metadata (no dedicated Pydantic model)

    def test_get_page_text(self, client: TestClient, auth_header: dict):
        """Get OCR text for a specific page."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages/1/text",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert data["page"] == 1
        assert "width" in data
        assert "height" in data
        # PageTextResponse has blocks but no full_text
        assert "full_text" not in data, "full_text field should not be present"
        assert "blocks" in data
        if data["blocks"]:
            block = data["blocks"][0]
            for field in ("number", "type", "bbox", "content", "confidence"):
                assert field in block, f"Missing field: {field}"
            # bbox should be a list of 4 floats in normalized 0..1 range
            assert isinstance(block["bbox"], list)
            assert len(block["bbox"]) == 4
            for coord in block["bbox"]:
                assert 0.0 <= coord <= 1.0, f"bbox coord {coord} out of range"

    def test_get_page_preview(self, client: TestClient, auth_header: dict):
        """Get a page preview with image URL, blocks and text layer."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages/1/preview",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-mock-001"
        assert data["page"] == 1
        assert "image_url" in data
        assert "blocks" in data
        assert "text_layer" in data

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
        assert "parameters" in data
        assert isinstance(data["parameters"], list)
        assert "total" in data
        assert isinstance(data["total"], int)

    def test_parameters_item_structure(self, client: TestClient, auth_header: dict):
        """Each parameter item should have required fields."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/parameters",
            headers=auth_header,
        )
        data = response.json()
        if data["parameters"]:
            item = data["parameters"][0]
            for field in (
                "symbol",
                "description",
                "unit",
                "value",
                "range",
                "source_clause",
                "source_page",
            ):
                assert field in item, f"Missing field: {field}"
            # Verify mock data values
            assert item["symbol"] == "R_доп"
            assert item["description"] == "Допустимый радиус"
            assert item["unit"] == "мм"

    def test_parameters_with_range(self, client: TestClient, auth_header: dict):
        """Parameter with range should have min/max fields."""
        response = client.get(
            "/api/v1/documents/doc-mock-001/parameters",
            headers=auth_header,
        )
        data = response.json()
        # Find the parameter with a range (second item in mock)
        if len(data["parameters"]) >= 2:
            range_item = data["parameters"][1]
            assert range_item["symbol"] == "L"
            assert range_item["range"] is not None
            assert "min" in range_item["range"]
            assert "max" in range_item["range"]
            assert range_item["range"]["min"] == 6
            assert range_item["range"]["max"] == 80

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
                "doc_code",
                "source_type",
                "status",
                "progress_percent",
                "current_step",
                "steps",
                "user_id",
                "uploaded_by",
                "created_at",
                "started_at",
                "estimated_completion",
            ):
                assert field in item, f"Missing field: {field}"
            # Verify mock data values
            assert item["source_type"] == "GOST"
            assert item["status"] == "validation"
            # Steps should be a QueuePipelineSteps with pipeline/formation/indexation
            assert "pipeline" in item["steps"]
            assert "formation" in item["steps"]["pipeline"]
            assert "indexation" in item["steps"]["pipeline"]
            assert item["steps"]["pipeline"]["formation"]["status"] == "in_progress"

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
        assert "version_id" in data
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
        assert "version_id" in data
        assert "file_url" in data
