"""
Integration test: draft → document → version chain (T-7).

Verifies that:
  1. POST /drafts → returns draft_id, task_id
  2. PATCH /drafts/{id}/decide with approve → returns document_id, version_id, is_new_document
  3. document_id and version_id are present in task details

Note: GET /drafts/{id} удалён из Orchestrator (чтение черновиков — Registry).
"""

import pytest
from fastapi.testclient import TestClient


class TestDraftToDocumentChain:
    """Chain: create draft → approve → get document and version."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"

    @pytest.fixture
    async def created_draft_and_task(self, client: TestClient, auth_header: dict, db_session) -> tuple:
        """Create draft and advance task to decision stage."""
        create_resp = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF-1.4 mock " * 150, "application/pdf")},
            data={"document_key": "doc-chain-test", "title": "Chain Test Doc", "source_type": "GOST"},
        )
        assert create_resp.status_code == 202
        data = create_resp.json()
        draft_id = data["draft_id"]
        task_id = data["task_id"]

        # Advance task to decision stage (Celery is mocked, steps won't run)
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

        return draft_id, task_id

    def test_full_chain(self, created_draft_and_task: tuple, client: TestClient, auth_header: dict):
        """Complete draft→document→version flow."""
        draft_id, task_id = created_draft_and_task

        # Step 1: Approve draft (GET /drafts/{id} удалён — чтение через Registry)
        decide_resp = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert decide_resp.status_code == 200
        decide_data = decide_resp.json()
        assert decide_data["draft_id"] == draft_id
        assert decide_data["document_id"] is not None
        assert decide_data["version_id"] is not None
        assert "is_new_document" in decide_data
        assert decide_data["action"] == "approve"

        # Step 3: Check task — should have document_id and version_id
        task_resp = client.get(
            f"/api/v1/tasks/{task_id}",
            headers=auth_header,
        )
        assert task_resp.status_code == 200
        task_data = task_resp.json()
        assert task_data["task_id"] == task_id
        assert task_data["draft_id"] == draft_id
        assert "document_id" in task_data
        assert "version_id" in task_data
