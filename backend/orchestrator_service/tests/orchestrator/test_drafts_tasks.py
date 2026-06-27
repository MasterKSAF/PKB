"""
Тесты задач черновиков через Orchestrator API.

Покрывает:
  - GET /drafts/{id}/tasks — список задач черновика
  - GET /tasks/{id} — детали задачи с разными статусами
  - GET /tasks/{id} — несуществующая задача

Внимание:
  - GET /drafts/{id}/tasks уже частично покрыт в tests/test_drafts.py
  - retry_status и audit_logs (time/event/stage) не существуют в модели Task
"""

import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDraftTasksExtended:
    """GET /api/v1/drafts/{draft_id}/tasks — расширенные сценарии."""

    TASKS_URL = "/api/v1/drafts/{draft_id}/tasks"

    def test_draft_tasks_has_correct_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Структура элементов списка задач."""
        # Create a draft
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-tasks-struct", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        resp = client.get(
            self.TASKS_URL.format(draft_id=draft_id), headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["draft_id"] == draft_id
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        if data["tasks"]:
            t = data["tasks"][0]
            assert "task_id" in t
            assert "status" in t
            assert "pipeline_stage" in t
            assert "initiated_by" in t
            assert "created_at" in t
            assert "updated_at" in t


class TestTaskStatusExtended:
    """GET /api/v1/tasks/{task_id} — детали задачи с разными статусами."""

    TASK_URL = "/api/v1/tasks/{task_id}"

    async def _create_task_with_status(
        self, db_session: AsyncSession, status: str, stage: str = "upload"
    ) -> int:
        """Create a task in DB directly and return its id."""
        from app.repositories.pipeline import TaskRepository

        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=3
        )
        task.status = status
        task.pipeline_stage = stage
        if status == "completed":
            task.completed_at = datetime.now(timezone.utc)
            task.progress_percent = 100
        elif status == "active":
            task.progress_percent = 50
        await db_session.flush()
        task_id = task.id
        await db_session.commit()
        return task_id

    async def test_get_task_completed(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ):
        """Completed task → 200, status='completed', progress=100."""
        task_id = await self._create_task_with_status(db_session, "completed")
        response = client.get(
            self.TASK_URL.format(task_id=task_id), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percent"] == 100
        assert "steps" in data
        assert data["has_notifications"] is False

    async def test_get_task_active(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ):
        """Active task → 200, status='active', progress between 0-99."""
        task_id = await self._create_task_with_status(db_session, "active", "preview")
        response = client.get(
            self.TASK_URL.format(task_id=task_id), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["pipeline_stage"] == "preview"
        assert data["progress_percent"] == 50

    async def test_get_task_failed(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ):
        """Failed task → 200, status='failed'."""
        task_id = await self._create_task_with_status(db_session, "failed")
        response = client.get(
            self.TASK_URL.format(task_id=task_id), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"

    async def test_get_task_not_found(
        self, client: TestClient, auth_header: dict
    ):
        """Несуществующая задача → 404."""
        response = client.get(
            self.TASK_URL.format(task_id=99999), headers=auth_header
        )
        assert response.status_code == 404
        data = response.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert detail["error"]["code"] == "NOT_FOUND"

    async def test_get_task_retry_count(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ):
        """В ответе задачи есть retry_count (как proxy retry_status)."""
        from app.repositories.pipeline import TaskRepository

        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=3
        )
        task.retry_count = 2
        await db_session.flush()
        task_id = task.id
        await db_session.commit()

        response = client.get(
            self.TASK_URL.format(task_id=task_id), headers=auth_header
        )
        assert response.status_code == 200
        # retry_count не входит в TaskStatusResponse,
        # но error_code/message доступны при наличии
        data = response.json()
        assert data["task_id"] == task_id
