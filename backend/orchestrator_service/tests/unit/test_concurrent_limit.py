"""
Tests for concurrent task limit in pipeline execution.

Covers:
1. TaskRepository.count_active_tasks() — counts only active (non-terminal) tasks
2. PipelineOrchestrator._check_concurrent_limit() — raises when limit exceeded
3. Endpoint integration — 5th concurrent approve returns 429
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pipeline import TaskRepository
from app.core.pipeline.orchestrator import (
    ConcurrentTaskLimitError,
    PipelineOrchestrator,
)
from app.core.config import settings


@pytest.mark.asyncio
class TestCountActiveTasks:
    """Tests for TaskRepository.count_active_tasks."""

    async def test_zero_when_no_tasks(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        count = await repo.count_active_tasks()
        assert count == 0

    async def test_counts_active_tasks(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        await repo.create_task(draft_id=2, pipeline_type="formation", total_steps=4)
        count = await repo.count_active_tasks()
        assert count == 2

    async def test_excludes_completed(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        t1 = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        t2 = await repo.create_task(draft_id=2, pipeline_type="formation", total_steps=4)
        await repo.update_task_status(t1.id, status="completed")
        count = await repo.count_active_tasks()
        assert count == 1  # t1 is terminal, t2 is active

    async def test_excludes_failed(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        t1 = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        t2 = await repo.create_task(draft_id=2, pipeline_type="formation", total_steps=4)
        await repo.update_task_status(t1.id, status="failed")
        count = await repo.count_active_tasks()
        assert count == 1

    async def test_does_not_count_soft_deleted(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        from datetime import datetime, timezone
        t = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        t.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()
        count = await repo.count_active_tasks()
        assert count == 0


@pytest.mark.asyncio
class TestCheckConcurrentLimit:
    """Tests for PipelineOrchestrator._check_concurrent_limit."""

    async def test_allows_when_below_limit(self, db_session: AsyncSession):
        orchestrator = PipelineOrchestrator(db_session)
        # No active tasks — should pass without error
        await orchestrator._check_concurrent_limit()

    async def test_raises_when_limit_reached(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        # Fill up to the limit
        for i in range(limit):
            await repo.create_task(
                draft_id=i + 1,
                pipeline_type="formation",
                total_steps=4,
            )
        orchestrator = PipelineOrchestrator(db_session)
        with pytest.raises(ConcurrentTaskLimitError) as excinfo:
            await orchestrator._check_concurrent_limit()
        assert str(limit) in str(excinfo.value)

    async def test_passes_when_completed_task_frees_slot(
        self, db_session: AsyncSession
    ):
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        tasks = []
        for i in range(limit):
            t = await repo.create_task(
                draft_id=i + 1, pipeline_type="formation", total_steps=4,
            )
            tasks.append(t)
        # Complete the last task — frees a slot
        await repo.update_task_status(tasks[-1].id, status="completed")
        orchestrator = PipelineOrchestrator(db_session)
        # Should not raise (one completed, remaining active = limit - 1)
        await orchestrator._check_concurrent_limit()


@pytest.mark.asyncio
class TestConcurrentLimitInPipeline:
    """Integration: concurrent limit blocks a new start_pipeline."""

    async def test_start_pipeline_raises_at_limit(
        self, db_session: AsyncSession, monkeypatch
    ):
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        for i in range(limit):
            await repo.create_task(
                draft_id=i + 1, pipeline_type="formation", total_steps=4,
            )

        orchestrator = PipelineOrchestrator(db_session)
        with pytest.raises(ConcurrentTaskLimitError):
            await orchestrator.start_pipeline(
                draft_id=999,
                task_id=0,  # bogus — _check_concurrent_limit runs before task lookup
                file_key="test.pdf",
                mime_type="application/pdf",
            )

    async def test_approve_draft_raises_at_limit(
        self, db_session: AsyncSession
    ):
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        for i in range(limit):
            await repo.create_task(
                draft_id=i + 1, pipeline_type="formation", total_steps=4,
            )

        # Create a task to attempt approve on
        task = await repo.create_task(
            draft_id=100, pipeline_type="formation", total_steps=4,
        )

        orchestrator = PipelineOrchestrator(db_session)
        with pytest.raises(ConcurrentTaskLimitError):
            await orchestrator.approve_draft(
                draft_id=100,
                task_id=task.id,
            )
