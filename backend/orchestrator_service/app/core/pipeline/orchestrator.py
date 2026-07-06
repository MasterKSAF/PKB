"""
Pipeline Orchestrator — core engine that coordinates draft processing.

Responsibilities:
1. Start pipeline for a draft (preview phase)
2. Advance through steps, enqueueing each via Celery
3. Handle step completion: update Task/TaskStep, transition draft, enqueue next step
4. Handle step failure: retry with backoff, or trigger Saga compensation
5. Handle approve/reject decisions (external UI actions)
6. Handle proceed/stop_duplicate/force_new_version (internal actions)
7. Detect and handle stale/running tasks
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.fsm import DraftFSM, DraftState, TaskStage, TaskStatus
from app.models.pipeline import Task
from app.core.pipeline.saga import SagaCoordinator
from app.core.trace import get_trace_id, set_trace_id
from app.repositories.pipeline import TaskRepository
from app.services.registry_client import RegistryServiceClient

logger = logging.getLogger("orchestrator.pipeline")

PREVIEW_STEPS = ["upload", "preview_ocr", "preview_converter"]


class ConcurrentTaskLimitError(ValueError):
    """Raised when concurrent task limit is exceeded."""


class PipelineOrchestrator:
    """Coordinates pipeline execution for drafts."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)

    async def _has_free_slot(self) -> bool:
        """Check if a concurrent execution slot is available.

        Returns True if the number of active tasks is below MAX_CONCURRENT_TASKS.
        Defensive: non-int return treated as no slot.
        """
        active = await self.task_repo.count_active_tasks()
        if not isinstance(active, int):
            logger.warning(
                "count_active_tasks returned non-int",
                extra={"type": type(active).__name__},
            )
            return False
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        if active >= limit:
            logger.warning(
                "No free execution slot",
                extra={"active": active, "limit": limit},
            )
            return False
        return True

    async def _enqueue_celery_tasks(
        self, task: Task, file_key: str,
    ) -> None:
        """Dispatch Celery preview tasks for a pipeline.

        Uses task.current_step_name to determine Parser vs OCR.
        The converter step is dispatched later in on_step_completed.
        """
        from app.tasks.pipeline_formation import (
            run_ocr_preview_step,
            run_parser_preview_step,
        )

        current_trace_id = task.trace_id or get_trace_id() or ""
        use_parser = task.current_step_name == "Parser Service"

        if use_parser:
            _params = {
                "task_id": task.id, "draft_id": task.draft_id,
                "file_key": file_key, "max_pages": 3, "trace_id": current_trace_id,
            }
            logger.info(
                "Parser-first: enqueuing celery task",
                extra={
                    "celery_task": "tasks.pipeline.run_parser_preview_step",
                    "queue": "pipeline",
                    "params": _params,
                    "draft_id": task.draft_id, "task_id": task.id,
                },
            )
            run_parser_preview_step.delay(**_params)
        else:
            _params = {
                "task_id": task.id, "draft_id": task.draft_id,
                "file_key": file_key, "max_pages": 3, "trace_id": current_trace_id,
            }
            logger.info(
                "OCR: enqueuing celery task",
                extra={
                    "celery_task": "tasks.pipeline.run_ocr_preview_step",
                    "queue": "pipeline",
                    "params": _params,
                    "draft_id": task.draft_id, "task_id": task.id,
                },
            )
            run_ocr_preview_step.delay(**_params)

        # Converter запускается ПОСЛЕ parser/ocr в on_step_completed
        # с результатом парсинга как raw_json

    async def _enqueue_celery_full_tasks(
        self, task: Task, file_key: str,
    ) -> None:
        """Dispatch Celery full-phase tasks for a pipeline.

        Starts the first full step (full_ocr) based on the step's service_name.
        Subsequent steps (converter, registry, rag_index) are chained
        via on_step_completed → _on_full_step_completed.
        """
        from app.tasks.pipeline_formation import (
            run_ocr_full_step,
            run_parser_full_step,
            run_converter_full_step,
        )

        current_trace_id = task.trace_id or get_trace_id() or ""

        # Get task steps and find pending full_ocr
        steps = await self.task_repo.get_task_steps(task.id)
        full_step = next(
            (s for s in steps if s.step_name == "full_ocr" and s.status == "pending"),
            None,
        )

        if not full_step:
            # No pending full_ocr — check for full_converter (full_preview case)
            full_converter = next(
                (s for s in steps if s.step_name == "full_converter" and s.status == "pending"),
                None,
            )
            if full_converter:
                await self.task_repo.start_task_step(full_converter.id)
                run_converter_full_step.delay(
                    task.id, task.draft_id, file_key, trace_id=current_trace_id,
                )
                logger.info(
                    "Dequeued full converter step (full preview, no Parser/OCR)",
                    extra={"task_id": task.id, "draft_id": task.draft_id},
                )
            else:
                logger.warning(
                    "No pending full_ocr or full_converter step found for dequeued task",
                    extra={"task_id": task.id, "draft_id": task.draft_id},
                )
            return

        # Start full_ocr step and dispatch — use step's service_name to decide engine
        await self.task_repo.start_task_step(full_step.id)
        if full_step.service_name == "Parser Service":
            run_parser_full_step.delay(
                task.id, task.draft_id, file_key, trace_id=current_trace_id,
            )
            logger.info(
                "Dequeued full Parser step (Parser-first)",
                extra={"task_id": task.id, "draft_id": task.draft_id},
            )
        else:
            run_ocr_full_step.delay(
                task.id, task.draft_id, file_key, trace_id=current_trace_id,
            )
            logger.info(
                "Dequeued full OCR step",
                extra={"task_id": task.id, "draft_id": task.draft_id},
            )

    async def _drain_queue(self) -> int:
        """Process queued tasks if execution slots are available.

        Uses try_activate_next_queued_task for atomic slot-check + activate (§3.1).
        FIFO order: picks oldest queued task (by created_at) and dispatches
        its Celery tasks. Continues until all slots are filled or queue is empty.

        Returns:
            int: Number of tasks dequeued and activated.
        """
        dequeued = 0
        while True:
            queued_task = await self.task_repo.try_activate_next_queued_task()
            if not queued_task:
                break

            # Get file_key from upload step output first
            steps = await self.task_repo.get_task_steps(queued_task.id)
            file_key = None
            for s in steps:
                if s.step_name == "upload" and s.output_data:
                    file_key = s.output_data.get("file_key")
                    break
            if not file_key:
                # Fallback: try input_data
                for s in steps:
                    if s.step_name == "upload" and s.input_data:
                        file_key = s.input_data.get("file_key")
                        break

            if not file_key:
                logger.warning(
                    "Cannot dequeue task: no file_key found in upload step, skipping",
                    extra={
                        "task_id": queued_task.id,
                        "draft_id": queued_task.draft_id,
                    },
                )
                # Activate anyway — cleanup_stale_tasks will catch malformed tasks.
                # Don't rollback here: this transaction may include changes from
                # the caller (e.g. on_step_completed already flushed progress).
                continue

            logger.info(
                "Dequeuing task",
                extra={
                    "task_id": queued_task.id,
                    "draft_id": queued_task.draft_id,
                    "stage": queued_task.pipeline_stage,
                },
            )

            # Task already ACTIVE (set inside try_activate_next_queued_task)

            # Choose dispatcher based on pipeline stage
            if queued_task.pipeline_stage in (
                TaskStage.FULL.value,
                TaskStage.REGISTRY.value,
            ):
                await self._enqueue_celery_full_tasks(queued_task, file_key)
            else:
                # Preview phase (default)
                await self._enqueue_celery_tasks(queued_task, file_key)

            logger.info(
                "Queued task activated and dispatched",
                extra={
                    "task_id": queued_task.id,
                    "draft_id": queued_task.draft_id,
                },
            )

            dequeued += 1

        if dequeued:
            logger.info(
                "Queue drain complete",
                extra={"dequeued": dequeued},
            )

        return dequeued

    async def drain_queue(self) -> int:
        """Public wrapper for _drain_queue, used by QueueDrainPoller."""
        return await self._drain_queue()

    async def start_pipeline(
        self, draft_id: int, task_id: int, file_key: str, mime_type: str,
        metadata_fields: Optional[dict] = None,
    ) -> bool:
        """Start the pipeline for a draft (preview phase).

        Parser-first strategy: if Parser is enabled, it is always tried first.
        If Parser fails or returns preview_not_supported and fallback is enabled,
        the pipeline falls back to OCR.

        1. Validates task exists
        2. Creates TaskSteps for preview phase (idempotent — skips existing)
        3. Checks for free execution slot:
           - If slot available: enqueues preview Celery tasks, task stays active
           - If no slot: task is set to queued, Celery tasks are NOT dispatched

        Returns:
            bool: True if Celery tasks were dispatched (active), False if queued.

        Args:
            metadata_fields: Initial metadata from POST /drafts form (source_type, doc_code, etc.)
        """
        task = await self.task_repo.get_task(task_id)
        if not task:
            logger.error(
                "start_pipeline: task not found",
                extra={"task_id": task_id, "draft_id": draft_id},
            )
            raise ValueError(f"Task not found: {task_id}")

        # Set trace_id on the task for propagation to Celery workers
        trace_id = get_trace_id()
        if trace_id and not task.trace_id:
            task.trace_id = trace_id
            await self.db.flush()

        # Update task stage to preview
        await self.task_repo.update_task_status(
            task_id=task_id,
            stage=TaskStage.PREVIEW.value,
            step_name="upload",
            step_index=0,
        )

        # --- Parser-first strategy (P1F-8 updated) ---
        parser_enabled = settings.services.PARSER_ENABLED
        ocr_enabled = settings.services.OCR_ENABLED

        if not parser_enabled and not ocr_enabled:
            raise ValueError(
                f"Cannot start pipeline: both Parser and OCR are disabled "
                f"(draft_id={draft_id}, task_id={task_id})"
            )

        if parser_enabled:
            preview_service = "Parser Service"
            use_parser = True
        elif ocr_enabled:
            preview_service = "OCR Service"
            use_parser = False
        else:
            preview_service = "Parser Service"
            use_parser = True

        # Store service selection on the task for fallback tracking
        task.current_step_name = preview_service
        await self.db.flush()

        # ── Idempotent step creation: check existing steps ──────────────
        existing_steps = await self.task_repo.get_task_steps(task_id)
        existing_step_names = {s.step_name for s in existing_steps}

        # Create TaskSteps (skip if already exist)
        # Step 0: upload
        if "upload" not in existing_step_names:
            upload_input = {"file_key": file_key, "draft_id": draft_id}
            if metadata_fields:
                upload_input["metadata_fields"] = metadata_fields
            upload_step = await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="upload",
                step_index=0,
                service_name="Orchestrator",
                input_data=upload_input,
            )
        else:
            upload_step = next((s for s in existing_steps if s.step_name == "upload"), None)

        # Step 1: preview Parser/OCR
        if "preview_ocr" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="preview_ocr",
                step_index=1,
                service_name=preview_service,
                input_data={"file_key": file_key, "mode": "preview", "max_pages": 3, "draft_id": draft_id},
            )

        # Step 2: preview Converter-validator
        if "preview_converter" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="preview_converter",
                step_index=2,
                service_name="Converter-validator",
                input_data={"file_key": file_key, "mode": "preview", "draft_id": draft_id},
            )

        # Start the first step (upload) and enqueue it
        await self.task_repo.start_task_step(upload_step.id)
        # Upload is immediate — mark as completed
        await self.task_repo.complete_task_step(
            upload_step.id,
            output_data={"draft_id": draft_id, "task_id": task_id, "file_key": file_key},
        )

        # ── Check free slot and dispatch or queue ───────────────────
        # Slot check (приблизительный, точная сериализация через SKIP LOCKED
        # в try_activate_next_queued_task)
        active_count = await self.task_repo.count_active_tasks()
        limit = settings.pipeline.MAX_CONCURRENT_TASKS
        if active_count < limit:
            # Slot available — activate and dispatch immediately
            if task.status != TaskStatus.ACTIVE.value:
                await self.task_repo.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.ACTIVE.value,
                )

            # Dispatch Celery tasks
            await self._enqueue_celery_tasks(task, file_key)

            # Update progress
            await self.task_repo.update_task_progress(
                task_id=task_id,
                progress_percent=10,
            )

            logger.info(
                "Pipeline preview started (active)",
                extra={"draft_id": draft_id, "task_id": task_id},
            )
            return True
        else:
            # No free slot — queue the task
            await self.task_repo.update_task_status(
                task_id=task_id,
                status=TaskStatus.QUEUED.value,
                progress_percent=5,
            )

            logger.info(
                "Pipeline preview queued (no free slot)",
                extra={
                    "draft_id": draft_id, "task_id": task_id,
                    "active_tasks": active_count,
                },
            )
            return False

    async def _start_converter_preview(
        self, task_id: int, draft_id: int, file_key: str,
        trace_id: str, raw_json: dict,
    ) -> None:
        """Dispatch converter preview step after parser/OCR completes."""
        from app.tasks.pipeline_formation import run_converter_preview_step
        _params = {
            "task_id": task_id, "draft_id": draft_id,
            "file_key": file_key, "trace_id": trace_id, "raw_json": raw_json,
        }
        logger.info(
            "Enqueuing converter preview",
            extra={
                "celery_task": "tasks.pipeline.run_converter_preview_step",
                "queue": "pipeline",
                "params": _params,
                "task_id": task_id, "draft_id": draft_id,
            },
        )
        run_converter_preview_step.delay(**_params)

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
        logger.info(
            f"Step completed: {step_name}",
            extra={"task_id": task_id, "step": step_name},
        )
        task = await self.task_repo.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found on step completion")
            return

        # Restore trace_id from task for logging context
        if task.trace_id:
            set_trace_id(task.trace_id)

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
            # Step not running — find the best candidate:
            # 1. Prefer "pending" (needs completion) over "completed" (already done)
            # 2. Skip if already completed (idempotent callback)
            best_pending = None
            for step in steps:
                if step.step_name == step_name:
                    if step.status == "pending":
                        best_pending = step
                        break  # pending is the best candidate
                    elif step.status == "completed":
                        # Already completed — skip (idempotent callback from Celery retry)
                        logger.debug(
                            f"Step {step_name} already completed, skipping",
                            extra={"task_id": task_id, "step": step_name},
                        )
                        current_step = step
                        # Don't break — keep looking for a pending candidate
                    elif current_step is None:
                        current_step = step  # fallback

            if best_pending:
                current_step = best_pending

        if current_step and current_step.status != "completed":
            logger.debug(
                f"Completing step {step_name} (id={current_step.id}, status={current_step.status})",
                extra={"task_id": task_id, "step": step_name},
            )
            await self.task_repo.complete_task_step(
                step_id=current_step.id,
                output_data=output_data,
            )
            # Also update input_data if provided
            if input_data and current_step.input_data is None:
                current_step.input_data = input_data
                await self.db.flush()
        elif current_step and current_step.status == "completed":
            logger.debug(
                f"Step {step_name} already completed, skipping completion",
                extra={"task_id": task_id, "step": step_name},
            )
            # Return early — downstream dispatch (converter, preview_completed,
            # full_step_completed, drain_queue) already happened when this
            # step first completed.  Re-entering would re-submit converter
            # or re-trigger preview_completed side-effects (Registry update,
            # OCR fallback, auto-approve).
            return

        # Calculate progress
        total_steps = task.total_steps or 3
        completed_steps = len({s.step_name for s in steps if s.status == "completed"})
        progress = min(int((completed_steps / total_steps) * 100), 99)

        await self.task_repo.update_task_progress(
            task_id=task.id,
            progress_percent=progress,
        )

        # After parser/OCR preview, dispatch converter with full_result
        if step_name == "preview_ocr" and output_data:
            full_result = output_data.get("full_result") or output_data
            await self._start_converter_preview(
                task_id=task_id,
                draft_id=task.draft_id,
                file_key=input_data.get("file_key", "") if input_data else "",
                trace_id=task.trace_id or "",
                raw_json=full_result,
            )

        # Handle preview phase completion
        if step_name == "preview_converter":
            await self._on_preview_completed(task, steps, output_data)
        elif step_name in ("full_ocr", "full_converter", "registry_creation", "rag_index"):
            await self._on_full_step_completed(task, step_name, steps)

        # Try to process queued tasks if a slot freed up
        await self._drain_queue()

    async def _run_ocr_fallback(self, task, file_key: str) -> None:
        """Run OCR preview as fallback after Parser failed or returned preview_not_supported."""
        logger.info(
            "Running OCR fallback",
            extra={"task_id": task.id, "draft_id": task.draft_id},
        )

        # Guard against duplicate OCR fallback steps (B1)
        steps = await self.task_repo.get_task_steps(task.id)
        has_pending_ocr = any(
            s.step_name == "preview_ocr" and s.status == "pending"
            for s in steps
        )
        has_existing_ocr = any(
            s.step_name == "preview_ocr"
            and s.service_name == "OCR Service"
            and s.status == "completed"
            for s in steps
        )
        if has_existing_ocr:
            # OCR already completed once — stop fallback cycle (B1)
            logger.info(
                "OCR fallback skipped: OCR already completed for this task",
                extra={"task_id": task.id, "draft_id": task.draft_id},
            )
            return

        if not has_pending_ocr:
            # Reuse the existing step row (UPDATE) instead of creating a new one
            ocr_step = await self.task_repo.reset_task_step_for_fallback(
                task_id=task.id,
                step_name="preview_ocr",
                new_service_name="OCR Service",
            )
            if ocr_step is None:
                # No existing step — create fresh (first-time fallback path)
                ocr_step = await self.task_repo.create_task_step(
                    task_id=task.id,
                    step_name="preview_ocr",
                    step_index=1,
                    service_name="OCR Service",
                    input_data={
                        "file_key": file_key,
                        "mode": "preview",
                        "max_pages": 3,
                        "draft_id": task.draft_id,
                    },
                )
            # Start the step: pending → running
            await self.task_repo.start_task_step(ocr_step.id)
        else:
            # Existing pending step from a previous call — start it too
            pending_step = next(
                (s for s in steps if s.step_name == "preview_ocr" and s.status == "pending"),
                None,
            )
            if pending_step:
                await self.task_repo.start_task_step(pending_step.id)

        # Reset retry count for the fallback attempt
        task.retry_count = 0
        task.current_step_name = "OCR Service"
        await self.db.flush()

        from app.tasks.pipeline_formation import run_ocr_preview_step

        current_trace_id = task.trace_id or ""
        run_ocr_preview_step.delay(
            task.id, task.draft_id, file_key,
            max_pages=3, trace_id=current_trace_id,
        )

        logger.info(
            "OCR fallback enqueued",
            extra={"task_id": task.id, "draft_id": task.draft_id},
        )

    @staticmethod
    def _find_best_step(steps, step_name: str):
        """Find the best step by name, preferring completed > running > pending.

        Handles duplicate steps (same name, different statuses) by picking
        the one with the most useful status for reading output_data.
        """
        best = None
        for s in steps:
            if s.step_name == step_name:
                if s.status == "completed":
                    return s  # completed is the best — has output_data
                if s.status == "running" and (best is None or best.status == "pending"):
                    best = s
                if best is None:
                    best = s
        return best

    async def _on_preview_completed(
        self, task, steps, converter_output: Optional[dict]
    ) -> None:
        """Handle completion of the preview phase.

        Flow:
        1. Parser → Converter — всегда
        2. Если Converter.validation = True → preview готов
        3. Если Converter.validation = False и использовался Parser
           и OCR доступен → OCR fallback → Converter повторно
        4. Если Converter.validation = False после OCR → review_required
        5. preview_not_supported → только full_completed (пропуск full-фазы),
           не триггерит OCR fallback
        """
        logger.info(
            "Preview phase completed",
            extra={"task_id": task.id, "draft_id": task.draft_id},
        )
        # Find best OCR/Parser step output (prefer completed > running > pending)
        preview_step = self._find_best_step(steps, "preview_ocr")

        preview_not_supported = False
        quality_data = {}
        file_key = ""
        if preview_step and preview_step.output_data:
            preview_not_supported = preview_step.output_data.get(
                "preview_not_supported", False
            )
            quality_data = preview_step.output_data.get("quality", {})
        if preview_step and preview_step.input_data:
            file_key = preview_step.input_data.get("file_key", "")

        # --- Save quality notifications from Parser/OCR (OR-6) ---
        notifications = quality_data.get("notifications", [])
        if notifications:
            await self.task_repo.save_notifications(
                task_id=task.id,
                draft_id=task.draft_id,
                notifications=notifications,
            )
            logger.info(
                f"Saved {len(notifications)} quality notifications",
                extra={
                    "task_id": task.id,
                    "draft_id": task.draft_id,
                    "critical_count": sum(
                        1 for n in notifications if n.get("severity") == "critical"
                    ),
                },
            )

        # --- Check converter validation status (P1F-2) ---
        converter_step = self._find_best_step(steps, "preview_converter")
        is_validated = True
        if converter_step and converter_step.output_data:
            is_validated = converter_step.output_data.get("validated", True)

        # --- OCR fallback by converter result (not by preview_not_supported) ---
        used_parser = (
            preview_step is not None
            and preview_step.service_name == "Parser Service"
        )
        ocr_enabled = settings.services.OCR_ENABLED
        fallback_to_ocr = settings.services.PARSER_FALLBACK_TO_OCR

        if not is_validated and used_parser and fallback_to_ocr and ocr_enabled:
            logger.info(
                "Converter validation failed after Parser — falling back to OCR",
                extra={"task_id": task.id, "draft_id": task.draft_id},
            )
            await self._run_ocr_fallback(task, file_key=file_key)
            return

        if not is_validated:
            logger.info(
                "Converter validation failed — setting review_required",
                extra={"task_id": task.id, "draft_id": task.draft_id},
            )
            registry = RegistryServiceClient()
            await registry.update_draft_status(
                draft_id=task.draft_id,
                status="review_required",
            )
            await registry.close()
            await self.task_repo.update_task_status(
                task_id=task.id,
                stage=TaskStage.DECISION.value,
                progress_percent=50,
            )
            return

        # Check if there are critical notifications — block auto-approve
        has_critical = await self.task_repo.has_critical_notifications(task.id)

        if preview_not_supported:
            logger.info(
                "Preview returned full document (preview_not_supported=True), "
                "skipping full Parser/OCR phase",
                extra={"task_id": task.id, "draft_id": task.draft_id},
            )
            # Engine returned full document — mark as full_completed
            await self.task_repo.update_task_status(
                task_id=task.id,
                stage=TaskStage.DECISION.value,
                progress_percent=50,
            )
            task.full_completed = True
            await self.db.flush()

            # Evaluate quality and auto-approve conditions
            quality_action = self._check_auto_approve(task, steps)
            if quality_action == "auto_approve":
                logger.info(
                    "Auto-approving draft after full preview",
                    extra={"draft_id": task.draft_id, "task_id": task.id},
                )
                await self.approve_draft(task.draft_id, task.id)
                return
            elif quality_action == "discarded":
                logger.warning(
                    "Discarding draft due to low quality",
                    extra={"draft_id": task.draft_id, "task_id": task.id},
                )
                registry = RegistryServiceClient()
                await registry.update_draft_status(
                    draft_id=task.draft_id,
                    status="discarded",
                    error_code="QUALITY_TOO_LOW",
                )
                await registry.close()
                await self.task_repo.update_task_status(
                    task_id=task.id,
                    stage=TaskStage.DECISION.value,
                    progress_percent=100,
                    status=TaskStatus.FAILED.value,
                )
                return
            elif quality_action == "review_required":
                logger.info(
                    "Review required due to quality thresholds",
                    extra={"draft_id": task.draft_id, "task_id": task.id},
                )
                registry = RegistryServiceClient()
                await registry.update_draft_status(
                    draft_id=task.draft_id,
                    status="review_required",
                )
                await registry.close()
                await self.task_repo.update_task_status(
                    task_id=task.id,
                    stage=TaskStage.DECISION.value,
                    progress_percent=50,
                )
                return
            # else: ready_for_approve — continue to normal flow

        else:
            # Partial preview — always wait for decision
            task.full_completed = False
            await self.db.flush()
            await self.task_repo.update_task_status(
                task_id=task.id,
                stage=TaskStage.DECISION.value,
                progress_percent=50,
            )

        # --- Save preview_metadata from converter (P1F-4) ---
        preview_metadata = {}
        if converter_step and converter_step.output_data:
            preview_metadata = converter_step.output_data.get("metadata", {}) or {}
        if not preview_metadata and preview_step and preview_step.output_data:
            preview_metadata = preview_step.output_data.get("metadata", {}) or {}

        # Update draft metadata via Registry
        if preview_metadata:
            registry_meta = RegistryServiceClient()
            await registry_meta.update_draft_metadata(
                draft_id=task.draft_id,
                preview_metadata=preview_metadata,
            )
            await registry_meta.close()

        # Update draft status to ready_for_approve via Registry
        registry = RegistryServiceClient()
        await registry.update_draft_status(
            draft_id=task.draft_id,
            status=DraftState.READY_FOR_APPROVE.value,
        )
        await registry.close()

    def _check_auto_approve(self, task, steps) -> str:
        """Evaluate quality thresholds and return recommended action.

        Returns one of:
          "auto_approve"  — all conditions met, approve automatically
          "ready_for_approve" — wait for user decision
          "review_required" — manual check needed (low confidence)
          "discarded" — quality too low, discard

        Doc: §3 Quality-решения и авто-апрув (pipeline1-orchestrator_details.md)
        """
        # Try to get quality_data from best converter step, then OCR/Parser
        converter_step = self._find_best_step(steps, "preview_converter")
        preview_step = self._find_best_step(steps, "preview_ocr")

        quality_data = {}
        metadata = {}
        if converter_step and converter_step.output_data:
            conv_quality = converter_step.output_data.get("quality", {}) or {}
            conv_metadata = converter_step.output_data.get("metadata", {}) or {}
            if conv_quality or conv_metadata:
                quality_data = conv_quality
                metadata = conv_metadata
        if not metadata and preview_step and preview_step.output_data:
            quality_data = preview_step.output_data.get("quality", {}) or {}
            metadata = preview_step.output_data.get("metadata", {}) or {}

        avg_confidence = quality_data.get("avg_confidence", 1.0)
        notifications = quality_data.get("notifications", [])
        critical_count = sum(
            1 for n in notifications if n.get("severity") == "critical"
        )
        warning_count = sum(
            1 for n in notifications if n.get("severity") == "warning"
        )
        pages_failed = quality_data.get("pages_failed", 0)
        lama_fallback_used = quality_data.get("lama_fallback_used", False)

        cfg = settings.pipeline

        # --- Check catastrophic quality → discarded ---
        if avg_confidence < cfg.QUALITY_REPROCESS_CONFIDENCE_BELOW:
            logger.warning(
                f"Quality too low ({avg_confidence:.2f} < {cfg.QUALITY_REPROCESS_CONFIDENCE_BELOW}), "
                f"discarding draft {task.draft_id}"
            )
            return "discarded"

        # --- Check low quality → review_required ---
        if (
            avg_confidence < cfg.QUALITY_OPERATOR_CONFIDENCE_BELOW
            or pages_failed > 0
            or lama_fallback_used
        ):
            logger.info(
                f"Quality below threshold: avg_confidence={avg_confidence:.2f}, "
                f"pages_failed={pages_failed}, lama_fallback={lama_fallback_used} "
                f"→ review_required for draft {task.draft_id}"
            )
            return "review_required"

        # --- Check auto-approve conditions ---
        has_valid_metadata = bool(metadata.get("doc_code") and metadata.get("title"))
        has_no_duplicates = not task.error_code or task.error_code != "DUPLICATE_DETECTED"

        if cfg.AUTO_APPROVE_ENABLED and has_valid_metadata and has_no_duplicates:
            # Check notification thresholds
            if critical_count <= cfg.AUTO_APPROVE_MAX_CRITICAL \
               and warning_count <= cfg.AUTO_APPROVE_MAX_WARNING:
                logger.info(
                    f"Auto-approve conditions met for draft {task.draft_id}"
                )
                return "auto_approve"
            else:
                logger.info(
                    f"Auto-approve blocked: critical={critical_count} "
                    f"(max={cfg.AUTO_APPROVE_MAX_CRITICAL}), "
                    f"warning={warning_count} (max={cfg.AUTO_APPROVE_MAX_WARNING})"
                )

        # Default: wait for user decision
        return "ready_for_approve"

    async def _on_full_step_completed(
        self, task, step_name: str, steps
    ) -> None:
        """Handle completion of a full processing step."""
        trace_id = task.trace_id or ""

        if step_name == "full_ocr":
            await self.task_repo.update_task_progress(
                task_id=task.id,
                progress_percent=65,
            )
            # Converter should already be enqueued or will run next

            from app.tasks.pipeline_formation import run_converter_full_step
            # Extract full parser result from the full_ocr step output
            full_result = None
            file_key = None
            for s in steps:
                if s.step_name == "upload" and s.output_data:
                    file_key = s.output_data.get("file_key")
                if s.step_name == "full_ocr" and s.output_data:
                    full_result = s.output_data.get("full_result")
            if not file_key:
                for s in steps:
                    if s.input_data and s.input_data.get("file_key"):
                        file_key = s.input_data["file_key"]
                        break
            logger.info(
                f"Starting full converter: task={task.id} draft={task.draft_id} file_key={file_key} has_raw_json={full_result is not None}",
                extra={"task_id": task.id, "draft_id": task.draft_id, "file_key": file_key},
            )
            logger.info(
                "Enqueuing converter full step",
                extra={
                    "celery_task": "tasks.pipeline.run_converter_full_step",
                    "queue": "pipeline",
                    "params": {"task_id": task.id, "draft_id": task.draft_id,
                               "file_key": file_key},
                },
            )
            run_converter_full_step.delay(
                task.id, task.draft_id, file_key, trace_id=trace_id,
                raw_json=full_result,
            )

        elif step_name == "full_converter":
            await self.task_repo.update_task_progress(
                task_id=task.id,
                progress_percent=85,
            )

            from app.tasks.pipeline_formation import run_registry_step
            # Extract document data from converter step output for Registry save
            document_data = None
            metadata = None
            for s in steps:
                if s.step_name == "full_converter" and s.output_data:
                    document_data = s.output_data.get("document")
                    metadata = s.output_data.get("metadata")
                    break

            # --- Create document in Registry (moved from approve_draft) ---
            meta = metadata or {}
            # Извлекаем file_hash_sha256 из upload step metadata_fields (P1F-12)
            upload_step = next((s for s in steps if s.step_name == "upload"), None)
            upload_metadata = {}
            if upload_step and upload_step.input_data:
                upload_metadata = upload_step.input_data.get("metadata_fields", {}) or {}
            file_hash = meta.get("file_hash_sha256") or upload_metadata.get("file_hash_sha256")

            doc_payload = {
                "title": meta.get("title") or f"Draft {task.draft_id}",
                "doc_code": meta.get("doc_code") or f"DRAFT-{task.draft_id}",
                "era": meta.get("era"),
                "source_type": meta.get("source_type"),
                "jurisdiction": meta.get("jurisdiction"),
                "mks_oks_code": meta.get("mks_oks_code"),
                "okstu_code": meta.get("okstu_code"),
                "issuing_body": meta.get("issuing_body"),
                "udk_code": meta.get("udk_code"),
                "draft_id": task.draft_id,
                "status": "uploaded",
                "file_hash_sha256": file_hash,
            }
            registry_doc = RegistryServiceClient()
            doc_result = await registry_doc.create_document(doc_payload)
            doc_data = doc_result.get("data", {})
            document_id = doc_data.get("document_id") or doc_data.get("id")
            if not document_id:
                raise ValueError(
                    f"Registry create_document returned no document_id: {doc_result}"
                )
            # Parse version_id
            raw_vid = doc_data.get("version_id")
            if raw_vid is not None:
                try:
                    version_id = int(str(raw_vid).lstrip("v").split("-")[0])
                except (ValueError, IndexError):
                    version_id = int(raw_vid) if isinstance(raw_vid, (int, float)) else None
            else:
                version_id = None

            task.document_id = document_id
            task.version_id = version_id
            await self.db.flush()

            # Sync document_id to Registry draft
            await registry_doc.update_draft_status(
                draft_id=task.draft_id,
                status=DraftState.APPROVED.value,
                document_id=document_id,
            )
            await registry_doc.close()

            logger.info(
                "Enqueuing registry creation step",
                extra={
                    "celery_task": "tasks.pipeline.run_registry_step",
                    "queue": "pipeline",
                    "params": {"task_id": task.id, "draft_id": task.draft_id,
                               "document_id": document_id, "version_id": version_id,
                               "has_document_data": document_data is not None,
                               "has_metadata": metadata is not None},
                },
            )
            run_registry_step.delay(
                task.id, task.draft_id, document_id, version_id,
                document_data=document_data, metadata=metadata, trace_id=trace_id,
            )

        elif step_name == "registry_creation":
            # Registry done — now dispatch RAG indexing
            await self.task_repo.update_task_progress(
                task_id=task.id,
                progress_percent=90,
            )

            from app.tasks.pipeline_formation import run_rag_index_step

            # Extract sections for RAG Builder — priority chain:
            # 1. registry_creation step output (saved by run_registry_step via create_document)
            # 2. Registry API (get_document_sections) — fallback if step output empty
            # 3. full_converter output (content[]) — fallback if Registry unavailable
            # 4. full_ocr output (sections from parser) — legacy path
            sections = None
            document_id = getattr(task, 'document_id', None) or task.draft_id

            # Priority 1: из step output registry_creation (уже с section_id от Registry)
            for s in steps:
                if s.step_name == "registry_creation" and s.output_data:
                    sections = s.output_data.get("sections")
                    step_doc_id = s.output_data.get("document_id")
                    if step_doc_id:
                        document_id = step_doc_id
                    if sections:
                        logger.info(
                            f"Got {len(sections)} sections from registry_creation output",
                            extra={"task_id": task.id, "draft_id": task.draft_id},
                        )
                    break

            # Priority 2: читаем из Registry API
            if not sections:
                registry = RegistryServiceClient()
                sec_result = await registry.get_document_sections(document_id)
                sec_data = sec_result.get("data", {})
                sections = sec_data.get("sections", [])
                await registry.close()
                if sections:
                    logger.info(
                        f"Got {len(sections)} sections via get_document_sections",
                        extra={"task_id": task.id, "draft_id": task.draft_id},
                    )

            # Priority 3: fallback к конвертеру (content[] → section format с ручным ID)
            if not sections:
                for s in steps:
                    if s.step_name == "full_converter" and s.output_data:
                        content_items = (s.output_data.get("document") or {}).get("content")
                        if content_items:
                            sections = []
                            for idx, item in enumerate(content_items):
                                sec = dict(item)
                                sec["section_id"] = idx + 1
                                sections.append(sec)
                            logger.info(
                                f"Extracted {len(sections)} sections from full_converter content",
                                extra={"task_id": task.id, "draft_id": task.draft_id},
                            )
                        break

            # Priority 4: legacy fallback к OCR/parser
            if not sections:
                for s in steps:
                    if s.step_name == "full_ocr" and s.output_data:
                        sections = s.output_data.get("sections")
                        if sections:
                            logger.info(
                                f"Extracted {len(sections)} sections from full_ocr output",
                                extra={"task_id": task.id, "draft_id": task.draft_id},
                            )
                        break

            # Fix document_id in sections to match actual registry document_id
            if sections:
                for s in sections:
                    s['document_id'] = document_id

                # Сохраняем sections в Registry (upsert по document_id)
                reg_save = RegistryServiceClient()
                await reg_save.create_document({
                    "document_id": document_id,
                    "draft_id": task.draft_id,
                    "document": {"sections": sections},
                })
                await reg_save.close()
                logger.info(
                    f"Saved {len(sections)} sections to Registry via upsert",
                    extra={"task_id": task.id, "draft_id": task.draft_id,
                           "document_id": document_id},
                )

            logger.info(
                "Enqueuing RAG index step",
                extra={
                    "celery_task": "tasks.pipeline.run_rag_index_step",
                    "queue": "pipeline",
                    "params": {"task_id": task.id, "draft_id": task.draft_id,
                               "document_id": document_id,
                               "sections_count": len(sections) if sections else 0},
                },
            )
            run_rag_index_step.delay(
                task.id, task.draft_id, document_id,
                sections=sections, trace_id=trace_id,
            )

        elif step_name == "rag_index":
            # RAG indexing complete — mark pipeline as completed
            await self.task_repo.update_task_status(
                task_id=task.id,
                status=TaskStatus.COMPLETED.value,
                stage=TaskStage.REGISTRY.value,
                progress_percent=100,
            )

            # Update document status after successful indexing
            # Valid transition from "uploaded" is "validating"
            document_id = getattr(task, 'document_id', None) or task.draft_id
            registry = RegistryServiceClient()
            await registry.update_document_status(
                document_id=document_id,
                status="validating",
            )
            await registry.close()

            # Schedule background activation: later check with RAG and activate
            try:
                from app.tasks.pipeline_indexation import run_activate_document_step
                run_activate_document_step.delay(task.id, document_id=document_id)
                logger.info(
                    f"Scheduled background activation for document {document_id}",
                    extra={"task_id": task.id, "draft_id": task.draft_id},
                )
            except Exception as e:
                logger.warning(
                    f"Failed to schedule background activation: {e}",
                    extra={"draft_id": task.draft_id, "document_id": document_id},
                )

            logger.info(
                f"Pipeline fully completed for draft {task.draft_id}",
                extra={"task_id": task.id},
            )

    async def approve_draft(
        self, draft_id: int, task_id: int,
        metadata_overrides: Optional[dict] = None,
    ) -> dict:
        """Handle user approve decision (external action).

        Creates document in Registry first, then triggers full processing.

        Returns dict with document_id and version_id.
        """
        task = await self.task_repo.get_task(task_id)
        if not task:
            logger.error(
                "approve_draft: task not found",
                extra={"task_id": task_id, "draft_id": draft_id},
            )
            raise ValueError(f"Task not found: {task_id}")

        # Restore trace_id for logging context
        if task.trace_id:
            set_trace_id(task.trace_id)

        logger.info(
            "Approving draft",
            extra={"draft_id": draft_id, "task_id": task_id},
        )

        # Guard: prevent double-approve — check stage, not just status
        if task.pipeline_stage in (
            TaskStage.FULL.value,
            TaskStage.REGISTRY.value,
            TaskStage.INDEXATION.value,
        ):
            raise ValueError(
                f"Cannot approve task {task_id}: already in stage {task.pipeline_stage}"
            )
        if task.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            raise ValueError(
                f"Cannot approve task {task_id}: already in terminal state {task.status}"
            )

        # --- Step 0: Collect draft metadata from Registry ---
        registry = RegistryServiceClient()
        draft_result = await registry.get_draft(draft_id)
        draft_data = draft_result.get("data", {})
        preview_result = await registry.get_draft_preview(draft_id)
        preview_data = preview_result.get("data", {})
        await registry.close()

        # --- Check BUSINESS_KEY_DRIFT (§5): compare preview metadata with current ---
        preview_title_hash = preview_data.get("title_hash_sha256")
        # Compute expected title_hash from current preview fields
        expected_title = (
            metadata_overrides.get("title")
            if metadata_overrides and metadata_overrides.get("title")
            else preview_data.get("title")
            or draft_data.get("title_key", f"Draft {draft_id}")
        )
        # We compare the business key fields rather than the hash directly
        # since Converter-validator may have recomputed the hash.
        # If the metadata changed significantly, we flag it.
        if preview_title_hash and metadata_overrides:
            expected_hash = hashlib.sha256(expected_title.encode("utf-8")).hexdigest()
            if expected_hash != preview_title_hash:
                logger.warning(
                    f"BUSINESS_KEY_DRIFT for draft {draft_id}: "
                    f"title_hash changed from {preview_title_hash} to {expected_hash}",
                    extra={"draft_id": draft_id, "task_id": task_id},
                )
                raise ValueError(
                    f"BUSINESS_KEY_DRIFT: business key changed between preview and approve. "
                    f"conflict: title_hash_sha256"
                )

        # --- Save preview snapshot to Registry (P1F-4 / CV-5) ---
        # Collect preview metadata from steps
        steps = await self.task_repo.get_task_steps(task_id)
        # Priority (low → high):
        #   0. Upload step: form-provided metadata_fields (POST /drafts)
        #   1. OCR/Parser extracted metadata
        #   2. Converter validated metadata
        #   3. User metadata_overrides (PATCH /decide)
        upload_step = next(
            (s for s in steps if s.step_name == "upload"), None
        )
        preview_step = next(
            (s for s in steps if s.step_name == "preview_ocr"), None
        )
        converter_step = next(
            (s for s in steps if s.step_name == "preview_converter"), None
        )
        # Start with metadata_fields from upload form (if any)
        snapshot_metadata = {}
        if upload_step and upload_step.input_data:
            form_meta = upload_step.input_data.get("metadata_fields", {})
            if form_meta:
                snapshot_metadata.update(form_meta)
        # Then OCR/Parser extracted metadata (overrides form fields)
        if preview_step and preview_step.output_data:
            ocr_meta = preview_step.output_data.get("metadata", {})
            if ocr_meta:
                snapshot_metadata.update(ocr_meta)
        # Then Converter validated metadata (highest from processing)
        if converter_step and converter_step.output_data:
            conv_meta = converter_step.output_data.get("metadata", {})
            if conv_meta:
                snapshot_metadata.update(conv_meta)
        # Finally, user metadata_overrides on top
        if metadata_overrides:
            snapshot_metadata.update(metadata_overrides)

        registry_snap = RegistryServiceClient()
        await registry_snap.create_draft_snapshot(draft_id, snapshot_metadata)
        await registry_snap.close()
        logger.info(
            "Preview snapshot saved",
            extra={"draft_id": draft_id, "task_id": task_id},
        )

        # Re-acquire with FOR UPDATE to atomically verify state (P1F-14)
        task = await self.task_repo.get_task_for_update(task_id)
        if task.pipeline_stage in (
            TaskStage.FULL.value,
            TaskStage.REGISTRY.value,
            TaskStage.INDEXATION.value,
        ):
            raise ValueError(
                f"Cannot approve task {task_id}: already in stage {task.pipeline_stage} (re-check)"
            )

        await self.task_repo.update_task_status(
            task_id=task_id,
            stage=TaskStage.FULL.value,
            progress_percent=50,
        )

        # Sync draft status to Registry so UI hides the approve button (P1F-14)
        registry_sync = RegistryServiceClient()
        await registry_sync.update_draft_status(
            draft_id=draft_id,
            status=DraftState.APPROVED.value,
        )
        await registry_sync.close()

        from app.tasks.pipeline_formation import (
            run_ocr_full_step,
            run_parser_full_step,
            run_converter_full_step,
            run_registry_step,
        )

        # Resolve file_key from upload step output
        steps = await self.task_repo.get_task_steps(task_id)
        existing_step_names = {s.step_name for s in steps}
        upload_step = next((s for s in steps if s.step_name == "upload"), None)
        file_key = None
        if upload_step and upload_step.output_data:
            file_key = upload_step.output_data.get("file_key")

        current_trace_id = task.trace_id or ""

        # Determine full phase mode (P1F-9)
        full_mode = settings.pipeline.FULL_PHASE_MODE
        need_full_processing = False
        if full_mode == "partial":
            need_full_processing = True
        elif full_mode == "full":
            need_full_processing = False
        else:  # "auto" — use full_completed flag
            need_full_processing = not task.full_completed

        # SAFETY GUARD: warn when full mode skips processing but preview is incomplete
        if not need_full_processing and full_mode == "full" and not task.full_completed:
            logger.warning(
                f"FULL_PHASE_MODE='full' skips Parser/OCR for draft {draft_id} "
                f"(task_id={task_id}), but full_completed=False. "
                f"Document will go to Converter without Parser/OCR output. "
                f"Set FULL_PHASE_MODE='auto' or 'partial' for normal operation.",
                extra={"draft_id": draft_id, "task_id": task_id},
            )

        # Choose service for full phase: Parser-first, fallback to OCR (P1F-8)
        parser_enabled = settings.services.PARSER_ENABLED
        ocr_enabled = settings.services.OCR_ENABLED

        use_parser_for_full = bool(parser_enabled)
        full_service_name = "Parser Service" if use_parser_for_full else "OCR Service"

        # Guard: skip creating steps that already exist (prevent duplicates on re-approve)
        if need_full_processing and "full_ocr" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="full_ocr",
                step_index=3,
                service_name=full_service_name,
                input_data={"file_key": file_key, "mode": "full", "draft_id": draft_id},
            )

        # Create full_converter step (always, if not exists)
        if "full_converter" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="full_converter",
                step_index=4,
                service_name="Converter-validator",
                input_data={"file_key": file_key, "mode": "full", "draft_id": draft_id},
            )

        # Create registry_creation step (if not exists)
        if "registry_creation" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="registry_creation",
                step_index=5,
                service_name="Registry",
                input_data={"draft_id": draft_id, "document_id": None},
            )

        # Create rag_index step (if not exists)
        if "rag_index" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="rag_index",
                step_index=6,
                service_name="RAG Builder",
                input_data={"draft_id": draft_id, "document_id": None},
            )

        # Refresh steps after potential creation
        steps = await self.task_repo.get_task_steps(task_id)

        # Check concurrent slot — queue if none available
        if not await self._has_free_slot():
            await self.task_repo.update_task_status(
                task_id=task_id,
                status=TaskStatus.QUEUED.value,
                stage=TaskStage.FULL.value,
                progress_percent=50,
            )
            logger.info(
                "Approve queued (no free slot)",
                extra={
                    "draft_id": draft_id, "task_id": task_id,
                    "active_tasks": await self.task_repo.count_active_tasks(),
                },
            )
            return {
                "document_id": None,
                "version_id": None,
                "is_new_document": False,
                "queued": True,
            }

        if need_full_processing:
            full_step = next(
                (
                    s
                    for s in steps
                    if s.step_name == "full_ocr" and s.status == "pending"
                ),
                None,
            )
            if full_step:
                await self.task_repo.start_task_step(full_step.id)
                if use_parser_for_full:
                    run_parser_full_step.delay(task_id, draft_id, file_key, trace_id=current_trace_id)
                    logger.info(
                        "Enqueued full Parser step (Parser-first)",
                        extra={"task_id": task_id, "draft_id": draft_id},
                    )
                else:
                    run_ocr_full_step.delay(task_id, draft_id, file_key, trace_id=current_trace_id)
                    logger.info(
                        "Enqueued full OCR step",
                        extra={"task_id": task_id, "draft_id": draft_id},
                    )
            else:
                logger.warning(
                    "No pending full_ocr step found after approve",
                    extra={"task_id": task_id, "draft_id": draft_id},
                )
        else:
            # Full preview — start full_converter step directly
            full_converter = next(
                (
                    s
                    for s in steps
                    if s.step_name == "full_converter" and s.status == "pending"
                ),
                None,
            )
            if full_converter:
                await self.task_repo.start_task_step(full_converter.id)
                # Must dispatch converter task — otherwise step stays running forever
                logger.info(
                    "Enqueuing full Converter step (full preview, no Parser/OCR)",
                    extra={"task_id": task_id, "draft_id": draft_id},
                )
                run_converter_full_step.delay(
                    task_id, draft_id, file_key, trace_id=current_trace_id,
                )

        return {
            "document_id": None,
            "version_id": None,
            "is_new_document": False,
            "queued": False,
        }

    async def proceed_draft(
        self, draft_id: int, task_id: int,
        metadata_overrides: Optional[dict] = None,
    ) -> dict:
        """Internal action: proceed with processing (same as approve but internal)."""
        return await self.approve_draft(draft_id, task_id, metadata_overrides)

    async def stop_duplicate_draft(self, draft_id: int, task_id: int) -> dict:
        """Internal action: mark as duplicate and stop processing."""
        task = await self.task_repo.get_task(task_id)
        if task and task.trace_id:
            set_trace_id(task.trace_id)

        logger.info(
            "Stopping duplicate draft",
            extra={"draft_id": draft_id, "task_id": task_id},
        )

        await self.task_repo.update_task_status(
            task_id=task_id,
            status=TaskStatus.FAILED.value,
            stage=TaskStage.DECISION.value,
        )

        # Update draft status
        registry = RegistryServiceClient()
        await registry.update_draft_status(
            draft_id=draft_id,
            status=DraftState.DISCARDED.value,
        )
        await registry.close()

        # Try to process queued tasks if a slot freed up
        await self._drain_queue()

        return {
            "document_id": None,
            "version_id": None,
            "is_new_document": False,
            "status": "discarded",
            "action": "stop_duplicate",
            "message": "Черновик помечен как дубликат, обработка остановлена",
        }

    async def force_new_version_draft(self, draft_id: int, task_id: int) -> dict:
        """Internal action: force create new version of existing document."""
        # Same as approve but with explicit version flag
        result = await self.approve_draft(draft_id, task_id)
        result["action"] = "force_new_version"
        result["message"] = "Принудительное создание новой версии"
        return result

    async def confirm_draft(
        self, draft_id: int, task_id: int,
        metadata_overrides: Optional[dict] = None,
    ) -> dict:
        """Handle user confirm decision for review_required drafts.

        Сохраняет metadata_overrides, переводит черновик в validation,
        запускает полный цикл OCR/Parser + Converter-validator с overrides.

        Doc: §4 (pipeline1-orchestrator_details.md) — action: confirm
        """
        task = await self.task_repo.get_task(task_id)
        if not task:
            logger.error(
                "confirm_draft: task not found",
                extra={"task_id": task_id, "draft_id": draft_id},
            )
            raise ValueError(f"Task not found: {task_id}")

        if task.trace_id:
            set_trace_id(task.trace_id)

        logger.info(
            "Confirming draft (review_required → validation)",
            extra={"draft_id": draft_id, "task_id": task_id, "overrides": metadata_overrides},
        )

        # Guard: prevent double-confirm
        if task.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            raise ValueError(
                f"Cannot confirm task {task_id}: already in terminal state {task.status}"
            )

        # --- Verify draft is in review_required status ---
        reg_check = RegistryServiceClient()
        draft_check = await reg_check.get_draft(draft_id)
        await reg_check.close()
        draft_status = draft_check.get("data", {}).get("status", "")
        if draft_status != "review_required":
            raise ValueError(
                f"Confirm requires draft status 'review_required', "
                f"current status: {draft_status}"
            )

        # --- Save metadata_overrides to Registry if provided ---
        if metadata_overrides:
            registry_meta = RegistryServiceClient()
            await registry_meta.update_draft_metadata(
                draft_id=draft_id,
                preview_metadata=metadata_overrides,
            )
            await registry_meta.close()

        # --- Update draft status to validation ---
        registry = RegistryServiceClient()
        await registry.update_draft_status(
            draft_id=draft_id,
            status="validation",
        )
        await registry.close()

        # --- Trigger full OCR/Parser + Converter cycle ---
        from app.tasks.pipeline_formation import (
            run_ocr_full_step,
            run_parser_full_step,
            run_converter_full_step,
        )

        # Resolve file_key from upload step
        steps = await self.task_repo.get_task_steps(task_id)
        upload_step = next((s for s in steps if s.step_name == "upload"), None)
        file_key = None
        if upload_step and upload_step.output_data:
            file_key = upload_step.output_data.get("file_key")

        current_trace_id = task.trace_id or ""

        # Choose service: Parser-first, fallback to OCR (P1F-8)
        parser_enabled = settings.services.PARSER_ENABLED
        use_parser = bool(parser_enabled)
        service_name = "Parser Service" if use_parser else "OCR Service"

        # Create full_ocr step for validation run (skip if already exists)
        steps = await self.task_repo.get_task_steps(task_id)
        existing_step_names = {s.step_name for s in steps}
        if "full_ocr" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="full_ocr",
                step_index=3,
                service_name=service_name,
                input_data={
                    "file_key": file_key,
                    "mode": "full",
                    "draft_id": draft_id,
                    "metadata_overrides": metadata_overrides,
                },
            )

        # Create full_converter step (skip if already exists)
        if "full_converter" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="full_converter",
                step_index=4,
                service_name="Converter-validator",
                input_data={
                    "file_key": file_key,
                    "mode": "full",
                    "draft_id": draft_id,
                    "metadata_overrides": metadata_overrides,
                },
            )

        # Check free slot — queue if none available
        if not await self._has_free_slot():
            await self.task_repo.update_task_status(
                task_id=task_id,
                status=TaskStatus.QUEUED.value,
                stage=TaskStage.FULL.value,
                progress_percent=5,
            )
            logger.info(
                "Confirm queued (no free slot)",
                extra={
                    "draft_id": draft_id, "task_id": task_id,
                    "active_tasks": await self.task_repo.count_active_tasks(),
                },
            )
            return {
                "status": "queued",
                "task_id": task_id,
                "draft_id": draft_id,
                "queued": True,
            }

        # Start full_ocr step
        steps = await self.task_repo.get_task_steps(task_id)
        full_step = next(
            (s for s in steps if s.step_name == "full_ocr" and s.status == "pending"),
            None,
        )
        if full_step:
            await self.task_repo.start_task_step(full_step.id)
            if use_parser:
                run_parser_full_step.delay(
                    task_id, draft_id, file_key, trace_id=current_trace_id
                )
            else:
                run_ocr_full_step.delay(
                    task_id, draft_id, file_key, trace_id=current_trace_id
                )

        await self.task_repo.update_task_status(
            task_id=task_id,
            stage=TaskStage.FULL.value,
            progress_percent=10,
        )

        return {
            "status": "validation",
            "task_id": task_id,
            "draft_id": draft_id,
            "queued": False,
        }

    async def reject_draft(self, draft_id: int, task_id: int) -> None:
        """Handle user reject decision."""
        task = await self.task_repo.get_task(task_id)
        if not task:
            logger.error(
                "reject_draft: task not found",
                extra={"task_id": task_id, "draft_id": draft_id},
            )
            raise ValueError(f"Task not found: {task_id}")

        # Restore trace_id for logging context
        if task.trace_id:
            set_trace_id(task.trace_id)

        logger.info(
            "Rejecting draft",
            extra={"draft_id": draft_id, "task_id": task_id},
        )

        await self.task_repo.update_task_status(
            task_id=task_id,
            status=TaskStatus.FAILED.value,
            stage=TaskStage.DECISION.value,
        )

        # Update draft status to discarded via Registry
        registry = RegistryServiceClient()
        await registry.update_draft_status(
            draft_id=draft_id,
            status=DraftState.DISCARDED.value,
        )
        await registry.close()

        # Try to process queued tasks if a slot freed up
        await self._drain_queue()

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

        # Restore trace_id for logging context
        if task.trace_id:
            set_trace_id(task.trace_id)

        logger.warning(
            f"Step failed: {step_name} ({error_code})",
            extra={
                "task_id": task_id,
                "step": step_name,
                "error_code": error_code,
            },
        )

        if task.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            logger.warning(
                f"on_step_failed called for already terminal task {task_id} "
                f"(status={task.status}, step={step_name})"
            )
            return

        # Mark the running step as failed
        steps = await self.task_repo.get_task_steps(task_id)
        failed_step = None
        for step in steps:
            if step.step_name == step_name and step.status == "running":
                await self.task_repo.fail_task_step(
                    step_id=step.id,
                    error_code=error_code,
                    error_message=error_message,
                )
                failed_step = step
                break

        # Update task error info
        await self.task_repo.set_task_error(task_id, error_code, error_message)

        # --- Parser-first: fallback from Parser to OCR on failure ---
        # Applies to both preview_ocr (preview) and full_ocr (full phase)
        use_ocr_fallback = False
        if (
            step_name in ("preview_ocr", "full_ocr")
            and failed_step is not None
            and failed_step.service_name == "Parser Service"
            and settings.services.PARSER_FALLBACK_TO_OCR
            and settings.services.OCR_ENABLED
        ):
            logger.info(
                f"Parser {step_name} failed ({error_code}) — falling back to OCR "
                f"instead of retry",
                extra={"task_id": task_id, "draft_id": task.draft_id},
            )
            use_ocr_fallback = True

        # --- Engine-availability guard (todo_pipeline_coverage §1.2) ---
        # Если оба движка выключены — retry/fallback невозможен.
        # Помечаем task как failed с понятным кодом, а не молча ретраим.
        if (
            step_name in ("preview_ocr", "full_ocr")
            and not settings.services.PARSER_ENABLED
            and not settings.services.OCR_ENABLED
        ):
            logger.error(
                f"No engines available for {step_name}: PARSER_ENABLED=False, "
                f"OCR_ENABLED=False",
                extra={"task_id": task_id, "draft_id": task.draft_id},
            )
            await self.task_repo.set_task_error(
                task_id,
                error_code="NO_AVAILABLE_ENGINES",
                error_message="Both PARSER_ENABLED and OCR_ENABLED are false",
            )
            await self.task_repo.update_task_status(
                task_id, status=TaskStatus.FAILED.value
            )
            # Release lock on terminal task.
            if task.locked_by is not None:
                await self.task_repo.unlock_task(task_id)
            return

        if use_ocr_fallback:
            # Fall back to OCR — create new OCR step (if not already pending) and enqueue
            file_key = ""
            if failed_step and failed_step.input_data:
                file_key = failed_step.input_data.get("file_key", "")

            mode = "preview" if "preview" in step_name else "full"
            max_pages = 3 if mode == "preview" else None

            # Guard: don't create duplicate step if one is already pending
            existing_pending = any(
                s.step_name == step_name and s.status == "pending"
                for s in steps
            )
            if not existing_pending:
                await self.task_repo.create_task_step(
                    task_id=task_id,
                    step_name=step_name,
                    step_index=task.current_step_index,
                    service_name="OCR Service",
                    input_data={
                        "file_key": file_key,
                        "mode": mode,
                        "draft_id": task.draft_id,
                    },
                )

            task.retry_count = 0
            task.current_step_name = "OCR Service"
            await self.db.flush()

            await self.task_repo.update_task_status(
                task_id=task_id,
                status=TaskStatus.ACTIVE.value,
            )

            from app.tasks.pipeline_formation import (
                run_ocr_preview_step,
                run_ocr_full_step,
            )

            trace = task.trace_id or ""
            if mode == "preview":
                run_ocr_preview_step.delay(
                    task_id, task.draft_id, file_key,
                    max_pages=max_pages, trace_id=trace,
                )
            else:
                run_ocr_full_step.delay(
                    task_id, task.draft_id, file_key, trace_id=trace,
                )

            logger.info(
                f"OCR fallback enqueued after parser {step_name} failure",
                extra={"task_id": task_id, "draft_id": task.draft_id},
            )

        elif failed_step is not None and task.retry_count < settings.pipeline.MAX_STEP_RETRIES:
            # Retry with exponential backoff
            backoff_delay = settings.pipeline.RETRY_BASE_DELAY * (2 ** task.retry_count)

            # Guard: don't create duplicate step if one is already pending
            existing_pending = any(
                s.step_name == step_name and s.status == "pending"
                for s in steps
            )
            if not existing_pending:
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
                f"Step {step_name} failed, retry {task.retry_count}/{settings.pipeline.MAX_STEP_RETRIES} "
                f"in {backoff_delay}s",
                extra={"task_id": task_id, "draft_id": task.draft_id},
            )
        else:
            # Failed step not found, or retries exhausted — fail the task and compensate
            await self.task_repo.update_task_status(
                task_id, status=TaskStatus.FAILED.value
            )
            # Release lock (todo_pipeline_coverage §14):
            # terminal task must not hold a worker lock.
            if task.locked_by is not None:
                await self.task_repo.unlock_task(task_id)
                logger.info(
                    f"Lock released on terminal task {task_id} "
                    f"(was held by {task.locked_by!r})",
                    extra={"task_id": task_id, "old_worker": task.locked_by},
                )

            # Run Saga compensation (rollback completed steps)
            saga = SagaCoordinator(self.db)
            await saga.compensate(task_id, step_name, task=task)

            # NOTE: draft status is NOT set to DISCARDED here.
            # Pipeline failure due to external service timeout is a transient error,
            # not a logical rejection. The draft remains in its current state
            # so the user can retry later via the UI.

            logger.error(
                f"Pipeline failed at step {step_name}",
                extra={
                    "task_id": task_id,
                    "draft_id": task.draft_id,
                    "error": error_message,
                },
            )

        # Try to process queued tasks if a slot freed up
        await self._drain_queue()

    async def _check_service_health(self, service_name: str) -> bool:
        """Check if a service is alive via HTTP health check (P2S-5).

        Uses short timeout (3s) and only probes alternative URLs on 404.
        """
        svc = settings.services
        url_map = {
            "Parser Service": svc.PARSER_SERVICE_URL,
            "OCR Service": svc.OCR_SERVICE_URL,
            "Converter-validator": svc.CONVERTER_SERVICE_URL,
            "Registry": svc.REGISTRY_SERVICE_URL,
            "RAG Builder": svc.RAG_BUILDER_SERVICE_URL,
            "Orchestrator": None,
        }
        base_url = url_map.get(service_name)
        if not base_url:
            return True  # cannot check, assume alive

        # Try primary /health first; fall back to /api/v1/health only on 404
        candidates = [
            f"{base_url}/health",
            f"{base_url}/api/v1/health",
        ]
        for i, url in enumerate(candidates):
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    r = await client.get(url)
                    if r.status_code < 500:
                        return True
                    # 404 on first URL → try the second
                    if r.status_code == 404 and i == 0:
                        continue
                    return False
            except (httpx.TimeoutException, httpx.ConnectError,
                    httpx.RequestError):
                # Network error → only retry if this is the first candidate
                if i == 0:
                    continue
                return False
        return False

    async def cleanup_stale_tasks(self) -> int:
        """Find and mark stale running tasks as failed.
        
        Also handles:
        - Stale pending steps (P3S-1: per-state timeout)
        - Stale running steps (B2: health check after timeout)
        - Absolute timeout tasks (P3S-1: 48h limit)
        """
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

        # Commit batch 1: stale tasks before moving to steps
        if stale_tasks:
            await self.db.commit()

        # Handle stale pending steps (P3S-1)
        pending_timeout = settings.pipeline.PENDING_STATE_TIMEOUT
        stale_steps = await self.task_repo.get_stale_pending_steps(pending_timeout)
        for step in stale_steps:
            await self.task_repo.fail_task_step(
                step.id,
                error_code="PENDING_TIMEOUT",
                error_message=f"Step pending for >{pending_timeout}s",
            )
            try:
                await self.on_step_failed(
                    step.task_id,
                    step.step_name,
                    "PENDING_TIMEOUT",
                    f"Step pending for >{pending_timeout}s",
                )
            except Exception as e:
                logger.error(
                    f"Cleanup on_step_failed for pending step {step.id} failed: {e}",
                    extra={"step_id": step.id, "task_id": step.task_id},
                )
            cleaned += 1

        # Commit batch 2: pending steps before hard kill
        if stale_steps:
            await self.db.commit()

        # Handle stale running steps — hard kill (H1: absolute execution timeout)
        # Runs BEFORE health-check: kills steps that exceed MAX_STEP_EXECUTION_TIME
        # regardless of whether the service is alive.
        max_exec_time = settings.pipeline.MAX_STEP_EXECUTION_TIME
        stale_hard_kill = await self.task_repo.get_stale_running_steps_for_hard_kill(max_exec_time)
        for step in stale_hard_kill:
            logger.warning(
                f"Step {step.step_name} running for >{max_exec_time}s "
                f"— hard kill (H1)",
                extra={"step_id": step.id, "step_name": step.step_name},
            )
            await self.task_repo.fail_task_step(
                step.id,
                error_code="STEP_HARD_TIMEOUT",
                error_message=f"Step running for >{max_exec_time}s (hard limit)",
            )
            try:
                await self.on_step_failed(
                    step.task_id,
                    step.step_name,
                    "STEP_HARD_TIMEOUT",
                    f"Step running for >{max_exec_time}s (hard limit)",
                )
            except Exception as e:
                logger.error(
                    f"Cleanup on_step_failed for hard-kill step {step.id} failed: {e}",
                    extra={"step_id": step.id, "task_id": step.task_id},
                )
            cleaned += 1

        # Commit batch 3: hard-kill before health-check (save progress)
        if stale_hard_kill:
            await self.db.commit()

        # Handle stale running steps (B2: check if service is alive)
        # NOTE: health checks run AFTER commit to keep transaction short
        running_timeout = settings.pipeline.RUNNING_STEP_TIMEOUT
        stale_running = await self.task_repo.get_stale_running_steps(running_timeout)
        for step in stale_running:
            service_alive = await self._check_service_health(step.service_name)
            if service_alive:
                logger.warning(
                    f"Step {step.step_name} running for >{running_timeout}s "
                    f"but service {step.service_name} is alive — possible slow processing",
                    extra={"step_id": step.id,
                           "step_name": step.step_name,
                           "service_name": step.service_name},
                )
                continue

            logger.warning(
                f"Step {step.step_name} running for >{running_timeout}s "
                f"and service {step.service_name} is DEAD — failing step",
                extra={"step_id": step.id,
                       "step_name": step.step_name,
                       "service_name": step.service_name},
            )
            await self.task_repo.fail_task_step(
                step.id,
                error_code="SERVICE_DEAD",
                error_message=f"Service {step.service_name} unreachable, step ran >{running_timeout}s",
            )
            try:
                await self.on_step_failed(
                    step.task_id,
                    step.step_name,
                    "SERVICE_DEAD",
                    f"Service {step.service_name} unreachable, step ran >{running_timeout}s",
                )
            except Exception as e:
                logger.error(
                    f"Cleanup on_step_failed for service-dead step {step.id} failed: {e}",
                    extra={"step_id": step.id, "task_id": step.task_id},
                )
            cleaned += 1

        # Commit batch 4: stale-running health-check results
        if stale_running:
            await self.db.commit()

        # Handle absolute timeout tasks (P3S-1)
        abs_timeout = settings.pipeline.ABSOLUTE_TASK_TIMEOUT_HOURS
        timed_out_tasks = await self.task_repo.get_absolute_timeout_tasks(abs_timeout)
        for task in timed_out_tasks:
            await self.task_repo.update_task_status(
                task.id,
                status=TaskStatus.FAILED.value,
            )
            await self.task_repo.set_task_error(
                task.id,
                error_code="ABSOLUTE_TIMEOUT",
                error_message=f"Task exceeded absolute timeout of {abs_timeout}h",
            )
            cleaned += 1

        # Commit batch 5: absolute timeout before stale validation
        if timed_out_tasks:
            await self.db.commit()

        # Handle stale validation tasks (C2: rag_index completed but activation stuck)
        validating_timeout = settings.pipeline.VALIDATING_STATE_TIMEOUT
        stale_validating = await self.task_repo.get_stale_validation_tasks(validating_timeout)
        for task in stale_validating:
            logger.warning(
                f"Task {task.id} stuck in validating for >{validating_timeout}s "
                f"(rag_index completed, activation never finished) — failing (C2)",
                extra={"task_id": task.id, "draft_id": task.draft_id},
            )
            await self.task_repo.update_task_status(
                task.id,
                status=TaskStatus.FAILED.value,
            )
            await self.task_repo.set_task_error(
                task.id,
                error_code="VALIDATING_TIMEOUT",
                error_message=f"Document stuck in validating for >{validating_timeout}s",
            )
            cleaned += 1

        # Commit batch 6: stale validation before stale locks
        if stale_validating:
            await self.db.commit()

        # Handle stale locks (M4: extracted to TaskRepository)
        released_locks = await self.task_repo.release_stale_locks(max_seconds=max_time)
        for lock in released_locks:
            logger.warning(
                f"Auto-released stale lock on task {lock['id']} "
                f"(was held by {lock['locked_by']!r}, locked_at={lock['locked_at']})",
                extra={"task_id": lock["id"], "old_worker": lock["locked_by"]},
            )
        cleaned += len(released_locks)

        # Commit batch 7: stale locks (no explicit commit needed — get_db_context commits at exit)

        if cleaned:
            logger.warning(f"Cleaned up {cleaned} stale pipeline items")

        return cleaned
