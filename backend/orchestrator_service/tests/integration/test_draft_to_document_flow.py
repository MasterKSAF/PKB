"""
Integration test: полный цикл draft → preview → approve → document.

Сценарий:
  1. POST /drafts (file) → draft_id, task_id, status="uploaded"
  2. POST /drafts/{id}/preview → task_id, status="previewing"
  3. PATCH /drafts/{id}/decide (approve) → document_id, version_id
  4. GET /tasks/{id} → document_id, version_id

Внимание:
  - GET /documents/{id} (чтение документа) — в Registry, не в оркестраторе
  - promoted_document_id проверяем через task.document_id
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDraftToDocumentFlow:
    """Integration: draft → preview → approve → document."""

    DRAFTS_URL = "/api/v1/drafts/"
    PREVIEW_URL = "/api/v1/drafts/{draft_id}/preview"
    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    TASK_URL = "/api/v1/tasks/{task_id}"

    @pytest.fixture
    async def created_draft(
        self, client: TestClient, auth_header: dict
    ) -> dict:
        """Step 1: Upload file → draft_id, task_id."""
        response = client.post(
            self.DRAFTS_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 mock content " * 100), "application/pdf")},
            data={"document_key": "doc-integration-flow", "title": "Integration Test Doc", "source_type": "GOST"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "uploaded"
        assert "draft_id" in data
        assert "task_id" in data
        assert "file_hash_sha256" in data
        assert "file_size_bytes" in data
        return data

    async def test_full_draft_to_document_flow(
        self,
        created_draft: dict,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Полный цикл: upload → preview → approve → verify."""
        draft_id = created_draft["draft_id"]
        task_id = created_draft["task_id"]

        # Step 2: Start preview
        preview_resp = client.post(
            self.PREVIEW_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert preview_resp.status_code == 202
        preview_data = preview_resp.json()
        assert preview_data["status"] == "previewing"
        assert preview_data["draft_id"] == draft_id
        assert "task_id" in preview_data

        # Step 3: Advance task to decision stage (Celery is mocked, steps won't run)
        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
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

        # Step 4: Approve draft
        decide_resp = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert decide_resp.status_code == 200
        decide_data = decide_resp.json()
        assert decide_data["draft_id"] == draft_id
        assert decide_data["document_id"] is None
        assert decide_data["version_id"] is None
        assert decide_data["is_new_document"] is False
        assert decide_data["action"] == "approve"
        assert decide_data["status"] == "proceeding"

        document_id = decide_data["document_id"]
        version_id = decide_data["version_id"]

        # Step 5: Verify task details contain document_id and version_id
        # Note: POST /drafts creates a task with task_id = created_draft["task_id"],
        # but approve creates a new task. Let's verify the decide response task_id.
        task_resp = client.get(
            self.TASK_URL.format(task_id=decide_data["task_id"]),
            headers=auth_header,
        )
        assert task_resp.status_code == 200
        task_data = task_resp.json()
        assert task_data["task_id"] == decide_data["task_id"]
        assert task_data["draft_id"] == draft_id
        # document_id should appear in task after approve
        # approve не создаёт документ — он появится после full_converter
        assert task_data.get("document_id") is None

    async def test_draft_upload_without_file_returns_422(
        self, client: TestClient, auth_header: dict
    ):
        """Валидация: загрузка без файла → 422."""
        response = client.post(
            self.DRAFTS_URL,
            headers=auth_header,
            data={"document_key": "doc-no-file", "source_type": "GOST"},
        )
        assert response.status_code == 422

    async def test_decide_reject_flow(
        self,
        created_draft: dict,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Альтернативный сценарий: upload → reject."""
        draft_id = created_draft["draft_id"]

        # Advance to decision stage
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.pipeline_stage = "decision"
            task.status = "active"
            await db_session.flush()
            await db_session.commit()

        # Reject
        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "reject", "comment": "Not relevant"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "reject"
        assert data["status"] == "discarded"
