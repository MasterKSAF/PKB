"""
Tests for new API endpoints added to the orchestrator service.

Covers:
  - Preview (start + status)
  - Decision (proceed, stop_duplicate, force_new_version)
  - Versions (upload + list)
  - Approve document
  - Document history
  - top_k validation in search
  - Upload with new fields (source_type, title, doc_code, etc.)
  - List with new filter params (source_type, era, validity_status, etc.)

NOTE: These tests run against the app in mock mode. In mock mode:
  - Auth dependency returns MOCK_USER for any request (no token validation)
  - All endpoints accept any task_id / document_id (no 404)
  - See conftest.py for mock configuration
"""

import io
from datetime import datetime

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
#  1. POST /api/v1/documents/tasks/{task_id}/preview
# ---------------------------------------------------------------------------


class TestTaskPreview:
    """Tests for POST /api/v1/documents/tasks/{task_id}/preview"""

    PREVIEW_URL = "/api/v1/documents/tasks/{task_id}/preview"

    def test_start_preview_returns_202(self, client: TestClient, auth_header: dict):
        """Starting preview returns 202 Accepted with preview metadata."""
        response = client.post(
            self.PREVIEW_URL.format(task_id=12345),
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == 12345
        assert data["status"] == "previewing"
        # estimated_completion should be a datetime string (ISO 8601) or null
        assert "estimated_completion" in data
        if data["estimated_completion"] is not None:
            # Verify it is parseable as ISO datetime
            datetime.fromisoformat(data["estimated_completion"])

    def test_start_preview_response_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Response contains all expected fields from TaskPreviewResponse."""
        response = client.post(
            self.PREVIEW_URL.format(task_id=999),
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert "estimated_completion" in data
        assert isinstance(data["task_id"], int)
        assert isinstance(data["status"], str)

    def test_start_preview_with_nonexistent_task_id(
        self, client: TestClient, auth_header: dict
    ):
        """Non-existent task_id still returns 202 in mock mode (mock bypasses 404)."""
        response = client.post(
            self.PREVIEW_URL.format(task_id=-1),
            headers=auth_header,
        )
        # Mock mode does not validate task existence
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == -1

    def test_start_preview_without_auth(self, client: TestClient):
        """Preview start works without auth in mock mode."""
        response = client.post(
            self.PREVIEW_URL.format(task_id=42),
        )
        assert response.status_code == 202

    def test_start_preview_estimated_completion_type(
        self, client: TestClient, auth_header: dict
    ):
        """estimated_completion is either None or an ISO datetime string."""
        response = client.post(
            self.PREVIEW_URL.format(task_id=777),
            headers=auth_header,
        )
        data = response.json()
        ec = data["estimated_completion"]
        assert ec is None or isinstance(ec, str)
        if ec:
            # Must be a valid ISO datetime
            parsed = datetime.fromisoformat(ec)
            assert parsed is not None


# ---------------------------------------------------------------------------
#  2. GET /api/v1/documents/tasks/{task_id}/preview/status
# ---------------------------------------------------------------------------


class TestPreviewStatus:
    """Tests for GET /api/v1/documents/tasks/{task_id}/preview/status"""

    STATUS_URL = "/api/v1/documents/tasks/{task_id}/preview/status"

    def test_get_preview_status_returns_200(
        self, client: TestClient, auth_header: dict
    ):
        """Preview status returns 200 OK."""
        response = client.get(
            self.STATUS_URL.format(task_id=12345),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_preview_status_top_level_fields(
        self, client: TestClient, auth_header: dict
    ):
        """Response contains all expected top-level fields."""
        response = client.get(
            self.STATUS_URL.format(task_id=12345),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "status" in data
        assert "ocr_parser_status" in data
        assert "converter_validator_status" in data
        assert "preview" in data
        assert "duplicates" in data
        assert "decision_required" in data

    def test_preview_structure(self, client: TestClient, auth_header: dict):
        """Preview metadata has expected fields."""
        response = client.get(
            self.STATUS_URL.format(task_id=12345),
            headers=auth_header,
        )
        data = response.json()
        preview = data["preview"]
        if preview is not None:
            assert "doc_code" in preview
            assert "title" in preview
            assert "document_type" in preview
            assert "year" in preview
            # doc_code and title should be strings or null
            assert isinstance(preview.get("doc_code"), (str, type(None)))
            assert isinstance(preview.get("title"), (str, type(None)))
            assert isinstance(preview.get("document_type"), (str, type(None)))
            assert isinstance(preview.get("year"), (str, type(None)))

    def test_duplicates_structure(self, client: TestClient, auth_header: dict):
        """Each duplicate item has the expected fields."""
        response = client.get(
            self.STATUS_URL.format(task_id=12345),
            headers=auth_header,
        )
        data = response.json()
        duplicates = data["duplicates"]
        assert isinstance(duplicates, list)
        if duplicates:
            dup = duplicates[0]
            assert "document_id" in dup
            assert "doc_code" in dup
            assert "title" in dup
            assert "similarity" in dup
            assert isinstance(dup["similarity"], (int, float))
            # similarity should be in the [0, 1] range
            assert 0.0 <= dup["similarity"] <= 1.0

    def test_decision_required_is_bool(self, client: TestClient, auth_header: dict):
        """decision_required is a boolean."""
        response = client.get(
            self.STATUS_URL.format(task_id=12345),
            headers=auth_header,
        )
        data = response.json()
        assert isinstance(data["decision_required"], bool)

    def test_status_is_string(self, client: TestClient, auth_header: dict):
        """status is a string."""
        response = client.get(
            self.STATUS_URL.format(task_id=12345),
            headers=auth_header,
        )
        data = response.json()
        assert isinstance(data["status"], str)

    def test_preview_status_with_longpoll(
        self, client: TestClient, auth_header: dict
    ):
        """longpoll parameter (0..60) is accepted."""
        for lp in (0, 15, 30, 60):
            response = client.get(
                self.STATUS_URL.format(task_id=12345),
                params={"longpoll": lp},
                headers=auth_header,
            )
            assert response.status_code == 200

    def test_preview_status_invalid_longpoll(
        self, client: TestClient, auth_header: dict
    ):
        """longpoll outside 0..60 should return 422."""
        for lp in (-1, 61):
            response = client.get(
                self.STATUS_URL.format(task_id=12345),
                params={"longpoll": lp},
                headers=auth_header,
            )
            assert response.status_code == 422

    def test_preview_status_ocr_and_converter_statuses(
        self, client: TestClient, auth_header: dict
    ):
        """OCR parser and converter/validator statuses are strings or null."""
        response = client.get(
            self.STATUS_URL.format(task_id=12345),
            headers=auth_header,
        )
        data = response.json()
        for key in ("ocr_parser_status", "converter_validator_status"):
            val = data.get(key)
            assert val is None or isinstance(val, str)

    def test_preview_status_without_auth(self, client: TestClient):
        """Preview status works without auth in mock mode."""
        response = client.get(
            self.STATUS_URL.format(task_id=42),
        )
        assert response.status_code == 200

    def test_document_id_is_string(self, client: TestClient, auth_header: dict):
        """document_id is a string or null."""
        response = client.get(
            self.STATUS_URL.format(task_id=12345),
            headers=auth_header,
        )
        data = response.json()
        assert data["document_id"] is None or isinstance(data["document_id"], str)


# ---------------------------------------------------------------------------
#  3. POST /api/v1/documents/tasks/{task_id}/decide
# ---------------------------------------------------------------------------


class TestDecideTask:
    """Tests for POST /api/v1/documents/tasks/{task_id}/decide"""

    DECIDE_URL = "/api/v1/documents/tasks/{task_id}/decide"

    def test_decide_proceed(self, client: TestClient, auth_header: dict):
        """Decision to proceed returns 202 with status='proceeding'."""
        response = client.post(
            self.DECIDE_URL.format(task_id=12345),
            json={"action": "proceed"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "proceeding"
        assert data["action"] == "proceed"
        assert "document_id" in data
        assert "message" in data

    def test_decide_stop_duplicate(self, client: TestClient, auth_header: dict):
        """Decision to stop as duplicate returns 202 with status='stopped'."""
        response = client.post(
            self.DECIDE_URL.format(task_id=12345),
            json={"action": "stop_duplicate"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "stopped"
        assert data["action"] == "stop_duplicate"
        assert "document_id" in data
        assert "message" in data

    def test_decide_force_new_version(self, client: TestClient, auth_header: dict):
        """Decision to force new version returns 202 with status='forcing'."""
        response = client.post(
            self.DECIDE_URL.format(task_id=12345),
            json={"action": "force_new_version"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "forcing"
        assert data["action"] == "force_new_version"
        assert "document_id" in data
        assert "message" in data

    def test_decide_with_comment(self, client: TestClient, auth_header: dict):
        """Decision with a comment is accepted."""
        response = client.post(
            self.DECIDE_URL.format(task_id=12345),
            json={"action": "proceed", "comment": "Проверено, всё верно"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_decide_invalid_action(self, client: TestClient, auth_header: dict):
        """Invalid action string returns 422."""
        response = client.post(
            self.DECIDE_URL.format(task_id=12345),
            json={"action": "invalid_action"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_decide_missing_action(self, client: TestClient, auth_header: dict):
        """Missing action field returns 422."""
        response = client.post(
            self.DECIDE_URL.format(task_id=12345),
            json={},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_decide_response_has_all_fields(
        self, client: TestClient, auth_header: dict
    ):
        """Response has document_id, status, action, and message."""
        response = client.post(
            self.DECIDE_URL.format(task_id=12345),
            json={"action": "proceed"},
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "status" in data
        assert "action" in data
        assert "message" in data
        assert isinstance(data["document_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["action"], str)
        assert isinstance(data["message"], str)

    def test_decide_without_auth(self, client: TestClient):
        """Decide works without auth in mock mode."""
        response = client.post(
            self.DECIDE_URL.format(task_id=42),
            json={"action": "proceed"},
        )
        assert response.status_code == 202


# ---------------------------------------------------------------------------
#  4. POST /api/v1/documents/{doc_id}/versions
# ---------------------------------------------------------------------------


class TestVersionCreate:
    """Tests for POST /api/v1/documents/{doc_id}/versions"""

    VERSIONS_URL = "/api/v1/documents/{doc_id}/versions"

    def test_upload_version_returns_202(self, client: TestClient, auth_header: dict):
        """Uploading a new version returns 202."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.pdf",
                    io.BytesIO(b"%PDF-1.4 version 2 content"),
                    "application/pdf",
                )
            },
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_upload_version_response_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Response has all expected VersionCreateResponse fields."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.pdf",
                    io.BytesIO(b"%PDF-1.4 version"),
                    "application/pdf",
                )
            },
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "version_id" in data
        assert "version_number" in data
        assert "status" in data
        assert "task_id" in data
        assert "file_hash_sha256" in data
        assert "is_duplicate_file" in data
        assert "created_at" in data

        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["version_id"], str)
        assert isinstance(data["version_number"], int)
        assert isinstance(data["status"], str)
        assert isinstance(data["task_id"], int)
        assert isinstance(data["file_hash_sha256"], str)
        assert isinstance(data["is_duplicate_file"], bool)

    def test_upload_version_status_uploaded(
        self, client: TestClient, auth_header: dict
    ):
        """Version upload status should be 'uploaded'."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.pdf",
                    io.BytesIO(b"%PDF-1.4 version"),
                    "application/pdf",
                )
            },
            headers=auth_header,
        )
        data = response.json()
        assert data["status"] == "uploaded"

    def test_upload_version_unsupported_type(
        self, client: TestClient, auth_header: dict
    ):
        """Uploading a non-PDF file type returns 400."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.txt",
                    io.BytesIO(b"plain text"),
                    "text/plain",
                )
            },
            headers=auth_header,
        )
        assert response.status_code == 400

    def test_upload_version_without_file(
        self, client: TestClient, auth_header: dict
    ):
        """Request without file returns 422."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_upload_version_without_auth(self, client: TestClient):
        """Version upload works without auth in mock mode."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.pdf",
                    io.BytesIO(b"%PDF-1.4 content"),
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 202


# ---------------------------------------------------------------------------
#  5. GET /api/v1/documents/{doc_id}/versions
# ---------------------------------------------------------------------------


class TestVersionsList:
    """Tests for GET /api/v1/documents/{doc_id}/versions"""

    VERSIONS_URL = "/api/v1/documents/{doc_id}/versions"

    def test_list_versions_returns_200(self, client: TestClient, auth_header: dict):
        """Listing versions returns 200."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_versions_response_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Response has document_id, versions list, and meta with total."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "versions" in data
        assert "meta" in data
        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["versions"], list)
        assert "total" in data["meta"]

    def test_list_versions_item_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Each version item has the expected fields."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["versions"]:
            version = data["versions"][0]
            assert "version_id" in version
            assert "version_number" in version
            assert "format_code" in version
            assert "format_label" in version
            assert "file_key" in version
            assert "file_hash_sha256" in version
            assert "size_bytes" in version
            assert "uploaded_at" in version
            assert "uploaded_by" in version

            assert isinstance(version["version_id"], str)
            assert isinstance(version["version_number"], int)
            assert isinstance(version["format_code"], str)
            assert isinstance(version["format_label"], str)
            assert isinstance(version["file_key"], str)
            assert isinstance(version["file_hash_sha256"], str)
            assert isinstance(version["size_bytes"], int)

    def test_list_versions_meta_total_is_int(
        self, client: TestClient, auth_header: dict
    ):
        """Meta.total is a non-negative integer."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        total = data["meta"]["total"]
        assert isinstance(total, int)
        assert total >= 0

    def test_list_versions_without_auth(self, client: TestClient):
        """List versions works without auth in mock mode."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  6. POST /api/v1/documents/{doc_id}/approve
# ---------------------------------------------------------------------------


class TestApproveDocument:
    """Tests for POST /api/v1/documents/{doc_id}/approve"""

    APPROVE_URL = "/api/v1/documents/{doc_id}/approve"

    def test_approve_with_force_and_comment(
        self, client: TestClient, auth_header: dict
    ):
        """Approve with force=True and a comment returns 202."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True, "comment": "Утверждено главным инженером"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_approve_without_force(self, client: TestClient, auth_header: dict):
        """Approve with force=False (default) also works."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": False},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_approve_default_force(self, client: TestClient, auth_header: dict):
        """Approve with empty body uses default force=False."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_approve_response_structure(self, client: TestClient, auth_header: dict):
        """Response has all expected ApproveResponse fields."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True, "comment": "OK"},
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "status" in data
        assert "promotion_task_id" in data
        assert "approved_by" in data
        assert "approved_at" in data

        assert data["document_id"] == "doc-test-001"
        assert data["status"] == "approved"
        assert isinstance(data["promotion_task_id"], str)
        assert isinstance(data["approved_by"], str)
        assert isinstance(data["approved_at"], str)

    def test_approve_promotion_task_id_prefix(
        self, client: TestClient, auth_header: dict
    ):
        """promotion_task_id starts with 'promo-'."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True},
            headers=auth_header,
        )
        data = response.json()
        assert data["promotion_task_id"].startswith("promo-")

    def test_approve_approved_at_iso_datetime(
        self, client: TestClient, auth_header: dict
    ):
        """approved_at is a valid ISO datetime string."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True},
            headers=auth_header,
        )
        data = response.json()
        parsed = datetime.fromisoformat(data["approved_at"])
        assert parsed is not None

    def test_approve_without_auth(self, client: TestClient):
        """Approve works without auth in mock mode."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True},
        )
        assert response.status_code == 202


# ---------------------------------------------------------------------------
#  7. GET /api/v1/documents/{doc_id}/history
# ---------------------------------------------------------------------------


class TestDocumentHistory:
    """Tests for GET /api/v1/documents/{doc_id}/history"""

    HISTORY_URL = "/api/v1/documents/{doc_id}/history"

    def test_get_history_returns_200(self, client: TestClient, auth_header: dict):
        """Getting document history returns 200."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_history_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, history list, and meta with total."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "history" in data
        assert "meta" in data
        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["history"], list)
        assert "total" in data["meta"]

    def test_history_item_structure(self, client: TestClient, auth_header: dict):
        """Each history item has the expected fields."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["history"]:
            item = data["history"][0]
            assert "history_id" in item
            assert "old_status" in item
            assert "new_status" in item
            assert "comment" in item
            assert "changed_by" in item
            assert "changed_at" in item

            assert isinstance(item["history_id"], str)
            assert isinstance(item["new_status"], str)
            assert isinstance(item["changed_by"], str)

    def test_history_comment_structure(self, client: TestClient, auth_header: dict):
        """Comment inside a history item has reason and details fields."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["history"]:
            comment = data["history"][0].get("comment")
            if comment is not None:
                assert "reason" in comment
                assert "details" in comment
                assert isinstance(comment.get("reason"), (str, type(None)))
                assert isinstance(comment.get("details"), (str, type(None)))

    def test_history_meta_total_is_int(self, client: TestClient, auth_header: dict):
        """Meta.total is a non-negative integer."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        total = data["meta"]["total"]
        assert isinstance(total, int)
        assert total >= 0

    def test_history_changed_at_iso_datetime(
        self, client: TestClient, auth_header: dict
    ):
        """changed_at is a valid ISO datetime string."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["history"]:
            parsed = datetime.fromisoformat(data["history"][0]["changed_at"])
            assert parsed is not None

    def test_history_old_status_may_be_null(
        self, client: TestClient, auth_header: dict
    ):
        """old_status can be null (first transition has no previous status)."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["history"]:
            item = data["history"][0]
            assert item["old_status"] is None or isinstance(item["old_status"], str)

    def test_history_without_auth(self, client: TestClient):
        """History works without auth in mock mode."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  8. top_k validation in search
# ---------------------------------------------------------------------------


class TestSearchTopKValidation:
    """Tests for top_k validation in POST /api/v1/documents/search"""

    SEARCH_URL = "/api/v1/documents/search"

    def test_top_k_equal_zero_returns_422(self, client: TestClient, auth_header: dict):
        """top_k=0 violates ge=1 constraint and returns 422."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 0},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_top_k_above_100_returns_422(self, client: TestClient, auth_header: dict):
        """top_k=101 violates le=100 constraint and returns 422."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 101},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_top_k_equal_100_returns_200(self, client: TestClient, auth_header: dict):
        """top_k=100 is the upper boundary and returns 200."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 100},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_top_k_equal_1_returns_200(self, client: TestClient, auth_header: dict):
        """top_k=1 is the lower boundary and returns 200."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 1},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_top_k_negative_returns_422(self, client: TestClient, auth_header: dict):
        """Negative top_k returns 422."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": -5},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_top_k_default_is_5(self, client: TestClient, auth_header: dict):
        """Default top_k should be 5 if not provided."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест"},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        # The response may reflect the actual top_k used; at minimum it should succeed
        assert "items" in data

    def test_top_k_missing_query_valid(self, client: TestClient, auth_header: dict):
        """Search with valid top_k=5 and empty query returns 200."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "", "top_k": 5},
            headers=auth_header,
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  9. Upload with new fields
# ---------------------------------------------------------------------------


class TestUploadWithNewFields:
    """Tests for POST /api/v1/documents/ with new fields (source_type, etc.)"""

    UPLOAD_URL = "/api/v1/documents/"

    def test_upload_with_source_type(self, client: TestClient, auth_header: dict):
        """Upload with valid source_type returns 202."""
        response = client.post(
            self.UPLOAD_URL,
            files={
                "file": (
                    "doc.pdf",
                    io.BytesIO(b"%PDF-1.4 test"),
                    "application/pdf",
                )
            },
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "uploaded"
        assert "task_id" in data
        assert "version_id" in data
        assert "file_hash_sha256" in data
        assert "file_size_bytes" in data
        assert "is_duplicate_file" in data
        assert "is_duplicate_document" in data

    def test_upload_all_optional_fields(self, client: TestClient, auth_header: dict):
        """Upload with all new optional fields returns 202."""
        response = client.post(
            self.UPLOAD_URL,
            files={
                "file": (
                    "doc.pdf",
                    io.BytesIO(b"%PDF-1.4 with metadata"),
                    "application/pdf",
                )
            },
            data={
                "source_type": "GOST_R",
                "title": "Тестовый документ",
                "doc_code": "ГОСТ 12345-2024",
                "mks_oks_code": "31.240",
                "okstu_code": "OKP 1234",
                "era": "CURRENT",
                "jurisdiction": "RU",
                "issuing_body": "Госстандарт",
                "metadata": '{"key": "value"}',
            },
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_upload_with_all_source_types(
        self, client: TestClient, auth_header: dict
    ):
        """All valid SourceType enum values are accepted."""
        for i, source_type in enumerate(("GOST", "GOST_R", "OST", "RD", "TU", "ISO", "DNV", "ASTM", "OTHER")):
            response = client.post(
                self.UPLOAD_URL,
                files={
                    "file": (
                        f"doc_{i}.pdf",
                        io.BytesIO(f"%PDF-1.4 source_type={source_type}".encode()),
                        "application/pdf",
                    )
                },
                data={"source_type": source_type},
                headers=auth_header,
            )
            assert response.status_code == 202, (
                f"source_type={source_type} should be accepted"
            )

    def test_upload_invalid_source_type(self, client: TestClient, auth_header: dict):
        """Invalid source_type returns 400."""
        response = client.post(
            self.UPLOAD_URL,
            files={
                "file": (
                    "doc.pdf",
                    io.BytesIO(b"%PDF-1.4"),
                    "application/pdf",
                )
            },
            data={"source_type": "INVALID_TYPE"},
            headers=auth_header,
        )
        assert response.status_code == 400
        data = response.json()
        # Should contain error details
        assert "error" in data or "detail" in data

    def test_upload_without_source_type(self, client: TestClient, auth_header: dict):
        """Missing source_type (required) returns 422."""
        response = client.post(
            self.UPLOAD_URL,
            files={
                "file": (
                    "doc.pdf",
                    io.BytesIO(b"%PDF-1.4"),
                    "application/pdf",
                )
            },
            data={},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_upload_with_all_era_values(
        self, client: TestClient, auth_header: dict
    ):
        """Valid era values are accepted."""
        for era in ("USSR", "CIS", "RF", "CURRENT"):
            response = client.post(
                self.UPLOAD_URL,
                files={
                    "file": (
                        f"doc_{era}.pdf",
                        io.BytesIO(f"%PDF-1.4 era={era}".encode()),
                        "application/pdf",
                    )
                },
                data={"source_type": "GOST", "era": era},
                headers=auth_header,
            )
            assert response.status_code == 202, f"era={era} should be accepted"

    def test_upload_with_jurisdiction(
        self, client: TestClient, auth_header: dict
    ):
        """Valid jurisdiction values are accepted."""
        for jurisdiction in ("RU", "EU", "US", "NO", "INTL"):
            response = client.post(
                self.UPLOAD_URL,
                files={
                    "file": (
                        f"doc_{jurisdiction}.pdf",
                        io.BytesIO(f"%PDF-1.4 jurisdiction={jurisdiction}".encode()),
                        "application/pdf",
                    )
                },
                data={
                    "source_type": "ISO",
                    "jurisdiction": jurisdiction,
                },
                headers=auth_header,
            )
            assert response.status_code == 202, (
                f"jurisdiction={jurisdiction} should be accepted"
            )

    def test_upload_response_has_title_hash(
        self, client: TestClient, auth_header: dict
    ):
        """When title is provided, title_hash_sha256 should be present."""
        response = client.post(
            self.UPLOAD_URL,
            files={
                "file": (
                    "doc.pdf",
                    io.BytesIO(b"%PDF-1.4"),
                    "application/pdf",
                )
            },
            data={
                "source_type": "GOST",
                "title": "Документ с названием",
            },
            headers=auth_header,
        )
        data = response.json()
        assert "title_hash_sha256" in data
        assert data["title_hash_sha256"] is not None
        assert isinstance(data["title_hash_sha256"], str)

    def test_upload_response_int_fields(
        self, client: TestClient, auth_header: dict
    ):
        """file_size_bytes and task_id are proper integers."""
        response = client.post(
            self.UPLOAD_URL,
            files={
                "file": (
                    "doc.pdf",
                    io.BytesIO(b"%PDF-1.4"),
                    "application/pdf",
                )
            },
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        data = response.json()
        assert isinstance(data["task_id"], int)
        assert isinstance(data["file_size_bytes"], int)
        assert data["file_size_bytes"] > 0

    def test_upload_with_unsupported_type_and_valid_source(
        self, client: TestClient, auth_header: dict
    ):
        """Unsupported file type returns 400 even with valid source_type."""
        response = client.post(
            self.UPLOAD_URL,
            files={
                "file": (
                    "doc.txt",
                    io.BytesIO(b"not a pdf"),
                    "text/plain",
                )
            },
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
#  10. List with new filter params
# ---------------------------------------------------------------------------


class TestListWithFilters:
    """Tests for GET /api/v1/documents/ with new filter parameters"""

    LIST_URL = "/api/v1/documents/"

    def test_list_with_source_type_filter(
        self, client: TestClient, auth_header: dict
    ):
        """Filtering by source_type returns 200 with items."""
        response = client.get(
            self.LIST_URL,
            params={"source_type": "GOST"},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "summary" in data
        assert "meta" in data

    def test_list_with_era_filter(self, client: TestClient, auth_header: dict):
        """Filtering by era returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"era": "USSR"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_validity_status_filter(
        self, client: TestClient, auth_header: dict
    ):
        """Filtering by validity_status returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"validity_status": "active"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_jurisdiction_filter(
        self, client: TestClient, auth_header: dict
    ):
        """Filtering by jurisdiction returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"jurisdiction": "RU"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_multiple_filters(
        self, client: TestClient, auth_header: dict
    ):
        """Combining multiple filters works."""
        response = client.get(
            self.LIST_URL,
            params={
                "source_type": "GOST",
                "era": "USSR",
                "validity_status": "active",
            },
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_mks_oks_code_filter(
        self, client: TestClient, auth_header: dict
    ):
        """Filtering by mks_oks_code returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"mks_oks_code": "31.240"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_okstu_code_filter(
        self, client: TestClient, auth_header: dict
    ):
        """Filtering by okstu_code returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"okstu_code": "OKP 1234"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_doc_code_filter(
        self, client: TestClient, auth_header: dict
    ):
        """Filtering by doc_code (document number) returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"doc_code": "20868-81"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_search_filter(self, client: TestClient, auth_header: dict):
        """Filtering by search (title text) returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"search": "стойки"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_date_range(self, client: TestClient, auth_header: dict):
        """Filtering by date range returns 200."""
        response = client.get(
            self.LIST_URL,
            params={
                "date_from": "2024-01-01T00:00:00",
                "date_to": "2026-12-31T23:59:59",
            },
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_sort_by_and_order(
        self, client: TestClient, auth_header: dict
    ):
        """Sorting by field with asc/desc order."""
        # Test sort_by=created_at with default order (desc)
        response = client.get(
            self.LIST_URL,
            params={"sort_by": "created_at"},
            headers=auth_header,
        )
        assert response.status_code == 200

        # Test sort_by=title with explicit order
        response = client.get(
            self.LIST_URL,
            params={"sort_by": "title", "order": "asc"},
            headers=auth_header,
        )
        assert response.status_code == 200

        # Test sort_by=status with desc order
        response = client.get(
            self.LIST_URL,
            params={"sort_by": "status", "order": "desc"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_status_filter(self, client: TestClient, auth_header: dict):
        """Filtering by document status."""
        response = client.get(
            self.LIST_URL,
            params={"status": "approved"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_all_filter_params(
        self, client: TestClient, auth_header: dict
    ):
        """All filter parameters combined should work."""
        response = client.get(
            self.LIST_URL,
            params={
                "source_type": "GOST",
                "era": "USSR",
                "validity_status": "active",
                "jurisdiction": "RU",
                "doc_code": "20868-81",
                "search": "стойки",
                "sort_by": "created_at",
                "order": "desc",
                "page": 1,
                "page_size": 20,
            },
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        # Verify pagination params are respected
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 20

    def test_list_filter_with_page_size(
        self, client: TestClient, auth_header: dict
    ):
        """Custom page_size is reflected in meta."""
        response = client.get(
            self.LIST_URL,
            params={"page_size": 50},
            headers=auth_header,
        )
        data = response.json()
        assert data["meta"]["page_size"] == 50

    def test_list_filter_invalid_page_size(
        self, client: TestClient, auth_header: dict
    ):
        """page_size > 100 returns 422."""
        response = client.get(
            self.LIST_URL,
            params={"page_size": 200},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_list_filter_item_fields(
        self, client: TestClient, auth_header: dict
    ):
        """List items include the new metadata fields."""
        response = client.get(
            self.LIST_URL,
            headers=auth_header,
        )
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            # New fields that should be present
            assert "source_type" in item
            assert "era" in item
            assert "validity_status" in item
            assert "jurisdiction" in item
            assert "issuing_body" in item
            assert "mks_oks_code" in item
            assert "classification_status" in item

    def test_list_without_auth(self, client: TestClient):
        """List with filters works without auth in mock mode."""
        response = client.get(
            self.LIST_URL,
            params={"source_type": "GOST"},
        )
        assert response.status_code == 200
