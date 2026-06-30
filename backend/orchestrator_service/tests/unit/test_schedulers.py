"""
Scheduler / cleanup tests (P0 from todo_pipeline_coverage §4).

Покрывает 3 сценария, отсутствующие в test_celery_tasks_all.TestCleanupStaleTasks:
1. Stale pending steps (P3S-1) — task_step завис в `pending` > 30с.
2. Absolute timeout (P3S-1) — task старше 48ч.
3. Stale running job — task `active` со `started_at` > MAX_JOB_RUNNING_TIME.

Все тесты — async, через `db_session` фикстуру.
Запускают `PipelineOrchestrator.cleanup_stale_tasks()` напрямую, минуя Celery.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pipeline import TaskRepository
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.core.config import settings


@pytest.mark.asyncio
class TestStalePendingTimeout:
    """task_step `pending` дольше PENDING_STATE_TIMEOUT → fail_task_step(PENDING_TIMEOUT)."""

    async def test_pending_step_older_than_threshold_marked_failed(
        self, db_session: AsyncSession
    ):
        """Шаг в pending > 30с → перевод в failed с кодом PENDING_TIMEOUT."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=2,
        )
        step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="OCR Service",
        )
        # Шаг создан недавно — не должен попасть в cleanup.
        stale = await repo.get_stale_pending_steps(
            max_pending_seconds=settings.pipeline.PENDING_STATE_TIMEOUT
        )
        assert not any(s.id == step.id for s in stale)

        # Сдвигаем created_at назад за порог (35с > 30с).
        db_step = await db_session.get(type(step), step.id)
        db_step.created_at = datetime.now(timezone.utc) - timedelta(
            seconds=settings.pipeline.PENDING_STATE_TIMEOUT + 5
        )
        await db_session.flush()

        # Cleanup: только этот шаг должен попасть.
        orchestrator = PipelineOrchestrator(db_session)
        cleaned = await orchestrator.cleanup_stale_tasks()
        assert cleaned >= 1

        # Шаг переведён в failed.
        await db_session.refresh(db_step)
        assert db_step.status == "failed"
        assert db_step.error_code == "PENDING_TIMEOUT"

    async def test_pending_step_within_threshold_untouched(
        self, db_session: AsyncSession
    ):
        """Свежий `pending` шаг НЕ попадает в cleanup (граничный случай)."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=1,
        )
        step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=0,
            service_name="OCR Service",
        )
        # created_at по умолчанию = now, шаг свежий.
        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.cleanup_stale_tasks()
        db_step = await db_session.get(type(step), step.id)
        assert db_step.status == "pending"

    async def test_multiple_pending_only_stale_marked_failed(
        self, db_session: AsyncSession
    ):
        """Cleanup не трогает свежие pending-шаги в той же task."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=3,
        )
        stale_step = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr",
            step_index=0, service_name="OCR Service",
        )
        fresh_step = await repo.create_task_step(
            task_id=task.id, step_name="preview_converter",
            step_index=1, service_name="Converter-validator",
        )
        # Только первый шаг делаем старым.
        db_stale = await db_session.get(type(stale_step), stale_step.id)
        db_stale.created_at = datetime.now(timezone.utc) - timedelta(seconds=120)
        await db_session.flush()

        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.cleanup_stale_tasks()

        await db_session.refresh(db_stale)
        await db_session.refresh(fresh_step)
        assert db_stale.status == "failed"
        assert fresh_step.status == "pending"


@pytest.mark.asyncio
class TestAbsoluteTimeout:
    """Task старше ABSOLUTE_TASK_TIMEOUT_HOURS → failed + error_code=ABSOLUTE_TIMEOUT."""

    async def test_task_older_than_48h_marked_failed(self, db_session: AsyncSession):
        """Task создан 49ч назад → cleanup_stale_tasks помечает failed."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=2,
        )
        await repo.update_task_status(task.id, status="active")
        # Сдвигаем created_at за порог 48ч.
        db_task = await repo.get_task_for_update(task.id)
        db_task.created_at = datetime.now(timezone.utc) - timedelta(
            hours=settings.pipeline.ABSOLUTE_TASK_TIMEOUT_HOURS + 1
        )
        await db_session.flush()

        # Должен попасть в выборку.
        stale = await repo.get_absolute_timeout_tasks(
            max_hours=settings.pipeline.ABSOLUTE_TASK_TIMEOUT_HOURS
        )
        assert any(t.id == task.id for t in stale)

        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.cleanup_stale_tasks()

        await db_session.refresh(db_task)
        assert db_task.status == "failed"
        assert db_task.error_code == "ABSOLUTE_TIMEOUT"

    async def test_task_within_48h_untouched(self, db_session: AsyncSession):
        """Свежая `active` task (1ч) НЕ попадает в absolute-timeout."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=2,
        )
        await repo.update_task_status(task.id, status="active")

        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.cleanup_stale_tasks()

        await db_session.refresh(task)
        assert task.status == "active"
        assert task.error_code is None

    async def test_completed_task_not_triggered_by_absolute_timeout(
        self, db_session: AsyncSession
    ):
        """`completed` task с created_at > 48ч НЕ попадает (фильтр status=='active')."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=2,
        )
        await repo.update_task_status(task.id, status="completed")
        # Имитируем очень старую дату, но completed.
        db_task = await repo.get_task_for_update(task.id)
        db_task.created_at = datetime.now(timezone.utc) - timedelta(hours=100)
        await db_session.flush()

        stale = await repo.get_absolute_timeout_tasks(max_hours=48)
        assert not any(t.id == task.id for t in stale)


@pytest.mark.asyncio
class TestStaleRunningJob:
    """Task `active` со started_at > MAX_JOB_RUNNING_TIME (по умолчанию 3600с = 1ч)."""

    async def test_running_task_older_than_max_running_time_failed(
        self, db_session: AsyncSession
    ):
        """Active task, который висит > 1ч, переводится в failed."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=3,
        )
        await repo.update_task_status(
            task.id, status="active", step_name="upload", step_index=0,
        )
        # Сдвигаем started_at за порог.
        db_task = await repo.get_task_for_update(task.id)
        db_task.started_at = datetime.now(timezone.utc) - timedelta(
            seconds=settings.pipeline.MAX_JOB_RUNNING_TIME + 60
        )
        await db_session.flush()

        stale = await repo.get_stale_running_tasks(
            max_running_seconds=settings.pipeline.MAX_JOB_RUNNING_TIME
        )
        assert any(t.id == task.id for t in stale)

        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.cleanup_stale_tasks()

        await db_session.refresh(db_task)
        assert db_task.status == "failed"
        # error_code зависит от реализации, главное — failed.
        assert db_task.error_code is not None

    async def test_recently_started_task_not_marked_stale(
        self, db_session: AsyncSession
    ):
        """Только что запущенная task НЕ попадает в stale."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=1,
        )
        await repo.update_task_status(
            task.id, status="active", step_name="upload", step_index=0,
        )
        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.cleanup_stale_tasks()
        await db_session.refresh(task)
        assert task.status == "active"
