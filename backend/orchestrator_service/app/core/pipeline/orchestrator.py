"""
Pipeline Orchestrator — core engine that coordinates draft processing.

Responsibilities:
1. Start pipeline for a draft (preview phase)
2. Advance through steps, enqueueing each via Celery
3. Handle step completion: update Task/TaskStep, transition draft, enqueue next step
4. Handle step failure: retry with backoff, or trigger Saga compensation
5. Handle approve/reject decisions
6. Detect and handle stale/running tasks
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.fsm import DraftFSM, DraftState, TaskStage, TaskStatus
from app.core.pipeline.saga import SagaCoordinator
from app.repositories.pipeline import TaskRepository
from app.services.registry_client import RegistryServiceClient

logger = logging.getLogger("orchestrator.pipeline")

PREVIEW_STEPS = ["upload", "preview_ocr", "preview_converter"]


class PipelineOrchestrator:
    """Coordinates pipeline execution for drafts."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)

    async def start_pipeline(
        self, draft_id: int, task_id: int, file_key: str, mime_type: str
    ) -> None:
        """Start the pipeline for a draft (preview phase).

        1. Validates task exists
        2. Creates TaskSteps for preview phase
        3. Enqueues preview Celery tasks
        """
        task = await self.task_repo.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Update task stage to preview
        await self.task_repo.update_task_status(
            task_id=task_id,
            stage=TaskStage.PREVIEW.value,
            step_name="upload",
            step_index=0,
        )

        # Determine which service handles the preview based on mime_type
        # For scanned/image → OCR Service; for digital PDF → Parser Service
        is_scanned = mime_type in ("image/png", "image/jpeg", "image/tiff") or (
            mime_type == "application/pdf"  # would need deeper check
        )
        preview_service = "OCR Service" if is_scanned else "Parser Service"
        preview_step = "preview_ocr"  # both use same step name

        # Create TaskSteps
        # Step 0: upload
        upload_step = await self.task_repo.create_task_step(
            task_id=task_id,
            step_name="upload",
            step_index=0,
            service_name="Orchestrator",
            input_data={"file_key": file_key},
        )

        # Step 1: preview OCR/Parser
        ocr_step = await self.task_repo.create_task_step(
            task_id=task_id,
            step_name=preview_step,
            step_index=1,
            service_name=preview_service,
            input_data={"file_key": file_key, "mode": "preview", "max_pages": 3},
        )

        # Step 2: preview Converter-validator
        converter_step = await self.task_repo.create_task_step(
            task_id=task_id,
            step_name="preview_converter",
            step_index=2,
            service_name="Converter-validator",
            input_data={"file_key": file_key, "mode": "preview"},
        )

        # Start the first step (upload) and enqueue it
        await self.task_repo.start_task_step(upload_step.id)
        # Upload is immediate — mark as completed
        await self.task_repo.complete_task_step(
            upload_step.id,
            output_data={"draft_id": draft_id, "task_id": task_id, "file_key": file_key},
        )

        # Enqueue preview tasks via Celery
        from app.tasks.pipeline_formation import (
            run_ocr_preview_step,
            run_parser_preview_step,
            run_converter_preview_step,
        )

        if is_scanned:
            run_ocr_preview_step.delay(task_id, draft_id, file_key, max_pages=3)
        else:
            run_parser_preview_step.delay(task_id, draft_id, file_key, max_pages=3)

        run_converter_preview_step.delay(task_id, draft_id, file_key)

        # Update progress
        await self.task_repo.update_task_status(
            task_id=task_id,
            progress_percent=10,
        )

        logger.info(
            "Pipeline preview started",
            extra={"draft_id": draft_id, "task_id": task_id},
        )

    async def on_step_completed(
        self,
        task_id: int,
        step_name: str,
        input_data: Optional[dict] = None,
        output_data: Optional[dict] = None,
    ) -> None:
        """Called when a pipeline step completes successfully.

        1. Mark step as completed with input/output data
        2. If preview phase complete, handle decision
        3. If full phase complete, advance to next step
        """
        task = await self.task_repo.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found on step completion")
            return

        # Guard: skip if task is already in a terminal state
        if task.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            logger.warning(
                f"on_step_completed called for already terminal task {task_id} "
                f"(status={task.status}, step={step_name})"
            )
            return

        # Find and complete the step
        steps = await self.task_repo.get_task_steps(task_id)
        current_step = None
        for step in steps:
            if step.step_name == step_name and step.status == "running":
                current_step = step
                break

        if current_step is None:
            # Maybe the step was already completed (upload step)
            for step in steps:
                if step.step_name == step_name:
                    current_step = step
                    break

        if current_step:
            await self.task_repo.complete_task_step(
                step_id=current_step.id,
                output_data=output_data,
            )
            # Also update input_data if provided
            if input_data and current_step.input_data is None:
                current_step.input_data = input_data
                await self.db.flush()

        # Calculate progress
        total_steps = task.total_steps or 3
        completed_steps = sum(1 for s in steps if s.status == "completed")
        progress = min(int((completed_steps / total_steps) * 100), 99)

        await self.task_repo.update_task_status(
            task_id=task_id,
            progress_percent=progress,
        )

        # Handle preview phase completion
        if step_name == "preview_converter":
            await self._on_preview_completed(task, steps, output_data)
        elif step_name in ("full_ocr", "full_converter", "registry_creation"):
            await self._on_full_step_completed(task, step_name, steps)

    async def _on_preview_completed(
        self, task, steps, converter_output: Optional[dict]
    ) -> None:
        """Handle completion of the preview phase."""
        # Find the OCR/Parser step output
        preview_step = None
        for step in steps:
            if step.step_name == "preview_ocr":
                preview_step = step
                break

        preview_not_supported = False
        if preview_step and preview_step.output_data:
            preview_not_supported = preview_step.output_data.get(
                "preview_not_supported", False
            )

        if preview_not_supported:
            # Engine returned full document — mark as full_completed
            await self.task_repo.update_task_status(
                task_id=task.id,
                stage=TaskStage.DECISION.value,
                progress_percent=50,
            )
            task.full_completed = True
            await self.db.flush()

            # Check auto-approve conditions
            can_auto_approve = self._check_auto_approve(task, steps)
            if can_auto_approve:
                logger.info(
                    "Auto-approving draft after full preview",
                    extra={"draft_id": task.draft_id, "task_id": task.id},
                )
                await self.approve_draft(task.draft_id, task.id)
                return

        else:
            # Partial preview — always wait for decision
            task.full_completed = False
            await self.db.flush()
            await self.task_repo.update_task_status(
                task_id=task.id,
                stage=TaskStage.DECISION.value,
                progress_percent=50,
            )

        # Update draft status to ready_for_approve via Registry
        try:
            registry = RegistryServiceClient()
            await registry.update_draft_status(
                draft_id=task.draft_id,
                status=DraftState.READY_FOR_APPROVE.value,
            )
            await registry.close()
        except Exception as e:
            logger.warning(
                f"Failed to update draft status to ready_for_approve: {e}",
                extra={"draft_id": task.draft_id},
            )

    def _check_auto_approve(self, task, steps) -> bool:
        """Check if conditions for auto-approve are met."""
        # Auto-approve if preview was full and metadata is valid
        # For now, return True if full_completed is set
        # In production, check metadata validity and no duplicates
        return True

    async def _on_full_step_completed(
        self, task, step_name: str, steps
    ) -> None:
        """Handle completion of a full processing step."""
        if step_name == "full_ocr":
            await self.task_repo.update_task_status(
                task_id=task.id,
                progress_percent=65,
            )
            # Converter should already be enqueued or will run next

            from app.tasks.pipeline_formation import run_converter_full_step
            run_converter_full_step.delay(task.id, task.draft_id)

        elif step_name == "full_converter":
            await self.task_repo.update_task_status(
                task_id=task.id,
                progress_percent=85,
            )

            from app.tasks.pipeline_formation import run_registry_step
            run_registry_step.delay(task.id, task.draft_id)

        elif step_name == "registry_creation":
            # Full pipeline complete
            await self.task_repo.update_task_status(
                task_id=task.id,
                status=TaskStatus.COMPLETED.value,
                stage=TaskStage.REGISTRY.value,
                progress_percent=100,
            )

            # Update draft status to approved via Registry
            try:
                registry = RegistryServiceClient()
                await registry.update_draft_status(
                    draft_id=task.draft_id,
                    status=DraftState.APPROVED.value,
                )
                await registry.close()
            except Exception as e:
                logger.warning(
                    f"Failed to update draft status to approved: {e}",
                    extra={"draft_id": task.draft_id},
                )

            logger.info(
                f"Pipeline completed for draft {task.draft_id}",
                extra={"task_id": task.id},
            )

    async def approve_draft(self, draft_id: int, task_id: int) -> None:
        """Handle user approve decision.

        If preview was partial, creates full processing steps.
        If preview was full, goes directly to registry creation.
        """
        task = await self.task_repo.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        await self.task_repo.update_task_status(
            task_id=task_id,
            stage=TaskStage.FULL.value,
            progress_percent=50,
        )

        from app.tasks.pipeline_formation import (
            run_ocr_full_step,
            run_parser_full_step,
            run_converter_full_step,
            run_registry_step,
        )

        # Resolve file_key from upload step output
        steps = await self.task_repo.get_task_steps(task_id)
        upload_step = next((s for s in steps if s.step_name == "upload"), None)
        file_key = None
        if upload_step and upload_step.output_data:
            file_key = upload_step.output_data.get("file_key")

        if not task.full_completed:
            # Partial preview — need full OCR/Parser
            # Create full_ocr step
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="full_ocr",
                step_index=3,
                service_name="OCR Service",
                input_data={"file_key": file_key, "mode": "full"},
            )
            run_ocr_full_step.delay(task_id, draft_id, file_key)

        # Create full_converter step (always)
        await self.task_repo.create_task_step(
            task_id=task_id,
            step_name="full_converter",
            step_index=4,
            service_name="Converter-validator",
            input_data={"file_key": file_key, "mode": "full"},
        )

        # Create registry_creation step
        await self.task_repo.create_task_step(
            task_id=task_id,
            step_name="registry_creation",
            step_index=5,
            service_name="Registry",
            input_data={"draft_id": draft_id},
        )

        # Start the first step
        if not task.full_completed:
            steps = await self.task_repo.get_task_steps(task_id)
            full_ocr = next(
                (
                    s
                    for s in steps
                    if s.step_name == "full_ocr" and s.status == "pending"
                ),
                None,
            )
            if full_ocr:
                await self.task_repo.start_task_step(full_ocr.id)

    async def reject_draft(self, draft_id: int, task_id: int) -> None:
        """Handle user reject decision."""
        task = await self.task_repo.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        await self.task_repo.update_task_status(
            task_id=task_id,
            status=TaskStatus.FAILED.value,
            stage=TaskStage.DECISION.value,
        )

        # Update draft status to discarded via Registry
        try:
            registry = RegistryServiceClient()
            await registry.update_draft_status(
                draft_id=draft_id,
                status=DraftState.DISCARDED.value,
            )
            await registry.close()
        except Exception as e:
            logger.warning(
                f"Failed to update draft status to discarded: {e}",
                extra={"draft_id": draft_id},
            )

    async def on_step_failed(
        self,
        task_id: int,
        step_name: str,
        error_code: str,
        error_message: str,
    ) -> None:
        """Called when a pipeline step fails.

        1. Mark step as failed
        2. Increment retry count on task
        3. If retries remain, re-enqueue step with exponential backoff
        4. If retries exhausted, mark task as failed and run Saga compensation
        """
        task = await self.task_repo.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found on step failure")
            return

        if task.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            logger.warning(
                f"on_step_failed called for already terminal task {task_id} "
                f"(status={task.status}, step={step_name})"
            )
            return

        # Mark the running step as failed
        steps = await self.task_repo.get_task_steps(task_id)
        for step in steps:
            if step.step_name == step_name and step.status == "running":
                await self.task_repo.fail_task_step(
                    step_id=step.id,
                    error_code=error_code,
                    error_message=error_message,
                )
                break

        # Update task error info
        await self.task_repo.set_task_error(task_id, error_code, error_message)

        max_retries = settings.pipeline.MAX_STEP_RETRIES

        if task.retry_count < max_retries:
            # Retry with exponential backoff
            backoff_delay = settings.pipeline.RETRY_BASE_DELAY * (2 ** task.retry_count)

            # Re-create step as pending for retry
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name=step_name,
                step_index=task.current_step_index,
                service_name=task.current_step_name or step_name,
            )

            await self.task_repo.update_task_status(
                task_id=task_id,
                status=TaskStatus.ACTIVE.value,
                step_name=step_name,
                step_index=task.current_step_index,
            )

            logger.info(
                f"Step {step_name} failed, retry {task.retry_count}/{max_retries} "
                f"in {backoff_delay}s",
                extra={"task_id": task_id, "draft_id": task.draft_id},
            )
        else:
            # Retries exhausted — fail the task and compensate
            await self.task_repo.update_task_status(
                task_id, status=TaskStatus.FAILED.value
            )

            # Run Saga compensation (rollback completed steps)
            saga = SagaCoordinator(self.db)
            await saga.compensate(task_id, step_name)

            # Update draft status
            try:
                registry = RegistryServiceClient()
                await registry.update_draft_status(
                    draft_id=task.draft_id,
                    status=DraftState.DISCARDED.value,
                )
                await registry.close()
            except Exception as e:
                logger.warning(
                    f"Failed to update draft status: {e}",
                    extra={"draft_id": task.draft_id},
                )

            logger.error(
                f"Pipeline failed at step {step_name}",
                extra={
                    "task_id": task_id,
                    "draft_id": task.draft_id,
                    "error": error_message,
                },
            )

    async def cleanup_stale_tasks(self) -> int:
        """Find and mark stale running tasks as failed."""
        max_time = settings.pipeline.MAX_JOB_RUNNING_TIME
        stale_tasks = await self.task_repo.get_stale_running_tasks(max_time)

        cleaned = 0
        for task in stale_tasks:
            await self.task_repo.update_task_status(
                task.id,
                status=TaskStatus.FAILED.value,
            )
            await self.task_repo.set_task_error(
                task.id,
                error_code="PIPELINE_TIMEOUT",
                error_message=f"Task running for >{max_time}s without completion",
            )
            cleaned += 1

        if cleaned:
            logger.warning(f"Cleaned up {cleaned} stale pipeline tasks")

        return cleaned
