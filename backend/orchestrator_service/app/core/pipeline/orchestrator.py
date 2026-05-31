"""
Pipeline Orchestrator — core engine that coordinates document processing.

Responsibilities:
1. Start Pipeline 1 (formation) or Pipeline 2 (indexation) for a document
2. Advance through steps, enqueueing each via Celery
3. Handle step completion: transition FSM, enqueue next step
4. Handle step failure: retry with backoff, or trigger Saga compensation
5. Detect and handle stale/running jobs

The orchestrator uses Repository pattern for DB operations and Celery
for async task execution. All FSM transitions are atomic (FOR UPDATE).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.fsm import (
    DocumentFSM,
    InvalidTransitionError,
    PIPELINE_1_STEPS,
    PIPELINE_2_STEPS,
    STEP_TO_STATE_MAP,
)
from app.core.pipeline.saga import SagaCoordinator
from app.repositories.document import DocumentRepository
from app.repositories.pipeline import PipelineRepository

logger = logging.getLogger("orchestrator.pipeline")


class PipelineOrchestrator:
    """Coordinates pipeline execution for documents."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.pipeline_repo = PipelineRepository(db)
        self.saga = SagaCoordinator(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start_pipeline_1(self, document_id: str) -> str:
        """Start Pipeline 1 (formation) for a document.

        1. Validates document exists and is in 'uploaded' state
        2. Creates a PipelineJob record
        3. Creates step logs for all steps (pending)
        4. Enqueues the first step via DB (Celery picks it up)
        5. Transitions document FSM to 'previewing'

        Returns the job ID.
        """
        doc = await self.doc_repo.get(document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        # Transition FSM: uploaded -> previewing
        DocumentFSM.validate_transition(doc.status, "previewing")

        # Create job
        job = await self.pipeline_repo.create_job(
            document_id=document_id,
            pipeline_type="formation",
            total_steps=len(PIPELINE_1_STEPS),
        )

        # Create step logs (all as pending, first will be started)
        for idx, step_name in enumerate(PIPELINE_1_STEPS):
            await self.pipeline_repo.create_step_log(
                job_id=job.id,
                document_id=document_id,
                step_name=step_name,
                step_index=idx,
            )

        # Set job as running + lock it
        await self.pipeline_repo.update_job_status(
            job_id=job.id,
            status="running",
            step_name=PIPELINE_1_STEPS[0],
            step_index=0,
        )
        await self.pipeline_repo.lock_job(job.id, "orchestrator")

        # Transition doc FSM
        await self.doc_repo.fsm_transition(document_id, "previewing")

        # Start the first step log
        step_logs = await self.pipeline_repo.get_step_logs_for_job(job.id)
        if step_logs:
            await self.pipeline_repo.start_step_log(step_logs[0].id)

        logger.info(
            "Pipeline 1 started",
            extra={
                "document_id": document_id,
                "job_id": job.id,
                "first_step": PIPELINE_1_STEPS[0],
            },
        )

        return job.id

    async def start_pipeline_2(self, document_id: str) -> str:
        """Start Pipeline 2 (indexation) for a document.

        Triggered automatically after Pipeline 1 completes successfully
        (registry -> pending_index transition).
        """
        doc = await self.doc_repo.get(document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        DocumentFSM.validate_transition(doc.status, "pending_index")

        job = await self.pipeline_repo.create_job(
            document_id=document_id,
            pipeline_type="indexation",
            total_steps=len(PIPELINE_2_STEPS),
        )

        for idx, step_name in enumerate(PIPELINE_2_STEPS):
            await self.pipeline_repo.create_step_log(
                job_id=job.id,
                document_id=document_id,
                step_name=step_name,
                step_index=idx,
            )

        await self.pipeline_repo.update_job_status(
            job_id=job.id,
            status="running",
            step_name=PIPELINE_2_STEPS[0],
            step_index=0,
        )
        await self.pipeline_repo.lock_job(job.id, "orchestrator")

        await self.doc_repo.fsm_transition(document_id, "pending_index")

        step_logs = await self.pipeline_repo.get_step_logs_for_job(job.id)
        if step_logs:
            await self.pipeline_repo.start_step_log(step_logs[0].id)

        logger.info(
            "Pipeline 2 started",
            extra={"document_id": document_id, "job_id": job.id},
        )

        return job.id

    async def on_step_completed(
        self,
        job_id: str,
        step_name: str,
        result: Optional[dict] = None,
    ) -> None:
        """Called when a pipeline step completes successfully.

        1. Mark step log as completed
        2. Transition document FSM if mapped
        3. Advance to next step, or complete the pipeline
        """
        job = await self.pipeline_repo.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found on step completion")
            return

        # Find the step log for this step and mark complete
        step_logs = await self.pipeline_repo.get_step_logs_for_job(job_id)
        current_log = None
        for log in step_logs:
            if log.step_name == step_name and log.status == "running":
                current_log = log
                break

        if current_log:
            result_ref = None
            if result:
                result_ref = f"{job.document_id}/{step_name}/result"
            await self.pipeline_repo.complete_step_log(
                log_id=current_log.id,
                output_ref=result_ref,
            )

        # Transition FSM based on step
        target_state = DocumentFSM.get_step_transition(step_name)
        if target_state:
            try:
                await self.doc_repo.fsm_transition(job.document_id, target_state)
            except Exception as e:
                logger.warning(
                    f"FSM transition to {target_state} failed: {e}",
                    extra={"document_id": job.document_id},
                )

        # Determine next step
        next_step_index = job.current_step_index + 1

        if next_step_index < job.total_steps:
            # Enqueue next step
            next_step_name = (
                PIPELINE_1_STEPS[next_step_index]
                if job.pipeline_type == "formation"
                else PIPELINE_2_STEPS[next_step_index]
            )

            await self.pipeline_repo.update_job_status(
                job_id=job_id,
                status="running",
                step_name=next_step_name,
                step_index=next_step_index,
            )

            # Start the next step log
            for log in step_logs:
                if log.step_name == next_step_name and log.status == "pending":
                    await self.pipeline_repo.start_step_log(log.id)
                    break

            logger.info(
                f"Pipeline step completed: {step_name}, next: {next_step_name}",
                extra={"job_id": job_id, "document_id": job.document_id},
            )
        else:
            # Pipeline complete
            await self.pipeline_repo.update_job_status(job_id, "completed")
            await self.pipeline_repo.unlock_job(job_id)

            # If Pipeline 1 finished, auto-start Pipeline 2
            if job.pipeline_type == "formation" and target_state == "registry":
                try:
                    await self.start_pipeline_2(job.document_id)
                except Exception as e:
                    logger.error(
                        f"Failed to auto-start Pipeline 2: {e}",
                        extra={"document_id": job.document_id},
                    )

            logger.info(
                f"Pipeline {job.pipeline_type} completed",
                extra={"job_id": job_id, "document_id": job.document_id},
            )

    async def on_step_failed(
        self,
        job_id: str,
        step_name: str,
        error_code: str,
        error_message: str,
    ) -> None:
        """Called when a pipeline step fails.

        1. Mark step log as failed
        2. Increment retry count on job
        3. If retries remain, re-enqueue step with exponential backoff
        4. If retries exhausted, mark job as failed and run Saga compensation
        """
        job = await self.pipeline_repo.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found on step failure")
            return

        # Mark the running step log as failed
        step_logs = await self.pipeline_repo.get_step_logs_for_job(job_id)
        for log in step_logs:
            if log.step_name == step_name and log.status == "running":
                await self.pipeline_repo.fail_step_log(
                    log_id=log.id,
                    error_code=error_code,
                    error_message=error_message,
                )
                break

        # Update job error info
        await self.pipeline_repo.set_job_error(job_id, error_code, error_message)

        max_retries = settings.pipeline.MAX_STEP_RETRIES

        if job.retry_count < max_retries:
            # Retry with exponential backoff
            backoff_delay = settings.pipeline.RETRY_BASE_DELAY * (2 ** job.retry_count)

            # Reset step log to pending
            for log in step_logs:
                if log.step_name == step_name and log.status == "failed":
                    # Re-create as pending for retry
                    await self.pipeline_repo.create_step_log(
                        job_id=job_id,
                        document_id=job.document_id,
                        step_name=step_name,
                        step_index=job.current_step_index,
                    )
                    break

            await self.pipeline_repo.update_job_status(
                job_id=job_id,
                status="running",
                step_name=step_name,
                step_index=job.current_step_index,
            )

            logger.info(
                f"Step {step_name} failed, retry {job.retry_count}/{max_retries} "
                f"in {backoff_delay}s",
                extra={"job_id": job_id, "document_id": job.document_id},
            )
        else:
            # Retries exhausted — fail the job and compensate
            await self.pipeline_repo.update_job_status(job_id, "failed")

            # Mark document as failed
            await self.doc_repo.set_error(
                job.document_id,
                error_code=error_code,
                error_message=error_message,
            )

            # Run Saga compensation (rollback completed steps)
            await self.saga.compensate(job_id, step_name)

            logger.error(
                f"Pipeline {job.pipeline_type} failed at step {step_name}",
                extra={
                    "job_id": job_id,
                    "document_id": job.document_id,
                    "error": error_message,
                },
            )

    async def cleanup_stale_jobs(self) -> int:
        """Find and mark stale running jobs as dead.

        Returns the number of jobs cleaned up.
        """
        max_time = settings.pipeline.MAX_JOB_RUNNING_TIME
        stale_jobs = await self.pipeline_repo.get_stale_running_jobs(max_time)

        cleaned = 0
        for job in stale_jobs:
            await self.pipeline_repo.update_job_status(job.id, "dead")
            # Mark document as failed
            await self.doc_repo.set_error(
                job.document_id,
                error_code="PIPELINE_TIMEOUT",
                error_message=f"Pipeline job running for >{max_time}s without completion",
            )
            cleaned += 1

        if cleaned:
            logger.warning(f"Cleaned up {cleaned} stale pipeline jobs")

        return cleaned
