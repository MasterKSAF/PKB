"""
Tests for queue-based concurrent task limiting in pipeline execution.

Covers:
1. TaskRepository.count_active_tasks() — counts only active (non-terminal) tasks
2. PipelineOrchestrator._has_free_slot() — returns bool
3. start_pipeline() queues when limit reached, dispatches when slot free
4. approve_draft() queues when limit reached
5. _drain_queue() processes queued tasks FIFO
6. get_next_queued_task() FIFO ordering with SKIP LOCKED
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.pipeline import TaskRepository
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.core.fsm import TaskStatus
from app.core.config import settings
from app.models.pipeline import Task as TaskModel


async def _create_task_with_upload_step(
    db: AsyncSession, draft_id: int, file_key: str = "test.pdf",
) -> TaskModel:
    """Create a task and run start_pipeline to set up proper upload steps.

    Returns the task after pipeline start (which may be active or queued).
    """
    repo = TaskRepository(db)
    task = await repo.create_task(
        draft_id=draft_id, pipeline_type="formation", total_steps=4,
    )
    orchestrator = PipelineOrchestrator(db)
    await orchestrator.start_pipeline(
        draft_id=draft_id,
        task_id=task.id,
        file_key=file_key,
        mime_type="application/pdf",
    )
    return task


async def _create_active_task_with_step(
    db: AsyncSession, draft_id: int,
) -> TaskModel:
    """Create a task with a minimal pending step so count_active_tasks counts it."""
    repo = TaskRepository(db)
    task = await repo.create_task(
        draft_id=draft_id, pipeline_type="formation", total_steps=4,
    )
    task.status = TaskStatus.ACTIVE.value
    await db.flush()
    # Create a pending step — required for count_active_tasks
    await repo.create_task_step(
        task_id=task.id,
        step_name="upload",
        step_index=0,
        service_name="Orchestrator",
        input_data={"file_key": "test.pdf", "draft_id": draft_id},
    )
    return task


@pytest.mark.asyncio
class TestCountActiveTasks:
    """Tests for TaskRepository.count_active_tasks."""

    async def test_zero_when_no_tasks(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        count = await repo.count_active_tasks()
        assert count == 0

    async def test_counts_active_tasks(self, db_session: AsyncSession):
        await _create_active_task_with_step(db_session, 1)
        await _create_active_task_with_step(db_session, 2)
        repo = TaskRepository(db_session)
        count = await repo.count_active_tasks()
        assert count == 2

    async def test_excludes_completed(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        t1 = await _create_active_task_with_step(db_session, 1)
        t2 = await _create_active_task_with_step(db_session, 2)
        await repo.update_task_status(t1.id, status="completed")
        count = await repo.count_active_tasks()
        assert count == 1  # t1 is terminal, t2 is active

    async def test_excludes_failed(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        t1 = await _create_active_task_with_step(db_session, 1)
        t2 = await _create_active_task_with_step(db_session, 2)
        await repo.update_task_status(t1.id, status="failed")
        count = await repo.count_active_tasks()
        assert count == 1

    async def test_excludes_queued(self, db_session: AsyncSession):
        """QUEUED tasks should NOT be counted as active."""
        repo = TaskRepository(db_session)
        t1 = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        await repo.update_task_status(t1.id, status=TaskStatus.QUEUED.value)
        count = await repo.count_active_tasks()
        assert count == 0

    async def test_does_not_count_soft_deleted(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        from datetime import datetime, timezone
        t = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        t.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()
        count = await repo.count_active_tasks()
        assert count == 0


@pytest.mark.asyncio
class TestHasFreeSlot:
    """Tests for PipelineOrchestrator._has_free_slot."""

    async def test_returns_true_when_below_limit(self, db_session: AsyncSession):
        orchestrator = PipelineOrchestrator(db_session)
        # No active tasks — should return True
        assert await orchestrator._has_free_slot() is True

    async def test_returns_false_when_limit_reached(self, db_session: AsyncSession):
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        # Fill up to the limit with tasks that have steps (counted as active)
        for i in range(limit):
            await _create_active_task_with_step(
                db_session, i + 1,
            )
        orchestrator = PipelineOrchestrator(db_session)
        assert await orchestrator._has_free_slot() is False

    async def test_returns_true_when_completed_frees_slot(
        self, db_session: AsyncSession
    ):
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        tasks = []
        for i in range(limit):
            t = await _create_active_task_with_step(
                db_session, i + 1,
            )
            tasks.append(t)
        # Complete the last task — frees a slot
        await repo.update_task_status(tasks[-1].id, status="completed")
        orchestrator = PipelineOrchestrator(db_session)
        assert await orchestrator._has_free_slot() is True

    async def test_queued_not_counted_as_active(self, db_session: AsyncSession):
        """QUEUED tasks should not consume slots."""
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        # Fill up with queued tasks
        for i in range(limit):
            t = await repo.create_task(
                draft_id=i + 1, pipeline_type="formation", total_steps=4,
            )
            await repo.update_task_status(t.id, status=TaskStatus.QUEUED.value)

        orchestrator = PipelineOrchestrator(db_session)
        # Should return True because queued tasks don't count as active
        assert await orchestrator._has_free_slot() is True


@pytest.mark.asyncio
class TestGetNextQueuedTask:
    """Tests for TaskRepository.get_next_queued_task."""

    async def test_returns_none_when_empty(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        assert await repo.get_next_queued_task() is None

    async def test_returns_oldest_queued(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        t1 = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        t2 = await repo.create_task(draft_id=2, pipeline_type="formation", total_steps=4)
        await repo.update_task_status(t1.id, status=TaskStatus.QUEUED.value)
        await repo.update_task_status(t2.id, status=TaskStatus.QUEUED.value)

        # Should return the oldest (t1, smaller id = earlier created_at)
        next_task = await repo.get_next_queued_task()
        assert next_task is not None
        assert next_task.id == t1.id

    async def test_ignores_active_tasks(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        t1 = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        t2 = await repo.create_task(draft_id=2, pipeline_type="formation", total_steps=4)
        await repo.update_task_status(t1.id, status=TaskStatus.QUEUED.value)
        # t2 stays active

        next_task = await repo.get_next_queued_task()
        assert next_task is not None
        assert next_task.id == t1.id

    async def test_ignores_terminal_tasks(self, db_session: AsyncSession):
        repo = TaskRepository(db_session)
        t1 = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)
        t2 = await repo.create_task(draft_id=2, pipeline_type="formation", total_steps=4)
        await repo.update_task_status(t1.id, status=TaskStatus.QUEUED.value)
        await repo.update_task_status(t2.id, status=TaskStatus.COMPLETED.value)

        next_task = await repo.get_next_queued_task()
        assert next_task is not None
        assert next_task.id == t1.id


@pytest.mark.asyncio
class TestStartPipelineQueuing:
    """Tests: start_pipeline queues when limit reached, dispatches when free."""

    async def test_dispatches_when_slot_available(
        self, db_session: AsyncSession
    ):
        repo = TaskRepository(db_session)
        task = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)

        orchestrator = PipelineOrchestrator(db_session)
        result = await orchestrator.start_pipeline(
            draft_id=1,
            task_id=task.id,
            file_key="test.pdf",
            mime_type="application/pdf",
        )

        # Should be active (slot was free)
        assert result is True

        # Verify task is active
        await db_session.refresh(task)
        assert task.status == TaskStatus.ACTIVE.value

    async def test_queues_when_limit_reached(
        self, db_session: AsyncSession
    ):
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        # Fill up to the limit with active tasks (with steps)
        for i in range(limit):
            await _create_active_task_with_step(
                db_session, draft_id=i + 2,
            )

        # Now try to start a new pipeline
        task = await repo.create_task(draft_id=1, pipeline_type="formation", total_steps=4)

        orchestrator = PipelineOrchestrator(db_session)
        result = await orchestrator.start_pipeline(
            draft_id=1,
            task_id=task.id,
            file_key="test.pdf",
            mime_type="application/pdf",
        )

        # Should be queued (no free slot)
        assert result is False

        # Verify task is queued
        await db_session.refresh(task)
        assert task.status == TaskStatus.QUEUED.value

    async def test_queue_then_drain_when_slot_frees(
        self, db_session: AsyncSession
    ):
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS

        # Fill slots with active tasks (with steps)
        active_tasks = []
        for i in range(limit):
            t = await _create_active_task_with_step(
                db_session, draft_id=i + 2,
            )
            active_tasks.append(t)

        # Create a task via start_pipeline to get proper upload step
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.start_pipeline(
            draft_id=1,
            task_id=task.id,
            file_key="test.pdf",
            mime_type="application/pdf",
        )
        # Because limit is already reached, start_pipeline should have queued it
        await db_session.refresh(task)
        assert task.status == TaskStatus.QUEUED.value

        # Complete one active task — frees a slot
        await repo.update_task_status(active_tasks[0].id, status="completed")

        # Drain queue
        dequeued = await orchestrator._drain_queue()

        # Verify the queued task was activated
        assert dequeued == 1
        await db_session.refresh(task)
        assert task.status == TaskStatus.ACTIVE.value


@pytest.mark.asyncio
class TestApproveDraftQueuing:
    """Tests: approve_draft queues when limit reached."""

    async def test_approve_returns_queued_when_limit_reached(
        self, db_session: AsyncSession
    ):
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS

        # Fill slots with active tasks (with steps)
        for i in range(limit):
            await _create_active_task_with_step(
                db_session, draft_id=i + 1,
            )

        # Create a task to attempt approve on
        task = await repo.create_task(
            draft_id=100, pipeline_type="formation", total_steps=4,
        )

        orchestrator = PipelineOrchestrator(db_session)
        result = await orchestrator.approve_draft(
            draft_id=100,
            task_id=task.id,
        )

        # Should indicate queued
        assert result.get("queued") is True

        # Verify task is queued with FULL stage (approve creates doc+steps first)
        await db_session.refresh(task)
        assert task.status == TaskStatus.QUEUED.value
        assert task.pipeline_stage == "full"


@pytest.mark.asyncio
class TestDrainQueue:
    """Tests for _drain_queue FIFO processing."""

    async def test_drain_none_when_empty(self, db_session: AsyncSession):
        orchestrator = PipelineOrchestrator(db_session)
        dequeued = await orchestrator._drain_queue()
        assert dequeued == 0

    async def test_drain_fifo_order(self, db_session: AsyncSession):
        """Drain should activate tasks in FIFO order (oldest first)."""
        limit = settings.pipeline.MAX_CONCURRENT_TASKS

        # Create tasks via start_pipeline so they have upload steps
        # First fill to limit with regular tasks (no steps needed, just active)
        repo = TaskRepository(db_session)
        filler_tasks = []
        for i in range(limit):
            t = await repo.create_task(
                draft_id=i + 1, pipeline_type="formation", total_steps=4,
            )
            filler_tasks.append(t)

        # Create three tasks with proper upload steps
        t1 = await _create_task_with_upload_step(db_session, 101, "t1.pdf")
        t2 = await _create_task_with_upload_step(db_session, 102, "t2.pdf")
        t3 = await _create_task_with_upload_step(db_session, 103, "t3.pdf")

        # Set them all to queued
        await repo.update_task_status(t1.id, status=TaskStatus.QUEUED.value)
        await repo.update_task_status(t2.id, status=TaskStatus.QUEUED.value)
        await repo.update_task_status(t3.id, status=TaskStatus.QUEUED.value)

        # Free all slots
        for t in filler_tasks:
            await repo.update_task_status(t.id, status="completed")

        orchestrator = PipelineOrchestrator(db_session)
        dequeued = await orchestrator._drain_queue()

        # Should drain up to limit tasks
        assert dequeued > 0

        await db_session.refresh(t1)
        await db_session.refresh(t2)
        await db_session.refresh(t3)

        # t1 is oldest, should be active
        assert t1.status == TaskStatus.ACTIVE.value

    async def test_drain_respects_limit(self, db_session: AsyncSession):
        """Drain should not exceed MAX_CONCURRENT_TASKS."""
        repo = TaskRepository(db_session)
        limit = settings.pipeline.MAX_CONCURRENT_TASKS

        # Queue more than limit tasks with upload steps
        queued_tasks = []
        for i in range(limit + 2):
            t = await _create_task_with_upload_step(
                db_session, i + 1, f"test{i}.pdf",
            )
            await repo.update_task_status(t.id, status=TaskStatus.QUEUED.value)
            queued_tasks.append(t)

        orchestrator = PipelineOrchestrator(db_session)
        dequeued = await orchestrator._drain_queue()

        # Should only drain up to limit
        assert dequeued <= limit

        # Active count should be exactly what was dequeued
        active_count = await repo.count_active_tasks()
        assert active_count == dequeued
