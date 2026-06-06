"""
Pipeline repository — CRUD operations for PipelineJob and PipelineStepLog.

Manages the lifecycle of pipeline execution records.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import PipelineJob, PipelineStepLog


class PipelineRepository:
    """Repository for PipelineJob and PipelineStepLog entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # PipelineJob
    # ------------------------------------------------------------------

    async def create_job(
        self,
        document_id: str,
        pipeline_type: str,
        total_steps: int,
        priority: int = 5,
    ) -> PipelineJob:
        """Create a new pipeline job."""
        job = PipelineJob(
            id=str(uuid.uuid4()),
            document_id=document_id,
            pipeline_type=pipeline_type,
            status="queued",
            priority=priority,
            total_steps=total_steps,
            current_step_index=0,
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_job(self, job_id: str) -> Optional[PipelineJob]:
        """Get job by ID."""
        result = await self.db.execute(
            select(PipelineJob).where(PipelineJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_job_for_update(self, job_id: str) -> Optional[PipelineJob]:
        """Get job with FOR UPDATE lock."""
        result = await self.db.execute(
            select(PipelineJob)
            .where(PipelineJob.id == job_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        step_name: Optional[str] = None,
        step_index: Optional[int] = None,
    ) -> Optional[PipelineJob]:
        """Update job status and optionally current step info."""
        job = await self.get_job_for_update(job_id)
        if job is None:
            return None
        job.status = status
        if step_name is not None:
            job.current_step_name = step_name
        if step_index is not None:
            job.current_step_index = step_index
        if status == "running" and job.started_at is None:
            job.started_at = datetime.now(timezone.utc)
        if status in ("completed", "failed", "dead"):
            job.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return job

    async def lock_job(self, job_id: str, worker_id: str) -> Optional[PipelineJob]:
        """Lock a job for exclusive processing by a worker."""
        job = await self.get_job_for_update(job_id)
        if job is None:
            return None
        job.locked_by = worker_id
        job.locked_at = datetime.now(timezone.utc)
        await self.db.flush()
        return job

    async def unlock_job(self, job_id: str) -> Optional[PipelineJob]:
        """Release lock on a job."""
        job = await self.get_job_for_update(job_id)
        if job is None:
            return None
        job.locked_by = None
        job.locked_at = None
        await self.db.flush()
        return job

    async def get_queued_jobs(
        self, pipeline_type: Optional[str] = None, limit: int = 10
    ) -> list[PipelineJob]:
        """Get next queued jobs, ordered by priority (highest first)."""
        query = select(PipelineJob).where(PipelineJob.status == "queued")
        if pipeline_type:
            query = query.where(PipelineJob.pipeline_type == pipeline_type)
        query = query.order_by(PipelineJob.priority.desc(), PipelineJob.created_at.asc())
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_stale_running_jobs(
        self, max_running_seconds: int = 3600
    ) -> list[PipelineJob]:
        """Find jobs that have been running too long (dead jobs)."""
        from datetime import timedelta
        threshold = datetime.now(timezone.utc) - timedelta(seconds=max_running_seconds)
        result = await self.db.execute(
            select(PipelineJob).where(
                and_(
                    PipelineJob.status == "running",
                    PipelineJob.started_at < threshold,
                )
            )
        )
        return list(result.scalars().all())

    async def set_job_error(
        self, job_id: str, error_code: str, error_message: str
    ) -> Optional[PipelineJob]:
        """Record an error on a job."""
        job = await self.get_job_for_update(job_id)
        if job is None:
            return None
        job.error_code = error_code
        job.error_message = error_message
        job.retry_count = job.retry_count + 1
        await self.db.flush()
        return job

    # ------------------------------------------------------------------
    # PipelineStepLog
    # ------------------------------------------------------------------

    async def create_step_log(
        self,
        job_id: str,
        document_id: str,
        step_name: str,
        step_index: int,
    ) -> PipelineStepLog:
        """Create a step log entry (status: pending)."""
        log = PipelineStepLog(
            job_id=job_id,
            document_id=document_id,
            step_name=step_name,
            step_index=step_index,
            status="pending",
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def start_step_log(self, log_id: int) -> Optional[PipelineStepLog]:
        """Mark step as running."""
        result = await self.db.execute(
            select(PipelineStepLog)
            .where(PipelineStepLog.id == log_id)
            .with_for_update()
        )
        log = result.scalar_one_or_none()
        if log is None:
            return None
        log.status = "running"
        log.started_at = datetime.now(timezone.utc)
        await self.db.flush()
        return log

    async def complete_step_log(
        self,
        log_id: int,
        output_ref: Optional[str] = None,
    ) -> Optional[PipelineStepLog]:
        """Mark step as completed successfully."""
        result = await self.db.execute(
            select(PipelineStepLog)
            .where(PipelineStepLog.id == log_id)
            .with_for_update()
        )
        log = result.scalar_one_or_none()
        if log is None:
            return None
        log.status = "success"
        log.completed_at = datetime.now(timezone.utc)
        if output_ref:
            log.output_ref = output_ref
        await self.db.flush()
        return log

    async def fail_step_log(
        self,
        log_id: int,
        error_code: str,
        error_message: str,
    ) -> Optional[PipelineStepLog]:
        """Mark step as failed."""
        result = await self.db.execute(
            select(PipelineStepLog)
            .where(PipelineStepLog.id == log_id)
            .with_for_update()
        )
        log = result.scalar_one_or_none()
        if log is None:
            return None
        log.status = "failed"
        log.completed_at = datetime.now(timezone.utc)
        log.error_code = error_code
        log.error_message = error_message
        await self.db.flush()
        return log

    async def compensate_step_log(self, log_id: int) -> Optional[PipelineStepLog]:
        """Mark step as compensated."""
        result = await self.db.execute(
            select(PipelineStepLog)
            .where(PipelineStepLog.id == log_id)
            .with_for_update()
        )
        log = result.scalar_one_or_none()
        if log is None:
            return None
        log.status = "compensated"
        await self.db.flush()
        return log

    async def get_step_logs_for_job(self, job_id: str) -> list[PipelineStepLog]:
        """Get all step logs for a job, ordered by step index."""
        result = await self.db.execute(
            select(PipelineStepLog)
            .where(PipelineStepLog.job_id == job_id)
            .order_by(PipelineStepLog.step_index)
        )
        return list(result.scalars().all())
