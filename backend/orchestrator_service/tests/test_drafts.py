"""
Tests for Drafts API endpoints.

Covers all /api/v1/drafts endpoints:
  - POST /drafts — upload file & create draft
  - GET /drafts — list drafts
  - GET /drafts/{draft_id} — draft detail
  - GET /drafts/{draft_id}/preview — preview metadata
  - POST /drafts/{draft_id}/preview — start preview
  - GET /drafts/{draft_id}/preview/status — preview status (with longpoll)
  - PATCH /drafts/{draft_id}/decide — approve / reject
  - DELETE /drafts/{draft_id} — delete draft

NOTE: Runs in mock mode (all external services return mock data).
"""

import io
from datetime import datetime

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
#  POST /drafts
# ---------------------------------------------------------------------------


class TestCreateDraft:
    """Tests for POST /api/v1/drafts."""

    URL = "/api/v1/drafts/"

    def test_create_draft_success(self, client: TestClient, auth_header: dict):
        """Successful upload returns 202 with expected fields."""
        file_content = b"%PDF-1.4 mock pdf content " * 100
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
            data={"document_key": "doc-001", "title": "Test Document"},
        )
        assert response.status_code == 202
        data = response.json()
        assert "draft_id" in data
        assert "task_id" in data
        assert data["status"] == "uploaded"
        assert "file_hash_sha256" in data
        assert "file_size_bytes" in data
        assert data["file_size_bytes"] == len(file_content)
        assert "is_duplicate_file" in data
        assert "is_duplicate_document" in data
        assert "title_hash_sha256" in data
        assert "created_at" in data

    def test_create_draft_invalid_mime(self, client: TestClient, auth_header: dict):
        """Upload with unsupported MIME returns 400."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.txt", io.BytesIO(b"plain text"), "text/plain")},
            data={"document_key": "doc-001"},
        )
        assert response.status_code == 400
        data = response.json()
        # FastAPI wraps HTTPException.detail in {"detail": ...}
        assert "error" in data.get("detail", data)

    def test_create_draft_file_too_large(self, client: TestClient, auth_header: dict):
        """File exceeding size limit returns 413.

        Uses mock.patch on MAX_FILE_SIZE_BYTES so a tiny file triggers
        the size check — avoids loading 100+ MB into memory during tests.
        """
        from unittest.mock import patch
        small_content = b"x" * 100  # 100 bytes — tiny
        with patch(
            "app.api.v1.endpoints.drafts.MAX_FILE_SIZE_BYTES", 50  # mock limit: 50 bytes
        ):
            response = client.post(
                self.URL,
                headers=auth_header,
                files={"file": ("big.pdf", io.BytesIO(small_content), "application/pdf")},
                data={"document_key": "doc-too-large"},
            )
        assert response.status_code == 413
        data = response.json()
        assert "error" in data.get("detail", data)

    def test_create_draft_without_auth(self, client: TestClient):
        """Request without auth still works in mock mode."""
        response = client.post(
            self.URL,
            files={"file": ("test.pdf", io.BytesIO(b"pdf content"), "application/pdf")},
            data={"document_key": "doc-001"},
        )
        # Mock mode returns mock user, so 202
        assert response.status_code == 202

    def test_create_draft_without_file(self, client: TestClient, auth_header: dict):
        """Missing file returns 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            data={"document_key": "doc-001"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
#  GET /drafts
# ---------------------------------------------------------------------------


class TestListDrafts:
    """Tests for GET /api/v1/drafts."""

    URL = "/api/v1/drafts/"

    def test_list_drafts_default(self, client: TestClient, auth_header: dict):
        """List drafts returns paginated response."""
        response = client.get(self.URL, headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_list_drafts_with_filters(self, client: TestClient, auth_header: dict):
        """List drafts with status and document_key filters."""
        response = client.get(
            self.URL,
            headers=auth_header,
            params={"status": "uploaded", "document_key": "doc-001", "page": 1, "page_size": 20},
        )
        assert response.status_code == 200

    def test_list_drafts_invalid_page(self, client: TestClient, auth_header: dict):
        """Negative page returns 422."""
        response = client.get(
            self.URL,
            headers=auth_header,
            params={"page": -1},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
#  GET /drafts/{draft_id}
# ---------------------------------------------------------------------------


class TestGetDraft:
    """Tests for GET /api/v1/drafts/{draft_id}."""

    URL = "/api/v1/drafts/{draft_id}"

    def test_get_draft_found(self, client: TestClient, auth_header: dict):
        """Existing draft returns full info."""
        response = client.get(self.URL.format(draft_id=1), headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == 1
        assert "status" in data
        assert "document_key" in data

    def test_get_draft_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent draft returns 404.

        In mock mode, RegistryServiceClient raises for draft_id >= 99999.
        """
        response = client.get(self.URL.format(draft_id=99999), headers=auth_header)
        assert response.status_code == 404
        data = response.json()
        assert "error" in data.get("detail", data)


# ---------------------------------------------------------------------------
#  GET /drafts/{draft_id}/preview
# ---------------------------------------------------------------------------


class TestGetDraftPreview:
    """Tests for GET /api/v1/drafts/{draft_id}/preview."""

    URL = "/api/v1/drafts/{draft_id}/preview"

    def test_get_preview_metadata(self, client: TestClient, auth_header: dict):
        """Preview metadata endpoint returns structure."""
        response = client.get(self.URL.format(draft_id=1), headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == 1
        assert "preview" in data
        preview = data["preview"]
        assert any(k in preview for k in ("doc_code", "title", "document_type"))

    def test_get_preview_not_found(self, client: TestClient, auth_header: dict):
        """Preview for non-existent draft returns 404."""
        response = client.get(self.URL.format(draft_id=99999), headers=auth_header)
        assert response.status_code == 404
        data = response.json()
        assert "error" in data.get("detail", data)


# ---------------------------------------------------------------------------
#  POST /drafts/{draft_id}/preview
# ---------------------------------------------------------------------------


class TestStartPreview:
    """Tests for POST /api/v1/drafts/{draft_id}/preview."""

    URL = "/api/v1/drafts/{draft_id}/preview"

    @pytest.fixture
    def created_draft(self, client: TestClient, auth_header: dict) -> int:
        """Create a draft via API and return its draft_id."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock content"), "application/pdf")},
            data={"document_key": "doc-start-preview", "title": "Test"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    def test_start_preview_202(self, created_draft: int, client: TestClient, auth_header: dict):
        """Starting preview returns 202."""
        response = client.post(self.URL.format(draft_id=created_draft), headers=auth_header)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "previewing"

    def test_start_preview_not_found(self, client: TestClient, auth_header: dict):
        """Preview for non-existent draft returns 404."""
        response = client.post(self.URL.format(draft_id=99999), headers=auth_header)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
#  GET /drafts/{draft_id}/preview/status
# ---------------------------------------------------------------------------


class TestPreviewStatus:
    """Tests for GET /api/v1/drafts/{draft_id}/preview/status."""

    URL = "/api/v1/drafts/{draft_id}/preview/status"

    @pytest.fixture
    def created_draft(self, client: TestClient, auth_header: dict) -> int:
        """Create a draft via API and return its draft_id."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock"), "application/pdf")},
            data={"document_key": "doc-preview-status", "title": "Test"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    def test_preview_status_structure(self, created_draft: int, client: TestClient, auth_header: dict):
        """Status response has all required fields.

        Uses longpoll=0 to avoid waiting (default is 15s).
        """
        response = client.get(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert "draft_id" in data
        assert "task_id" in data
        assert "status" in data
        assert "progress_percent" in data
        assert "preview" in data
        assert "decision_required" in data

    def test_preview_status_with_longpoll(self, created_draft: int, client: TestClient, auth_header: dict):
        """Longpoll parameter is accepted (0-60).

        Uses longpoll=0 (no wait) for fast test execution.
        """
        response = client.get(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        assert response.status_code == 200

    def test_preview_status_longpoll_zero(self, created_draft: int, client: TestClient, auth_header: dict):
        """longpoll=0 returns immediately."""
        response = client.get(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        assert response.status_code == 200

    def test_preview_status_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent draft returns 404."""
        response = client.get(
            self.URL.format(draft_id=99999),
            headers=auth_header,
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
#  PATCH /drafts/{draft_id}/decide
# ---------------------------------------------------------------------------


class TestDecideDraft:
    """Tests for PATCH /api/v1/drafts/{draft_id}/decide."""

    URL = "/api/v1/drafts/{draft_id}/decide"

    @pytest.fixture
    def created_draft(self, client: TestClient, auth_header: dict) -> int:
        """Create a draft via API and return its draft_id."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock"), "application/pdf")},
            data={"document_key": "doc-decide", "title": "Test"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    def test_approve_draft(self, created_draft: int, client: TestClient, auth_header: dict):
        """Approve action returns success."""
        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "approve"
        assert data["status"] == "proceeding"

    def test_reject_draft(self, created_draft: int, client: TestClient, auth_header: dict):
        """Reject action returns discarded status."""
        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "reject", "comment": "Not needed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "reject"
        assert data["status"] == "discarded"

    def test_decide_invalid_action(self, created_draft: int, client: TestClient, auth_header: dict):
        """Unknown action returns 400."""
        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "invalid_action"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data.get("detail", data)

    def test_decide_draft_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent draft for decision returns 404."""
        response = client.patch(
            self.URL.format(draft_id=99999),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
#  DELETE /drafts/{draft_id}
# ---------------------------------------------------------------------------


class TestDeleteDraft:
    """Tests for DELETE /api/v1/drafts/{draft_id}."""

    URL = "/api/v1/drafts/{draft_id}"

    def test_delete_draft_success(self, client: TestClient, auth_header: dict):
        """Successful deletion returns 204."""
        response = client.delete(self.URL.format(draft_id=1), headers=auth_header)
        assert response.status_code == 204

    def test_delete_draft_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent draft returns 404.

        In mock mode, RegistryServiceClient raises for draft_id >= 99999.
        """
        response = client.delete(self.URL.format(draft_id=99999), headers=auth_header)
        assert response.status_code == 404
        data = response.json()
        assert "error" in data.get("detail", data)
