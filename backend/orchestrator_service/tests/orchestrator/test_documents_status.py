"""
Тесты статусов документов (через task status в оркестраторе).

Покрывает статусы pipeline-задач:
  - GET /tasks/{id} — completed (аналог документ обработан)
  - GET /tasks/{id} — active/processing (аналог документ в обработке)
  - GET /tasks/{id} — failed (аналог ошибка обработки)
  - GET /tasks/{id} — несуществующий

Внимание:
  - GET /documents/{id}/status — эндпоинт находится в Registry, не в оркестраторе
  - chunk_summary — поле Registry, не в оркестраторе
  - Статусы pipeline-задач — это proxy для статусов документов
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestTaskStatusAsDocumentStatus:
    """Статусы документов через task status (proxy)."""

    TASK_URL = "/api/v1/tasks/{task_id}"

    async def _create_task(
        self, db_session: AsyncSession, status: str, stage: str
    ) -> int:
        """Create a task in DB."""
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
        elif status == "failed":
            task.error_code = "PROCESSING_ERROR"
            task.error_message = "Document processing failed"
        elif status == "active":
            task.progress_percent = 30
        await db_session.flush()
        task_id = task.id
        await db_session.commit()
        return task_id

    async def test_completed_status(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ):
        """Completed task → 200, status='completed', progress_percent=100."""
        task_id = await self._create_task(db_session, "completed", "registry")
        response = client.get(
            self.TASK_URL.format(task_id=task_id), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percent"] == 100
        assert data["pipeline_stage"] == "registry"

    async def test_processing_status(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ):
        """Active task → 200, status='active', stage отражает этап."""
        task_id = await self._create_task(db_session, "active", "indexation")
        response = client.get(
            self.TASK_URL.format(task_id=task_id), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["pipeline_stage"] == "indexation"
        assert data["progress_percent"] == 30

    async def test_failed_status(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ):
        """Failed task → 200, status='failed'."""
        task_id = await self._create_task(db_session, "failed", "preview")
        response = client.get(
            self.TASK_URL.format(task_id=task_id), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"

    async def test_not_found(
        self, client: TestClient, auth_header: dict
    ):
        """Несуществующая задача → 404."""
        response = client.get(
            self.TASK_URL.format(task_id=99999), headers=auth_header
        )
        assert response.status_code == 404
