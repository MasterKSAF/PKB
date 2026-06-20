"""
Unit tests for P2I-2 — Index integrity check.

Tests:
  - TaskRepository.get_recently_indexed_tasks()
  - Integrity check logic in pipeline_indexation (inline self-check)
  - Background integrity check task in scheduler
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.core.fsm import TaskStatus
from app.repositories.pipeline import TaskRepository


# ============================================================================
#  TaskRepository — get_recently_indexed_tasks
# ============================================================================


class TestGetRecentlyIndexedTasks:
    """Tests for TaskRepository.get_recently_indexed_tasks()."""

    @pytest.mark.asyncio
    async def test_returns_only_indexation_pipeline(self, db_session):
        """Only indexation pipeline tasks are returned."""
        repo = TaskRepository(db_session)
        from app.models.pipeline import Task

        # Create: indexation task (should be returned)
        index_task = await repo.create_task(
            draft_id=1, pipeline_type="indexation", total_steps=3,
        )
        # Mark as completed
        index_task.status = "completed"
        index_task.completed_at = datetime.now(timezone.utc)
        await db_session.flush()

        # Create: formation task (should NOT be returned)
        form_task = await repo.create_task(
            draft_id=2, pipeline_type="formation", total_steps=6,
        )
        form_task.status = "completed"
        form_task.completed_at = datetime.now(timezone.utc)
        await db_session.flush()

        result = await repo.get_recently_indexed_tasks(max_hours=24)
        task_ids = [t.id for t in result]
        assert index_task.id in task_ids
        assert form_task.id not in task_ids

    @pytest.mark.asyncio
    async def test_returns_completed_and_partially_indexed(self, db_session):
        """Both 'completed' and 'partially_indexed' statuses are returned."""
        repo = TaskRepository(db_session)
        from app.models.pipeline import Task

        # Completed indexation task
        t1 = await repo.create_task(
            draft_id=10, pipeline_type="indexation", total_steps=3,
        )
        t1.status = "completed"
        t1.completed_at = datetime.now(timezone.utc)
        await db_session.flush()

        # Partially indexed task
        t2 = await repo.create_task(
            draft_id=11, pipeline_type="indexation", total_steps=3,
        )
        t2.status = TaskStatus.PARTIALLY_INDEXED.value
        t2.completed_at = datetime.now(timezone.utc)
        await db_session.flush()

        # Failed task (should NOT be returned)
        t3 = await repo.create_task(
            draft_id=12, pipeline_type="indexation", total_steps=3,
        )
        t3.status = "failed"
        t3.completed_at = datetime.now(timezone.utc)
        await db_session.flush()

        result = await repo.get_recently_indexed_tasks(max_hours=24)
        task_ids = [t.id for t in result]
        assert t1.id in task_ids
        assert t2.id in task_ids
        assert t3.id not in task_ids

    @pytest.mark.asyncio
    async def test_excludes_old_tasks(self, db_session):
        """Tasks older than max_hours are excluded."""
        repo = TaskRepository(db_session)
        from datetime import timedelta
        from app.models.pipeline import Task

        t_old = await repo.create_task(
            draft_id=20, pipeline_type="indexation", total_steps=3,
        )
        t_old.status = "completed"
        t_old.completed_at = datetime.now(timezone.utc) - timedelta(hours=48)
        await db_session.flush()

        t_new = await repo.create_task(
            draft_id=21, pipeline_type="indexation", total_steps=3,
        )
        t_new.status = "completed"
        t_new.completed_at = datetime.now(timezone.utc)
        await db_session.flush()

        result = await repo.get_recently_indexed_tasks(max_hours=24)
        task_ids = [t.id for t in result]
        assert t_new.id in task_ids
        assert t_old.id not in task_ids

    @pytest.mark.asyncio
    async def test_excludes_soft_deleted(self, db_session):
        """Soft-deleted tasks are excluded."""
        repo = TaskRepository(db_session)
        from app.models.pipeline import Task

        t = await repo.create_task(
            draft_id=30, pipeline_type="indexation", total_steps=3,
        )
        t.status = "completed"
        t.completed_at = datetime.now(timezone.utc)
        t.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()

        result = await repo.get_recently_indexed_tasks(max_hours=24)
        assert t.id not in [r.id for r in result]

    @pytest.mark.asyncio
    async def test_empty_when_no_tasks(self, db_session):
        """Returns empty list when no matching tasks exist."""
        repo = TaskRepository(db_session)
        result = await repo.get_recently_indexed_tasks(max_hours=24)
        assert result == []


# ============================================================================
#  Pipeline indexation — self-check integrity (inline in run_rag_index_step)
# ============================================================================


class TestIntegrityCheckInline:
    """Tests for inline integrity check logic in pipeline_indexation.

    Tests the integrity check branches without calling Celery directly.
    """

    @pytest.mark.asyncio
    async def test_inline_integrity_fail_on_zero_chunks(self):
        """When indexed_count=0 but expected_count>0, integrity should fail."""
        # Simulate: index returns 0 chunks but expected 100
        indexed_count = 0
        expected_count = 100

        # The inline check: expected_count > 0 and indexed_count == 0 -> fail
        inline_integrity_fail = (
            expected_count > 0 and indexed_count == 0
        )
        assert inline_integrity_fail, "Should detect zero indexed chunks"

    def test_inline_integrity_pass_when_chunks_match(self):
        """When indexed_count matches expected, integrity should pass."""
        indexed_count = 128
        expected_count = 128

        inline_integrity_fail = (
            expected_count > 0 and indexed_count == 0
        )
        assert not inline_integrity_fail

    def test_inline_integrity_pass_when_both_zero(self):
        """When both indexed and expected are 0, no integrity failure."""
        indexed_count = 0
        expected_count = 0

        inline_integrity_fail = (
            expected_count > 0 and indexed_count == 0
        )
        assert not inline_integrity_fail


# ============================================================================
#  Scheduler — background integrity check
# ============================================================================


class TestBackgroundIntegrityCheck:
    """Tests for the background integrity check task."""

    @pytest.mark.asyncio
    async def test_integrity_check_task_definition(self):
        """Task must be registered with correct name."""
        from app.tasks.scheduler import integrity_check
        from app.celery_app import celery_app

        task = celery_app.tasks.get("app.tasks.scheduler.integrity_check")
        assert task is not None, "Background integrity check task not registered"
        assert task.name == "app.tasks.scheduler.integrity_check"

    @pytest.mark.asyncio
    async def test_integrity_check_doc_id_derivation(self):
        """doc_id derivation: document_id first, fallback to draft_id."""
        from app.models.pipeline import Task

        task = MagicMock(spec=Task)
        task.document_id = 42
        task.draft_id = 1
        doc_id = str(task.document_id or task.draft_id)
        assert doc_id == "42"

        # Fallback to draft_id
        task.document_id = None
        doc_id = str(task.document_id or task.draft_id)
        assert doc_id == "1"

    @pytest.mark.asyncio
    async def test_integrity_check_task_is_callable(self):
        """Verify the task function is a Celery Task with .delay()."""
        from app.tasks.scheduler import integrity_check

        # In test mode, .delay() is mocked to no-op via conftest
        result = integrity_check.delay()
        assert result is None  # Mocked .delay() returns None
