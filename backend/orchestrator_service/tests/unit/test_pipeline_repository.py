"""
Unit tests for TaskRepository (replaces PipelineRepository).

Tests cover:
- Create + get Task
- Task status transitions (active -> completed/failed)
- Task locking / unlocking
- TaskStep CRUD (create, start, complete, fail, compensate)
- Stale task detection
- Error recording with retry
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pipeline import TaskRepository


@pytest.mark.asyncio
class TestTaskRepository:
    """Tests for TaskRepository."""

    # ------------------------------------------------------------------
    # Task
    # ------------------------------------------------------------------

    async def test_create_task(self, db_session: AsyncSession):
        """Creating a task returns it with status=active and stage=upload."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1,
            pipeline_type="formation",
            total_steps=4,
        )
        assert task.id is not None
        assert isinstance(task.id, int)
        assert task.status == "active"
        assert task.pipeline_stage == "upload"
        assert task.pipeline_type == "formation"
        assert task.total_steps == 4
        assert task.current_step_index == 0

    async def test_get_task(self, db_session: AsyncSession):
        """Getting an existing task returns it."""
        repo = TaskRepository(db_session)
        created = await repo.create_task(
            draft_id=1,
            pipeline_type="formation",
            total_steps=4,
        )
        fetched = await repo.get_task(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    async def test_get_task_not_found(self, db_session: AsyncSession):
        """Getting a non-existent task returns None."""
        repo = TaskRepository(db_session)
        assert await repo.get_task(99999) is None

    async def test_update_task_status_to_active(self, db_session: AsyncSession):
        """Updating task to active sets started_at."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1,
            pipeline_type="formation",
            total_steps=4,
        )
        updated = await repo.update_task_status(
            task.id,
            status="active",
            step_name="upload",
            step_index=0,
        )
        assert updated.status == "active"
        assert updated.current_step_name == "upload"
        assert updated.current_step_index == 0
        assert updated.started_at is not None

    async def test_update_task_status_to_completed(self, db_session: AsyncSession):
        """Updating task to completed sets completed_at."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1,
            pipeline_type="formation",
            total_steps=4,
        )
        await repo.update_task_status(task.id, status="active", step_name="upload", step_index=0)
        updated = await repo.update_task_status(task.id, status="completed")
        assert updated.status == "completed"
        assert updated.completed_at is not None

    async def test_task_lock_unlock(self, db_session: AsyncSession):
        """Locking a task sets locked_by and locked_at; unlock clears them."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1,
            pipeline_type="formation",
            total_steps=4,
        )
        locked = await repo.lock_task(task.id, "worker-1")
        assert locked.locked_by == "worker-1"
        assert locked.locked_at is not None

        unlocked = await repo.unlock_task(task.id)
        assert unlocked.locked_by is None
        assert unlocked.locked_at is None

    async def test_set_task_error(self, db_session: AsyncSession):
        """set_task_error records error info and increments retry."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        errored = await repo.set_task_error(
            task.id, "OCR_ERROR", "OCR failed"
        )
        assert errored.error_code == "OCR_ERROR"
        assert errored.error_message == "OCR failed"
        assert errored.retry_count == 1

    async def test_stale_running_tasks(self, db_session: AsyncSession):
        """get_stale_running_tasks finds tasks that have been running too long."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        # Set to active with very old started_at
        await repo.update_task_status(task.id, status="active", step_name="upload", step_index=0)
        # Manually set started_at in the past
        from datetime import datetime, timedelta, timezone
        db_task = await repo.get_task_for_update(task.id)
        db_task.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await db_session.flush()

        stale = await repo.get_stale_running_tasks(max_running_seconds=3600)
        assert len(stale) == 1
        assert stale[0].id == task.id

    async def test_update_task_stage(self, db_session: AsyncSession):
        """update_task_status can change the pipeline stage."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        updated = await repo.update_task_status(
            task.id, stage="preview", progress_percent=10
        )
        assert updated.pipeline_stage == "preview"
        assert updated.progress_percent == 10

    # ------------------------------------------------------------------
    # TaskStep
    # ------------------------------------------------------------------

    async def test_create_task_step(self, db_session: AsyncSession):
        """Creating a task step returns it with status=pending."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        step = await repo.create_task_step(
            task_id=task.id,
            step_name="upload",
            step_index=0,
            service_name="Orchestrator",
            input_data={"file_key": "test.pdf"},
        )
        assert step.step_name == "upload"
        assert step.service_name == "Orchestrator"
        assert step.status == "pending"
        assert step.input_data == {"file_key": "test.pdf"}

    async def test_task_step_lifecycle(self, db_session: AsyncSession):
        """Task step transitions through pending -> running -> completed."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        step = await repo.create_task_step(
            task_id=task.id,
            step_name="upload",
            step_index=0,
            service_name="Orchestrator",
        )

        started = await repo.start_task_step(step.id)
        assert started.status == "running"
        assert started.started_at is not None

        completed = await repo.complete_task_step(
            step.id, output_data={"result": "ok"}
        )
        assert completed.status == "completed"
        assert completed.output_data == {"result": "ok"}

    async def test_task_step_fail(self, db_session: AsyncSession):
        """Marking step as failed records error info."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="OCR Service",
        )
        await repo.start_task_step(step.id)
        failed = await repo.fail_task_step(step.id, "ERR", "msg")
        assert failed.status == "failed"
        assert failed.error_code == "ERR"
        assert failed.error_message == "msg"

    async def test_task_step_compensate(self, db_session: AsyncSession):
        """Marking step as compensated."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="OCR Service",
        )
        compensated = await repo.compensate_task_step(step.id)
        assert compensated.status == "compensated"

    async def test_get_task_steps(self, db_session: AsyncSession):
        """get_task_steps returns steps ordered by step_index."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=4,
        )
        steps = []
        for name, idx, svc in [
            ("upload", 0, "Orchestrator"),
            ("preview_ocr", 1, "OCR Service"),
            ("preview_converter", 2, "Converter-validator"),
        ]:
            step = await repo.create_task_step(
                task_id=task.id, step_name=name, step_index=idx, service_name=svc
            )
            steps.append(step)

        fetched = await repo.get_task_steps(task.id)
        assert len(fetched) == 3
        for i, step in enumerate(fetched):
            assert step.step_index == i  # Ordered by step_index
