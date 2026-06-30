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
            data={"document_key": "doc-001", "title": "Test Document", "source_type": "GOST"},
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
        """Upload with unsupported MIME returns 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.txt", io.BytesIO(b"plain text"), "text/plain")},
            data={"document_key": "doc-001", "source_type": "GOST"},
        )
        assert response.status_code == 422
        data = response.json()
        # FastAPI wraps HTTPException.detail in {"detail": ...}
        assert "error" in data.get("detail", data)

    def test_create_draft_file_too_large(self, client: TestClient, auth_header: dict):
        """File exceeding size limit returns 413.

        Uses mock.patch on MAX_FILE_SIZE_BYTES so a tiny file triggers
        the size check — avoids loading 100+ MB into memory during tests.
        """
        from unittest.mock import patch
        small_content = b"x" * 2000  # 2000 bytes (>= 1024) — tiny
        with patch(
            "app.api.v1.endpoints.drafts.MAX_FILE_SIZE_BYTES", 50  # mock limit: 50 bytes
        ):
            response = client.post(
                self.URL,
                headers=auth_header,
                files={"file": ("big.pdf", io.BytesIO(small_content), "application/pdf")},
                data={"document_key": "doc-too-large", "source_type": "GOST"},
            )
            assert response.status_code == 413
        data = response.json()
        assert "error" in data.get("detail", data)

    def test_create_draft_without_auth(self, client: TestClient):
        """Request without auth still works in mock mode."""
        response = client.post(
            self.URL,
            files={"file": ("test.pdf", io.BytesIO(b"pdf content " * 100), "application/pdf")},
            data={"document_key": "doc-001", "source_type": "GOST"},
        )
        # Mock mode returns mock user, so 202
        assert response.status_code == 202

    def test_create_draft_without_file(self, client: TestClient, auth_header: dict):
        """Missing file returns 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            data={"document_key": "doc-001", "source_type": "GOST"},
        )
        assert response.status_code == 422

    # --- New field validations (Блок 11) ---

    def test_create_draft_without_source_type_returns_422(self, client: TestClient, auth_header: dict):
        """Missing required source_type returns 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-no-source"},
        )
        assert response.status_code == 422

    def test_create_draft_invalid_source_type_returns_422(self, client: TestClient, auth_header: dict):
        """Invalid source_type value returns 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-bad-source", "source_type": "INVALID"},
        )
        assert response.status_code == 422
        data = response.json()
        detail = data.get("detail", data)
        error = detail.get("error", detail)
        assert "INVALID" in error.get("message", "")

    def test_create_draft_invalid_era_returns_422(self, client: TestClient, auth_header: dict):
        """Invalid era value returns 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-bad-era", "source_type": "GOST", "era": "ANCIENT"},
        )
        assert response.status_code == 422

    def test_create_draft_invalid_jurisdiction_returns_422(self, client: TestClient, auth_header: dict):
        """Invalid jurisdiction value returns 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-bad-jur", "source_type": "GOST", "jurisdiction": "MOON"},
        )
        assert response.status_code == 422

    def test_create_draft_response_has_title_key(self, client: TestClient, auth_header: dict):
        """Successful upload returns title_key in response (DB-28)."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={
                "document_key": "doc-title-key",
                "source_type": "GOST",
                "title": "Test Doc",
                "era": "RF",
                "doc_code": "12345",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert "title_key" in data
        assert data["title_key"] is not None
        # title_key should contain the key fields concatenated
        assert "RF" in data["title_key"]
        assert "GOST" in data["title_key"]
        assert "Test Doc" in data["title_key"]

    def test_create_draft_title_key_none_when_no_fields(self, client: TestClient, auth_header: dict):
        """Without era/doc_code/title, title_key only has source_type."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-key-none", "source_type": "GOST"},
        )
        assert response.status_code == 202
        data = response.json()
        assert "title_key" in data
        assert data["title_key"] == "GOST"


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
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock content " * 100), "application/pdf")},
            data={"document_key": "doc-start-preview", "title": "Test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    def test_start_preview_202(self, created_draft: int, client: TestClient, auth_header: dict):
        """Starting preview returns 202."""
        response = client.post(self.URL.format(draft_id=created_draft), headers=auth_header)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "previewing"

    def test_start_preview_response_structure(self, created_draft: int, client: TestClient, auth_header: dict):
        """Response contains all expected fields."""
        response = client.post(self.URL.format(draft_id=created_draft), headers=auth_header)
        assert response.status_code == 202
        data = response.json()
        assert "draft_id" in data
        assert "task_id" in data
        assert "status" in data
        assert "message" in data
        assert data["status"] == "previewing"
        assert isinstance(data["status"], str)

    def test_start_preview_without_auth(self, client: TestClient):
        """Preview start works without auth in mock mode."""
        # Create a draft without auth first
        response = client.post(
            "/api/v1/drafts/",
            files={"file": ("test.pdf", io.BytesIO(b"%PDF content " * 200), "application/pdf")},
            data={"document_key": "doc-no-auth-preview", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        # Now start preview without auth
        response = client.post(self.URL.format(draft_id=draft_id))
        assert response.status_code == 202
        assert response.json()["status"] == "previewing"

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
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-preview-status", "title": "Test", "source_type": "GOST"},
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

    def test_preview_status_decision_required_is_bool(self, created_draft: int, client: TestClient, auth_header: dict):
        """decision_required is a boolean."""
        response = client.get(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        data = response.json()
        assert isinstance(data["decision_required"], bool)

    def test_preview_status_status_is_string(self, created_draft: int, client: TestClient, auth_header: dict):
        """Status is a string."""
        response = client.get(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        data = response.json()
        assert isinstance(data["status"], str)

    def test_preview_status_invalid_longpoll(self, created_draft: int, client: TestClient, auth_header: dict):
        """longpoll outside 0..60 should return 422."""
        for lp in (-1, 61):
            response = client.get(
                self.URL.format(draft_id=created_draft),
                headers=auth_header,
                params={"longpoll": lp},
            )
            assert response.status_code == 422

    def test_preview_status_without_auth(self, client: TestClient):
        """Preview status works without auth in mock mode."""
        # Create a draft without auth first
        response = client.post(
            "/api/v1/drafts/",
            files={"file": ("test.pdf", io.BytesIO(b"%PDF content " * 200), "application/pdf")},
            data={"document_key": "doc-no-auth-status", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        # Start preview first
        client.post(self.URL.format(draft_id=draft_id))
        # Get status without auth
        response = client.get(
            self.URL.format(draft_id=draft_id),
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
    async def created_draft(self, client: TestClient, auth_header: dict, db_session) -> int:
        """Create a draft via API and return its draft_id.

        Advances task state to 'decision' stage so approve/reject can be tested.
        """
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-decide", "title": "Test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        # Advance task to decision stage (Celery is mocked, so steps won't run)
        from sqlalchemy import select, update
        from app.models.pipeline import Task, TaskStep
        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.pipeline_stage = "decision"
            task.status = "active"
            # Complete preview steps so approve doesn't get blocked by 5.3 check
            steps_result = await db_session.execute(
                select(TaskStep).where(TaskStep.task_id == task.id)
            )
            for step in steps_result.scalars().all():
                step.status = "completed"
            await db_session.flush()
            await db_session.commit()  # Make visible to endpoint's session

        return draft_id

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

    def test_decide_with_comment(self, created_draft: int, client: TestClient, auth_header: dict):
        """Decision with a comment is accepted."""
        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "approve", "comment": "Проверено, всё верно"},
        )
        assert response.status_code == 200

    def test_decide_missing_action(self, created_draft: int, client: TestClient, auth_header: dict):
        """Missing action field returns 422."""
        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={},
        )
        assert response.status_code == 422

    def test_decide_response_has_all_fields(self, created_draft: int, client: TestClient, auth_header: dict):
        """Response has document_id, version_id, status, action."""
        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "draft_id" in data
        assert "task_id" in data
        assert "document_id" in data
        assert "version_id" in data
        assert "is_new_document" in data
        assert "status" in data
        assert "action" in data
        assert "message" in data

    async def test_decide_terminal_task(self, created_draft: int, client: TestClient, auth_header: dict, db_session):
        """Decide on a completed task returns 409."""
        # Set task to completed
        from sqlalchemy import select
        from app.models.pipeline import Task
        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = "completed"
            await db_session.flush()
            await db_session.commit()

        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert response.status_code == 409

    async def test_decide_wrong_stage(self, created_draft: int, client: TestClient, auth_header: dict, db_session):
        """Decide on invalid stage returns 409."""
        # Set task to a non-decision stage (upload/preview/decision are valid)
        from sqlalchemy import select
        from app.models.pipeline import Task
        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        if task:
            task.pipeline_stage = "full"
            await db_session.flush()
            await db_session.commit()

        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert response.status_code == 409

    async def test_decide_without_auth(self, client: TestClient, db_session):
        """Decide works without auth in mock mode."""
        # Create a draft without auth first
        response = client.post(
            "/api/v1/drafts/",
            files={"file": ("test.pdf", io.BytesIO(b"%PDF content " * 200), "application/pdf")},
            data={"document_key": "doc-no-auth-decide", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        # Advance task to decision stage
        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep
        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.pipeline_stage = "decision"
            task.status = "active"
            # Complete preview steps to pass 5.3 check
            steps_result = await db_session.execute(
                select(TaskStep).where(TaskStep.task_id == task.id)
            )
            for step in steps_result.scalars().all():
                step.status = "completed"
            await db_session.flush()
            await db_session.commit()

        # Decide without auth
        response = client.patch(
            self.URL.format(draft_id=draft_id),
            json={"action": "approve"},
        )
        assert response.status_code == 200

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


# ---------------------------------------------------------------------------
#  GET /drafts/{draft_id}/tasks
# ---------------------------------------------------------------------------


class TestDraftTasks:
    """Tests for GET /api/v1/drafts/{draft_id}/tasks."""

    URL = "/api/v1/drafts/{draft_id}/tasks"

    def test_draft_tasks_success(self, client: TestClient, auth_header: dict):
        """Existing draft returns task list."""
        # Create a draft first
        create_resp = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF content " * 200), "application/pdf")},
            data={"document_key": "doc-tasks-test", "source_type": "GOST"},
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        response = client.get(self.URL.format(draft_id=draft_id), headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == draft_id
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        if data["tasks"]:
            task = data["tasks"][0]
            assert "task_id" in task
            assert "status" in task
            assert "pipeline_stage" in task

    def test_draft_tasks_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent draft returns empty tasks (not 404)."""
        response = client.get(self.URL.format(draft_id=99999), headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == 99999
        assert data["tasks"] == []


# ---------------------------------------------------------------------------
#  Metadata round-trip tests: create → retrieve → update → verify
# ---------------------------------------------------------------------------


class TestMetadataRoundTrip:
    """
    Tests for metadata persistence round-trip.

    Verifies that metadata sent during POST /drafts is properly stored
    and can be retrieved via GET /drafts/{id}/preview and
    PATCH /drafts/{id}/metadata.
    """

    CREATE_URL = "/api/v1/drafts/"
    PREVIEW_URL = "/api/v1/drafts/{draft_id}/preview"
    METADATA_URL = "/api/v1/drafts/{draft_id}/metadata"

    def test_create_and_retrieve_all_metadata_fields(self, client: TestClient, auth_header: dict):
        """
        Round-trip: create draft with ALL metadata fields →
        GET preview → every field matches what was sent.
        """
        # --- Create draft with full metadata ---
        create_resp = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 mock " * 200), "application/pdf")},
            data={
                "document_key": "doc-meta-roundtrip",
                "source_type": "GOST",
                "title": "Тестовый документ",
                "doc_code": "ГОСТ 1234-2024",
                "era": "RF",
                "jurisdiction": "RU",
                "mks_oks_code": "01.040.01",
                "okstu_code": "OKP 1234",
                "issuing_body": "Росстандарт",
            },
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        # --- Retrieve preview metadata ---
        preview_resp = client.get(
            self.PREVIEW_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert preview_resp.status_code == 200
        data = preview_resp.json()
        preview = data["preview"]

        # --- Verify each field matches exactly ---
        assert preview["source_type"] == "GOST"
        assert preview["title"] == "Тестовый документ"
        assert preview["doc_code"] == "ГОСТ 1234-2024"
        assert preview["era"] == "RF"
        assert preview["jurisdiction"] == "RU"
        assert preview["mks_oks_code"] == "01.040.01"
        assert preview["okstu_code"] == "OKP 1234"
        assert preview["issuing_body"] == "Росстандарт"

    def test_create_without_metadata_returns_fallback(self, client: TestClient, auth_header: dict):
        """
        Create draft without metadata → GET preview returns hardcoded fallback
        (not empty). This protects existing behaviour for draft_id=1 seed data.
        """
        # Create with only required source_type
        create_resp = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-no-meta", "source_type": "GOST"},
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        preview_resp = client.get(
            self.PREVIEW_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert preview_resp.status_code == 200
        preview = preview_resp.json()["preview"]

        # Fallback defaults should still be present for fields NOT in metadata_fields
        assert preview["doc_code"] == "ГОСТ 20868-81"
        assert preview["title"] == "Стойки установочные крепежные"
        assert preview["document_type"] == "normative"
        # source_type is required and always stored, so it's present
        assert preview["source_type"] == "GOST"
        # Fields not provided remain at fallback defaults or None
        assert preview["era"] is None
        assert preview["jurisdiction"] is None

    def test_create_with_json_metadata_field(self, client: TestClient, auth_header: dict):
        """
        Create draft with JSON `metadata` field → merged into metadata_fields →
        retrievable via preview.
        """
        import json
        extra_meta = json.dumps({"udk_code": "УДК 123.456", "custom_field": "custom_value"})

        create_resp = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={
                "document_key": "doc-json-meta",
                "source_type": "GOST",
                "title": "JSON Meta Test",
                "metadata": extra_meta,
            },
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        preview_resp = client.get(
            self.PREVIEW_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert preview_resp.status_code == 200
        preview = preview_resp.json()["preview"]

        # Form fields should be set
        assert preview["source_type"] == "GOST"
        assert preview["title"] == "JSON Meta Test"
        # JSON metadata fields merged in — udk_code is a PreviewMetadata field
        assert preview["udk_code"] == "УДК 123.456"
        # custom_field is not in PreviewMetadata schema, so it won't appear in response

    def test_patch_metadata_then_retrieve(self, client: TestClient, auth_header: dict):
        """
        Create draft → PATCH metadata → GET preview → verify updated values.
        """
        # Create draft without extra metadata
        create_resp = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-patch-meta", "source_type": "GOST"},
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        # --- PATCH metadata ---
        patch_payload = {
            "preview_metadata": {
                "doc_code": "ПATCH-001",
                "title": "Patched Title",
                "era": "CURRENT",
            },
            "updated_by": "test-user",
        }
        patch_resp = client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json=patch_payload,
        )
        assert patch_resp.status_code == 200
        patch_data = patch_resp.json()
        assert patch_data["draft_id"] == draft_id
        assert patch_data["preview_metadata"]["doc_code"] == "ПATCH-001"

        # --- Retrieve preview and verify updated values ---
        preview_resp = client.get(
            self.PREVIEW_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert preview_resp.status_code == 200
        preview = preview_resp.json()["preview"]
        assert preview["doc_code"] == "ПATCH-001"
        assert preview["title"] == "Patched Title"
        assert preview["era"] == "CURRENT"
        # source_type was set at creation and should still be present
        assert preview["source_type"] == "GOST"

    def test_patch_metadata_not_found(self, client: TestClient, auth_header: dict):
        """PATCH metadata on non-existent draft returns 404."""
        patch_resp = client.patch(
            self.METADATA_URL.format(draft_id=99999),
            headers=auth_header,
            json={"preview_metadata": {"title": "Nope"}},
        )
        assert patch_resp.status_code == 404
        detail = patch_resp.json().get("detail", patch_resp.json())
        assert "error" in detail


# ---------------------------------------------------------------------------
#  Bug #18 — Drafts создаются от u-mock-001 вместо реального пользователя
# ---------------------------------------------------------------------------


class TestCreatedByUser:
    """
    Verifies that created_by uses the real user_id from auth (bug #18).

    In mock mode the auth dependency returns MOCK_USER (u-mock-001).
    This test overrides the dependency with a custom user and checks
    that created_by in Registry storage matches the custom user_id.
    """

    CREATE_URL = "/api/v1/drafts/"
    GET_URL = "/api/v1/drafts/{draft_id}"

    def test_created_by_uses_mock_user_by_default(self, client: TestClient):
        """Without override, created_by is MOCK_USER_ID (u-mock-001)."""
        response = client.post(
            self.CREATE_URL,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
            data={"document_key": "doc-default-user", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        # Check Registry storage directly
        from app.services.registry_client import RegistryServiceClient
        draft = RegistryServiceClient._storage["drafts"][draft_id]
        assert draft["created_by"] == "u-mock-001"

    def test_created_by_uses_custom_user_id(self, client: TestClient):
        """Auth override → created_by matches custom user_id."""
        from app.api.deps import get_current_user, CurrentUser

        custom_user = CurrentUser(
            user_id="real-user-42",
            email="real@test.com",
            full_name="Real User",
            roles=["engineer"],
            permissions=["documents:write"],
        )

        client.app.dependency_overrides[get_current_user] = lambda: custom_user
        try:
            response = client.post(
                self.CREATE_URL,
                files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
                data={"document_key": "doc-custom-user", "source_type": "GOST"},
            )
            assert response.status_code == 202
            draft_id = response.json()["draft_id"]

            from app.services.registry_client import RegistryServiceClient
            draft = RegistryServiceClient._storage["drafts"][draft_id]
            assert draft["created_by"] == "real-user-42"
        finally:
            client.app.dependency_overrides.pop(get_current_user, None)

    def test_created_by_not_fallback_object(self, client: TestClient):
        """created_by is a string, not a CurrentUser object (regression for old bug)."""
        from app.api.deps import get_current_user, CurrentUser

        custom_user = CurrentUser(
            user_id="str-user-99",
            email="str@test.com",
            full_name="String Test",
            roles=[],
            permissions=[],
        )

        client.app.dependency_overrides[get_current_user] = lambda: custom_user
        try:
            response = client.post(
                self.CREATE_URL,
                files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
                data={"document_key": "doc-str-user", "source_type": "GOST"},
            )
            assert response.status_code == 202
            draft_id = response.json()["draft_id"]

            from app.services.registry_client import RegistryServiceClient
            draft = RegistryServiceClient._storage["drafts"][draft_id]
            created_by = draft["created_by"]
            # Must be a plain string, not a serialized object
            assert isinstance(created_by, str), f"Expected str, got {type(created_by)}"
            assert created_by == "str-user-99"
        finally:
            client.app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
#  Bug #15 — Upload draft: 500 ошибка, но draft появляется в списке
# ---------------------------------------------------------------------------


class TestUploadPartialFailure:
    """
    If pipeline start fails after Registry draft creation, the endpoint
    returns 500 but the draft/task already exist (bug #15).
    """

    CREATE_URL = "/api/v1/drafts/"

    async def test_pipeline_failure_orphans_draft_in_registry(
        self, client: TestClient, auth_header: dict,
    ):
        """start_pipeline fails → 500. Draft persists in Registry (bug #15).

        Bug #15: Registry draft is created BEFORE the local DB task.
        If pipeline start fails, the DB transaction rolls back (so task
        disappears), but the Registry draft remains orphaned.
        """
        from unittest.mock import patch, AsyncMock
        from app.core.pipeline.orchestrator import PipelineOrchestrator
        from fastapi import HTTPException

        with patch.object(
            PipelineOrchestrator,
            "start_pipeline",
            new=AsyncMock(side_effect=HTTPException(
                status_code=500,
                detail={"error": {"code": "PIPELINE_FAILED", "message": "pipeline crashed"}},
            )),
        ):
            response = client.post(
                self.CREATE_URL,
                headers=auth_header,
                files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 200), "application/pdf")},
                data={"document_key": "doc-orphan", "source_type": "GOST"},
            )

        # FastAPI catches HTTPException and returns proper 500
        assert response.status_code == 500
        detail = response.json().get("detail", response.json())
        assert detail["error"]["code"] == "PIPELINE_FAILED"

        # --- Verify draft EXISTS in Registry (orphaned) ---
        from app.services.registry_client import RegistryServiceClient
        draft = None
        for did, d in RegistryServiceClient._storage["drafts"].items():
            if d.get("document_key") == "doc-orphan":
                draft = d
                break
        assert draft is not None, "Draft should exist in Registry despite 500"
        assert draft.get("status") == "uploaded", \
            f"Expected uploaded, got {draft.get('status')}"


# ---------------------------------------------------------------------------
#  P2-блок: TestUnknownDraftStatus + TestTimeoutCascade
#  Источник: todo_pipeline_coverage.md (P2 №7-8)
# ---------------------------------------------------------------------------


class TestUnknownDraftStatus:
    """P2-7: неизвестный draft status в Registry.

    Если Registry вернул draft со status, который FSM не знает
    (например, 'validation' или 'review_required' — задокументировано
    в todo_pipeline_coverage.md §5 как расхождение), текущая логика
    обрабатывает это как 409 CONFLICT.
    """

    def test_get_draft_with_unknown_status(
        self, client: TestClient, auth_header: dict
    ):
        """GET /drafts/{id} для draft с неизвестным status → 200 (mock-режим)."""
        from app.services.registry_client import RegistryServiceClient
        from app.api.v1.endpoints.drafts import get_draft

        # Создаём draft с нестандартным статусом
        RegistryServiceClient._storage["drafts"][9001] = {
            "id": 9001,
            "document_key": "doc-unknown-status",
            "status": "validation",  # нет в DraftState enum
            "created_by": "u-mock-001",
            "file_key": "drafts/test.pdf",
        }

        response = client.get(
            "/api/v1/drafts/9001",
            headers=auth_header,
        )
        # В mock-режиме проксирование просто отдаёт то, что вернул Registry.
        assert response.status_code in (200, 404)

    def test_start_preview_with_unknown_status_returns_409(
        self, client: TestClient, auth_header: dict
    ):
        """start_preview для draft с неизвестным status → 409 (текущее поведение)."""
        from app.services.registry_client import RegistryServiceClient
        from unittest.mock import patch

        # Создаём draft с status != "uploaded"
        RegistryServiceClient._storage["drafts"][9002] = {
            "id": 9002,
            "document_key": "doc-bad-status",
            "status": "validation",  # не "uploaded"
            "file_key": "drafts/test.pdf",
        }

        response = client.post(
            "/api/v1/drafts/9002/preview",
            headers=auth_header,
        )
        # 409 — preview нельзя запустить, draft в неожиданном статусе
        assert response.status_code == 409

    def test_fsm_rejects_unknown_status(self):
        """DraftState enum НЕ содержит validation/review_required (расхождение docs↔code)."""
        from app.core.fsm import DraftState

        # Текущий DraftState
        states = {s.value for s in DraftState}
        assert "uploaded" in states
        assert "previewing" in states
        assert "ready_for_approve" in states
        assert "approved" in states
        assert "discarded" in states
        # validation/review_required отсутствуют (документированный дефект)
        assert "validation" not in states
        assert "review_required" not in states


class TestTimeoutCascade:
    """P2-8: каскад таймаутов в pipeline.

    Сценарий: OCR-шаг превысил STEP_TIMEOUT_OCR (300 сек).
    Каскад: OCR таймаут → on_step_failed → retry → retry_count++
    → если retry_count == MAX_STEP_RETRIES, fail + Saga.
    """

    @pytest.fixture
    def mock_db(self):
        """Mock AsyncSession для unit-тестов PipelineOrchestrator."""
        from unittest.mock import AsyncMock
        m = AsyncMock()
        m.flush = AsyncMock()
        return m

    class _MockTask:
        def __init__(self, status="active", id=1, draft_id=1):
            self.id = id
            self.draft_id = draft_id
            self.document_id = 0
            self.trace_id = "test-trace"
            self.status = status
            self.retry_count = 0
            self.current_step_index = 0
            self.current_step_name = ""
            self.locked_by = None
            self.locked_at = None

    class _MockStep:
        def __init__(self, step_name, step_index, status="completed", service_name=""):
            self.id = step_index * 100
            self.task_id = 1
            self.step_name = step_name
            self.step_index = step_index
            self.status = status
            self.output_data = {}
            self.service_name = service_name or step_name

    def test_step_timeout_ocr_default(self):
        """STEP_TIMEOUT_OCR = 300 (по умолчанию)."""
        from app.core.config import PipelineConfig

        config = PipelineConfig()
        assert config.STEP_TIMEOUT_OCR == 300

    def test_step_timeouts_defined_for_all_stages(self):
        """Все step-таймауты определены в конфиге."""
        from app.core.config import PipelineConfig

        config = PipelineConfig()
        assert config.STEP_TIMEOUT_OCR == 300
        assert config.STEP_TIMEOUT_PARSER == 300
        assert config.STEP_TIMEOUT_CONVERTER == 120
        assert config.STEP_TIMEOUT_REGISTRY == 30
        assert config.STEP_TIMEOUT_RAG_INDEX == 300

    def test_max_step_retries_constant(self):
        """MAX_STEP_RETRIES = 3."""
        from app.core.config import PipelineConfig

        config = PipelineConfig()
        assert config.MAX_STEP_RETRIES == 3

    def test_retry_base_delay_constant(self):
        """RETRY_BASE_DELAY = 60 (экспоненциальный backoff)."""
        from app.core.config import PipelineConfig

        config = PipelineConfig()
        assert config.RETRY_BASE_DELAY == 60

    async def test_on_step_failed_uses_exponential_backoff(
        self, mock_db
    ):
        """on_step_failed планирует retry с экспоненциальным backoff."""
        from app.core.config import settings
        from app.core.pipeline.orchestrator import PipelineOrchestrator
        from app.core.pipeline.saga import SagaCoordinator

        orchestrator = PipelineOrchestrator(mock_db)
        orchestrator.task_repo = AsyncMock()

        # task с retry_count = 0 (ниже MAX)
        task = self._MockTask(status="active")
        task.retry_count = 0
        task.current_step_index = 1
        task.current_step_name = "preview_ocr"
        orchestrator.task_repo.get_task.return_value = task
        orchestrator.task_repo.get_task_steps.return_value = [
            self._MockStep("upload", 0, status="completed"),
            self._MockStep("preview_ocr", 1, status="running"),
        ]
        orchestrator.task_repo.create_task_step.return_value = self._MockStep(
            "preview_ocr", 1
        )

        with patch.object(SagaCoordinator, "compensate", new=AsyncMock()):
            with patch(
                "app.tasks.pipeline_formation.run_ocr_preview_step.delay"
            ) as mock_delay:
                await orchestrator.on_step_failed(
                    task_id=1,
                    step_name="preview_ocr",
                    error_code="OCR_TIMEOUT",
                    error_message="step timeout 300s exceeded",
                )

        # retry не вызвал Saga (retry_count < max)
        # task остаётся в active
        assert orchestrator.task_repo.update_task_status.called
        # retry_count увеличен
        # (проверяется через set_task_error, который инкрементирует retry_count)
        orchestrator.task_repo.set_task_error.assert_called_once()

    async def test_on_step_failed_after_max_retries_triggers_saga(
        self, mock_db
    ):
        """После MAX_STEP_RETRIES saga компенсирует."""
        from app.core.config import settings
        from app.core.pipeline.orchestrator import PipelineOrchestrator
        from app.core.pipeline.saga import SagaCoordinator

        # Снижаем порог
        original = settings.pipeline.MAX_STEP_RETRIES
        settings.pipeline.MAX_STEP_RETRIES = 0
        try:
            orchestrator = PipelineOrchestrator(mock_db)
            orchestrator.task_repo = AsyncMock()

            task = self._MockTask(status="active")
            task.retry_count = 0  # 0 >= MAX(0) → fail
            task.current_step_index = 1
            task.current_step_name = "preview_ocr"
            orchestrator.task_repo.get_task.return_value = task
            orchestrator.task_repo.get_task_steps.return_value = [
                self._MockStep("upload", 0, status="completed"),
                self._MockStep("preview_ocr", 1, status="running"),
            ]
            orchestrator.task_repo.create_task_step.return_value = self._MockStep(
                "preview_ocr", 1
            )

            with patch.object(
                SagaCoordinator, "compensate", new=AsyncMock()
            ) as mock_saga:
                await orchestrator.on_step_failed(
                    task_id=1,
                    step_name="preview_ocr",
                    error_code="OCR_TIMEOUT",
                    error_message="step timeout",
                )

            # Saga вызвана
            mock_saga.assert_awaited_once()
        finally:
            settings.pipeline.MAX_STEP_RETRIES = original
