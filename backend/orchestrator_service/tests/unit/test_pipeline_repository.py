"""
Unit tests for PipelineRepository.

Tests cover:
- Create + get PipelineJob
- Job status transitions (queued -> running -> completed/failed)
- Job locking / unlocking
- Step log CRUD (create, start, complete, fail, compensate)
- Queued job retrieval with priority ordering
- Stale job detection
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pipeline import PipelineRepository
from app.repositories.document import DocumentRepository


@pytest.mark.asyncio
class TestPipelineRepository:
    """Tests for PipelineRepository."""

    async def _create_document(self, db_session, hash_suffix="pipe"):
        repo = DocumentRepository(db_session)
        return await repo.create(
            file_hash_sha256=f"pipe_test_{hash_suffix}",
            original_filename=f"pipe_{hash_suffix}.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
        )

    # ------------------------------------------------------------------
    # PipelineJob
    # ------------------------------------------------------------------

    async def test_create_job(self, db_session: AsyncSession):
        """Creating a job returns it with status=queued."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id,
            pipeline_type="formation",
            total_steps=4,
        )
        assert job.id is not None
        assert job.status == "queued"
        assert job.pipeline_type == "formation"
        assert job.total_steps == 4
        assert job.current_step_index == 0

    async def test_get_job(self, db_session: AsyncSession):
        """Getting an existing job returns it."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        created = await pipeline_repo.create_job(
            document_id=doc.id,
            pipeline_type="formation",
            total_steps=4,
        )
        fetched = await pipeline_repo.get_job(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    async def test_get_job_not_found(self, db_session: AsyncSession):
        """Getting a non-existent job returns None."""
        pipeline_repo = PipelineRepository(db_session)
        assert await pipeline_repo.get_job("no-such-job") is None

    async def test_update_job_status_to_running(self, db_session: AsyncSession):
        """Updating job to 'running' sets started_at."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id,
            pipeline_type="formation",
            total_steps=4,
        )
        updated = await pipeline_repo.update_job_status(
            job.id,
            status="running",
            step_name="ocr",
            step_index=0,
        )
        assert updated.status == "running"
        assert updated.current_step_name == "ocr"
        assert updated.current_step_index == 0
        assert updated.started_at is not None

    async def test_update_job_status_to_completed(self, db_session: AsyncSession):
        """Updating job to 'completed' sets completed_at."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id,
            pipeline_type="formation",
            total_steps=4,
        )
        await pipeline_repo.update_job_status(job.id, "running", step_name="ocr", step_index=0)
        updated = await pipeline_repo.update_job_status(job.id, "completed")
        assert updated.status == "completed"
        assert updated.completed_at is not None

    async def test_job_lock_unlock(self, db_session: AsyncSession):
        """Locking a job sets locked_by and locked_at; unlock clears them."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id,
            pipeline_type="formation",
            total_steps=4,
        )
        locked = await pipeline_repo.lock_job(job.id, "worker-1")
        assert locked.locked_by == "worker-1"
        assert locked.locked_at is not None

        unlocked = await pipeline_repo.unlock_job(job.id)
        assert unlocked.locked_by is None
        assert unlocked.locked_at is None

    async def test_get_queued_jobs(self, db_session: AsyncSession):
        """get_queued_jobs returns queued jobs ordered by priority."""
        doc = await self._create_document(db_session, "queued")
        pipeline_repo = PipelineRepository(db_session)

        # Create two jobs: high priority and normal
        job1 = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation",
            total_steps=4, priority=10,
        )
        job2 = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="indexation",
            total_steps=1, priority=1,
        )

        queued = await pipeline_repo.get_queued_jobs(limit=5)
        # job1 (priority 10) should come before job2 (priority 1)
        assert len(queued) >= 2
        assert queued[0].id == job1.id  # highest priority first

    async def test_get_queued_jobs_filter_by_type(self, db_session: AsyncSession):
        """get_queued_jobs filters by pipeline_type."""
        doc = await self._create_document(db_session, "filter")
        pipeline_repo = PipelineRepository(db_session)
        await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation", total_steps=4,
        )
        await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="indexation", total_steps=1,
        )
        formation_jobs = await pipeline_repo.get_queued_jobs(
            pipeline_type="formation", limit=10
        )
        for j in formation_jobs:
            assert j.pipeline_type == "formation"

    async def test_set_job_error(self, db_session: AsyncSession):
        """set_job_error records error info and increments retry."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation", total_steps=4,
        )
        errored = await pipeline_repo.set_job_error(
            job.id, "OCR_ERROR", "OCR failed"
        )
        assert errored.error_code == "OCR_ERROR"
        assert errored.error_message == "OCR failed"
        assert errored.retry_count == 1

    async def test_stale_running_jobs(self, db_session: AsyncSession):
        """get_stale_running_jobs finds jobs that have been running too long."""
        doc = await self._create_document(db_session, "stale")
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation", total_steps=4,
        )
        # Set to running with very old started_at
        await pipeline_repo.update_job_status(job.id, "running", step_name="ocr", step_index=0)
        # Manually set started_at in the past
        from datetime import datetime, timedelta, timezone
        job = await pipeline_repo.get_job_for_update(job.id)
        job.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await db_session.flush()

        stale = await pipeline_repo.get_stale_running_jobs(max_running_seconds=3600)
        assert len(stale) == 1
        assert stale[0].id == job.id

    # ------------------------------------------------------------------
    # PipelineStepLog
    # ------------------------------------------------------------------

    async def test_create_step_log(self, db_session: AsyncSession):
        """Creating a step log returns it with status=pending."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation", total_steps=4,
        )
        log = await pipeline_repo.create_step_log(
            job_id=job.id,
            document_id=doc.id,
            step_name="ocr",
            step_index=0,
        )
        assert log.step_name == "ocr"
        assert log.status == "pending"

    async def test_step_log_lifecycle(self, db_session: AsyncSession):
        """Step log transitions through pending -> running -> success."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation", total_steps=4,
        )
        log = await pipeline_repo.create_step_log(
            job_id=job.id,
            document_id=doc.id,
            step_name="ocr",
            step_index=0,
        )

        started = await pipeline_repo.start_step_log(log.id)
        assert started.status == "running"
        assert started.started_at is not None

        completed = await pipeline_repo.complete_step_log(
            log.id, output_ref="ref/ocr/result"
        )
        assert completed.status == "success"
        assert completed.output_ref == "ref/ocr/result"

    async def test_step_log_fail(self, db_session: AsyncSession):
        """Marking step as failed records error info."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation", total_steps=4,
        )
        log = await pipeline_repo.create_step_log(
            job_id=job.id,
            document_id=doc.id,
            step_name="ocr",
            step_index=0,
        )
        await pipeline_repo.start_step_log(log.id)
        failed = await pipeline_repo.fail_step_log(log.id, "ERR", "msg")
        assert failed.status == "failed"
        assert failed.error_code == "ERR"
        assert failed.error_message == "msg"

    async def test_step_log_compensate(self, db_session: AsyncSession):
        """Marking step as compensated."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation", total_steps=4,
        )
        log = await pipeline_repo.create_step_log(
            job_id=job.id,
            document_id=doc.id,
            step_name="ocr",
            step_index=0,
        )
        compensated = await pipeline_repo.compensate_step_log(log.id)
        assert compensated.status == "compensated"

    async def test_get_step_logs_for_job(self, db_session: AsyncSession):
        """get_step_logs_for_job returns logs ordered by step_index."""
        doc = await self._create_document(db_session)
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.create_job(
            document_id=doc.id, pipeline_type="formation", total_steps=4,
        )
        logs = []
        for name, idx in [("ocr", 0), ("parser", 1), ("converter", 2), ("registry", 3)]:
            log = await pipeline_repo.create_step_log(
                job_id=job.id, document_id=doc.id, step_name=name, step_index=idx
            )
            logs.append(log)

        fetched = await pipeline_repo.get_step_logs_for_job(job.id)
        assert len(fetched) == 4
        for i, log in enumerate(fetched):
            assert log.step_index == i  # Ordered by step_index
