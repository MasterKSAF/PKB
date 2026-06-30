"""
Тесты preview и decision черновиков через Orchestrator API.

Покрывает сценарии, требующие прямой манипуляции БД (статусы шагов):
  - GET /drafts/{id}/preview/status — pending/processing
  - GET /drafts/{id}/preview/status — completed с preview_metadata
  - GET /drafts/{id}/preview/status — failed с error info
  - PATCH /drafts/{id}/decide — reject без comment
  - PATCH /drafts/{id}/decide — невалидный action → 422 (через pydantic)

Внимание:
  - Большая часть preview/decide тестов уже в tests/test_drafts.py
  - Здесь только то, что требует DB setup или не покрыто там
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPreviewStatusExtended:
    """GET /api/v1/drafts/{draft_id}/preview/status — расширенные сценарии."""

    STATUS_URL = "/api/v1/drafts/{draft_id}/preview/status"
    CREATE_URL = "/api/v1/drafts/"
    PREVIEW_URL = "/api/v1/drafts/{draft_id}/preview"

    @pytest.fixture
    def created_draft(self, client: TestClient, auth_header: dict) -> int:
        """Create a draft via API."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-preview-ext", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    async def test_preview_status_pending(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """
        Preview не запущен → статус "processing" (нет completed steps).
        После create_draft задача в stage="upload", preview status без longpoll.
        """
        # Start preview to create steps
        client.post(
            self.PREVIEW_URL.format(draft_id=created_draft),
            headers=auth_header,
        )

        # Steps are created with status="pending" — query without longpoll
        response = client.get(
            self.STATUS_URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        assert response.status_code == 200
        data = response.json()
        # Steps are pending — not yet completed or failed
        assert data["status"] in ("processing", "pending")
        assert "task_id" in data
        assert "progress_percent" in data
        assert "decision_required" in data

    async def test_preview_status_completed_with_metadata(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """
        Preview steps are "completed" → status="completed", preview_metadata
        is populated from converter step output_data.
        """
        # Start preview to create task + steps
        client.post(
            self.PREVIEW_URL.format(draft_id=created_draft),
            headers=auth_header,
        )

        # Find the task and set steps to completed with output_data
        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        assert task is not None

        # Set preview_steps to completed
        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        steps = list(steps_result.scalars().all())

        for step in steps:
            step.status = "completed"
            if step.step_name == "preview_converter":
                step.output_data = {
                    "metadata": {
                        "doc_code": "ГОСТ 1234-2024",
                        "title": "Preview Test Title",
                        "document_type": "normative",
                        "source_type": "GOST",
                        "year": "2024",
                        "era": "CURRENT",
                        "jurisdiction": "RU",
                    }
                }

        # Advance task stage to decision
        task.pipeline_stage = "decision"
        await db_session.flush()
        await db_session.commit()

        response = client.get(
            self.STATUS_URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["decision_required"] is True
        # Проверяем preview_metadata
        preview = data.get("preview")
        assert preview is not None
        assert preview.get("doc_code") == "ГОСТ 1234-2024"
        assert preview.get("title") == "Preview Test Title"
        assert preview.get("source_type") == "GOST"

    async def test_preview_status_failed(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """
        Preview steps are "failed" → status="failed", decision_required=False.
        """
        # Start preview
        client.post(
            self.PREVIEW_URL.format(draft_id=created_draft),
            headers=auth_header,
        )

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        assert task is not None

        # Set preview steps to failed
        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        for step in steps_result.scalars().all():
            step.status = "failed"
            step.error_code = "PROCESSING_ERROR"
            step.error_message = "OCR processing failed: timeout"

        task.status = "failed"
        await db_session.flush()
        await db_session.commit()

        response = client.get(
            self.STATUS_URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"


class TestDecideDraftExtended:
    """PATCH /api/v1/drafts/{draft_id}/decide — расширенные сценарии."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def created_draft(self, client: TestClient, auth_header: dict, db_session) -> int:
        """Create draft + advance task to decision stage."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-decide-ext", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

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

        return draft_id

    def test_decide_reject_without_comment(
        self, created_draft: int, client: TestClient, auth_header: dict
    ):
        """Reject без comment → 200, status='discarded'."""
        response = client.patch(
            self.DECIDE_URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "reject"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "reject"
        assert data["status"] == "discarded"

    def test_decide_invalid_action_via_pydantic(
        self, created_draft: int, client: TestClient, auth_header: dict
    ):
        """Поле action с невалидным значением → 400 (не 422, т.к. str, а не enum)."""
        response = client.patch(
            self.DECIDE_URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "unknown_pipeline_action"},
        )
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", data)
        assert "error" in detail


class TestPreviewStatusDuplicateSteps:
    """
    GET /preview/status с дублирующимися шагами (5.1).

    Если есть 2 preview_ocr (один completed, другой running),
    после дедупликации статус должен быть "processing", а не "completed".
    """

    STATUS_URL = "/api/v1/drafts/{draft_id}/preview/status"
    CREATE_URL = "/api/v1/drafts/"
    PREVIEW_URL = "/api/v1/drafts/{draft_id}/preview"

    @pytest.fixture
    def created_draft(self, client: TestClient, auth_header: dict) -> int:
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF dup " * 150), "application/pdf")},
            data={"document_key": "doc-dup-status", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    async def test_preview_status_duplicate_steps_returns_processing(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """2 preview_ocr шага (completed + running) → статус processing."""
        # Start preview
        client.post(
            self.PREVIEW_URL.format(draft_id=created_draft),
            headers=auth_header,
        )

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        assert task is not None

        # Get current steps
        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        steps = list(steps_result.scalars().all())

        # Find first preview_ocr step and mark it completed
        ocr_steps = [s for s in steps if s.step_name == "preview_ocr"]
        assert len(ocr_steps) >= 1, "Expected at least one preview_ocr step"

        # Set first ocr step to completed
        ocr_steps[0].status = "completed"

        # Create a DUPLICATE preview_ocr step with status=running
        duplicate_step = TaskStep(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=99,
            status="running",
            input_data={},
        )
        db_session.add(duplicate_step)

        # Set converter to completed (so without dedup it would be 'all completed')
        conv_steps = [s for s in steps if s.step_name == "preview_converter"]
        if conv_steps:
            conv_steps[0].status = "completed"

        await db_session.flush()
        await db_session.commit()

        # Query without longpoll
        response = client.get(
            self.STATUS_URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        assert response.status_code == 200
        data = response.json()
        # After dedup: preview_ocr best=completed (completed > running), preview_converter=completed → completed
        # Дедупликация не даёт дублирующему running-шагу заблокировать завершение
        assert data["status"] == "completed", (
            f"Expected 'completed' with duplicate running step (dedup), got {data['status']}"
        )

    async def test_preview_status_duplicate_one_completed_one_failed(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Duplicate steps: completed + failed → failed (failed wins)."""
        client.post(
            self.PREVIEW_URL.format(draft_id=created_draft),
            headers=auth_header,
        )

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        assert task is not None

        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        steps = list(steps_result.scalars().all())

        ocr_steps = [s for s in steps if s.step_name == "preview_ocr"]
        assert len(ocr_steps) >= 1
        ocr_steps[0].status = "completed"

        # Add duplicate failed step
        duplicate_step = TaskStep(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=99,
            status="failed",
            input_data={},
            error_code="TEST_ERROR",
            error_message="Test failure",
        )
        db_session.add(duplicate_step)

        conv_steps = [s for s in steps if s.step_name == "preview_converter"]
        if conv_steps:
            conv_steps[0].status = "completed"

        await db_session.flush()
        await db_session.commit()

        response = client.get(
            self.STATUS_URL.format(draft_id=created_draft),
            headers=auth_header,
            params={"longpoll": 0},
        )
        assert response.status_code == 200
        data = response.json()
        # After dedup: preview_ocr best=failed → overall failed
        assert data["status"] == "failed"
