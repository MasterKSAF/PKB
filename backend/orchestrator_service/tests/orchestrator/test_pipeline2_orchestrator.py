"""
Тесты Pipeline 2 (Индексация) на уровне оркестратора.

Покрывает сценарии из pipeline2-orchestrator_details.md:
  - _on_full_step_completed rag_index → pipeline completed
  - Связь Pipeline 1 → Pipeline 2 (pending_index)
  - Reprocess mode=reindex (через API)
  - Integrity check (через Celery task)

Внимание:
  - Большая часть Pipeline 2 логики — в Celery задачах (tests/unit/test_celery_tasks_all.py)
  - Оркестратор только диспатчит RAG index step и обрабатывает завершение
  - Scheduler-триггер индексации не реализован в оркестраторе
"""

import io

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.repositories.pipeline import TaskRepository
from app.core.fsm import TaskStatus, TaskStage


class TestRagIndexCompletion:
    """_on_full_step_completed при завершении rag_index."""

    async def test_rag_index_completion_marks_pipeline_completed(
        self, db_session: AsyncSession,
    ):
        """rag_index step completed → task=completed, stage=registry, progress=100."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=400, pipeline_type="formation", total_steps=7,
        )
        task.document_id = 100500
        task.status = "active"
        task.pipeline_stage = "full"
        await db_session.flush()

        # Create the rag_index step
        rag_step = await repo.create_task_step(
            task_id=task.id, step_name="rag_index", step_index=6,
            service_name="RAG Builder",
            input_data={"draft_id": 400, "document_id": 100500},
        )
        await repo.start_task_step(rag_step.id)
        await repo.complete_task_step(
            rag_step.id,
            output_data={"chunks_count": 42, "index_stats": {"tokens": 15000}},
        )

        mock_registry = AsyncMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_full_step_completed(
                task, "rag_index", await repo.get_task_steps(task.id)
            )

        # Verify: task completed
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status == TaskStatus.COMPLETED.value
        assert updated.pipeline_stage == TaskStage.REGISTRY.value
        assert updated.progress_percent == 100

        # Registry document status should be updated to validating
        mock_registry.update_document_status.assert_called_with(
            document_id=100500,
            status="validating",
        )


class TestReprocessReindex:
    """POST /documents/{doc_id}/reprocess mode=reindex."""

    URL = "/api/v1/documents/{doc_id}/reprocess"

    def test_reprocess_reindex_mode(
        self, client: TestClient, auth_header: dict
    ):
        """Reprocess mode=reindex → 202."""
        response = client.post(
            self.URL.format(doc_id="doc-reindex-001"),
            json={"mode": "reindex"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["mode"] == "reindex"
        assert "task_id" in data
        assert data["status"] == "reprocessing_queued"

    def test_reprocess_chunking_only_mode(
        self, client: TestClient, auth_header: dict
    ):
        """Reprocess mode=chunking_only → 202."""
        response = client.post(
            self.URL.format(doc_id="doc-chunking-001"),
            json={"mode": "chunking_only"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["mode"] == "chunking_only"


class TestGetTaskWithIndexationType:
    """GET /tasks с фильтром pipeline_type=indexation."""

    TASKS_URL = "/api/v1/tasks"

    async def test_list_tasks_filters_by_pipeline_type(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession,
    ):
        """GET /tasks?pipeline_type=indexation возвращает только indexation задачи."""
        # Create a formation task
        repo = TaskRepository(db_session)
        formation = await repo.create_task(
            draft_id=500, pipeline_type="formation", total_steps=3,
        )
        # Create an indexation task
        indexation = await repo.create_task(
            draft_id=501, pipeline_type="indexation", total_steps=1,
        )
        # Create a reprocess task
        reprocess = await repo.create_task(
            draft_id=502, pipeline_type="reprocess", total_steps=1,
        )
        await db_session.commit()

        # Filter by indexation
        response = client.get(
            self.TASKS_URL,
            headers=auth_header,
            params={"pipeline_type": "indexation"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        for item in data["items"]:
            assert item["pipeline_type"] == "indexation"

        # Filter by formation
        response2 = client.get(
            self.TASKS_URL,
            headers=auth_header,
            params={"pipeline_type": "formation"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) >= 1
        for item in data2["items"]:
            assert item["pipeline_type"] == "formation"
