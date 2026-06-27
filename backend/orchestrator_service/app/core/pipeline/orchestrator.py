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

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.fsm import DraftFSM, DraftState, TaskStage, TaskStatus
from app.core.pipeline.saga import SagaCoordinator
from app.core.trace import get_trace_id, set_trace_id
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
        self, draft_id: int, task_id: int, file_key: str, mime_type: str,
        metadata_fields: Optional[dict] = None,
    ) -> None:
        """Start the pipeline for a draft (preview phase).

        Parser-first strategy: if Parser is enabled, it is always tried first.
        If Parser fails or returns preview_not_supported and fallback is enabled,
        the pipeline falls back to OCR.

        1. Validates task exists
        2. Creates TaskSteps for preview phase (idempotent — skips existing)
        3. Enqueues preview Celery tasks

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
        # Try Parser first if enabled, fall back to OCR if:
        #   - Parser is disabled
        #   - Parser fails and PARSER_FALLBACK_TO_OCR is enabled
        #   - Parser returns preview_not_supported and PARSER_FALLBACK_TO_OCR is enabled
        parser_enabled = settings.services.PARSER_ENABLED
        ocr_enabled = settings.services.OCR_ENABLED
        fallback_to_ocr = settings.services.PARSER_FALLBACK_TO_OCR

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
            # Should not reach here due to check above
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
            preview_step = await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="preview_ocr",  # unified step name
                step_index=1,
                service_name=preview_service,
                input_data={"file_key": file_key, "mode": "preview", "max_pages": 3, "draft_id": draft_id},
            )

        # Step 2: preview Converter-validator
        if "preview_converter" not in existing_step_names:
            converter_step = await self.task_repo.create_task_step(
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

        # Enqueue preview tasks via Celery
        from app.tasks.pipeline_formation import (
            run_ocr_preview_step,
            run_parser_preview_step,
            run_converter_preview_step,
        )

        current_trace_id = get_trace_id() or ""

        task_names = {
            run_parser_preview_step: "tasks.pipeline.run_parser_preview_step",
            run_ocr_preview_step: "tasks.pipeline.run_ocr_preview_step",
        }

        if use_parser:
            _task = run_parser_preview_step
            _params = {"task_id": task_id, "draft_id": draft_id,
                       "file_key": file_key, "max_pages": 3, "trace_id": current_trace_id}
            logger.info(
                "Parser-first: enqueuing celery task",
                extra={
                    "celery_task": task_names[_task],
                    "queue": "pipeline",
                    "params": _params,
                    "draft_id": draft_id, "task_id": task_id,
                },
            )
            _task.delay(**_params)
        else:
            _task = run_ocr_preview_step
            _params = {"task_id": task_id, "draft_id": draft_id,
                       "file_key": file_key, "max_pages": 3, "trace_id": current_trace_id}
            logger.info(
                "OCR: enqueuing celery task",
                extra={
                    "celery_task": task_names[_task],
                    "queue": "pipeline",
                    "params": _params,
                    "draft_id": draft_id, "task_id": task_id,
                },
            )
            _task.delay(**_params)

        # Converter запускается ПОСЛЕ parser/ocr в on_step_completed
        # с результатом парсинга как raw_json

        # Update progress
        await self.task_repo.update_task_status(
            task_id=task_id,
            progress_percent=10,
        )

        logger.info(
            "Pipeline preview started",
            extra={"draft_id": draft_id, "task_id": task_id},
        )

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

        # Calculate progress
        total_steps = task.total_steps or 3
        completed_steps = sum(1 for s in steps if s.status == "completed")
        progress = min(int((completed_steps / total_steps) * 100), 99)

        await self.task_repo.update_task_status(
            task_id=task_id,
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

    async def _run_ocr_fallback(self, task, file_key: str) -> None:
        """Run OCR preview as fallback after Parser failed or returned preview_not_supported."""
        logger.info(
            "Running OCR fallback",
            extra={"task_id": task.id, "draft_id": task.draft_id},
        )

        # Guard against duplicate OCR fallback steps
        steps = await self.task_repo.get_task_steps(task.id)
        has_pending_ocr = any(
            s.step_name == "preview_ocr" and s.status == "pending"
            for s in steps
        )
        if not has_pending_ocr:
            # Create a new preview step for OCR
            await self.task_repo.create_task_step(
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
            try:
                registry = RegistryServiceClient()
                await registry.update_draft_status(
                    draft_id=task.draft_id,
                    status="review_required",
                )
                await registry.close()
            except Exception as e:
                logger.warning(
                    f"Failed to set draft status to review_required: {e}",
                    extra={"draft_id": task.draft_id},
                )
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

            # Check auto-approve conditions (skip if critical notifications)
            if not has_critical:
                can_auto_approve = self._check_auto_approve(task, steps)
                if can_auto_approve:
                    logger.info(
                        "Auto-approving draft after full preview",
                        extra={"draft_id": task.draft_id, "task_id": task.id},
                    )
                    await self.approve_draft(task.draft_id, task.id)
                    return
            else:
                logger.info(
                    "Auto-approve blocked: critical quality notifications",
                    extra={"draft_id": task.draft_id, "task_id": task.id},
                )

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
            try:
                registry_meta = RegistryServiceClient()
                await registry_meta.update_draft_metadata(
                    draft_id=task.draft_id,
                    preview_metadata=preview_metadata,
                )
                await registry_meta.close()
            except Exception as e:
                logger.warning(
                    f"Failed to save preview_metadata: {e}",
                    extra={"draft_id": task.draft_id},
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
        """Check if conditions for auto-approve are met.

        Auto-approve if:
        - preview was full (preview_not_supported=True)
        - metadata is valid (doc_code and title present)
        - no duplicates detected
        """
        # Try to get metadata from best converter step (validated metadata)
        # then fallback to best OCR/Parser step
        converter_step = self._find_best_step(steps, "preview_converter")
        preview_step = self._find_best_step(steps, "preview_ocr")

        metadata = {}
        if converter_step and converter_step.output_data:
            metadata = converter_step.output_data.get("metadata", {})
        if not metadata and preview_step and preview_step.output_data:
            metadata = preview_step.output_data.get("metadata", {})

        has_valid_metadata = bool(metadata.get("doc_code") and metadata.get("title"))

        # Check uniqueness — if no title_hash, it may be a new document
        has_no_duplicates = not task.error_code or task.error_code != "DUPLICATE_DETECTED"

        return bool(has_valid_metadata and has_no_duplicates and task.full_completed)

    async def _on_full_step_completed(
        self, task, step_name: str, steps
    ) -> None:
        """Handle completion of a full processing step."""
        trace_id = task.trace_id or ""
        version_id = getattr(task, 'version_id', None)

        if step_name == "full_ocr":
            await self.task_repo.update_task_status(
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
                               "file_key": file_key, "version_id": version_id},
                },
            )
            run_converter_full_step.delay(
                task.id, task.draft_id, file_key, trace_id=trace_id,
                raw_json=full_result, version_id=version_id,
            )

        elif step_name == "full_converter":
            await self.task_repo.update_task_status(
                task_id=task.id,
                progress_percent=85,
            )

            from app.tasks.pipeline_formation import run_registry_step
            # Pass document_id and version_id to registry step
            document_id = getattr(task, 'document_id', None) or task.draft_id
            logger.info(
                "Enqueuing registry creation step",
                extra={
                    "celery_task": "tasks.pipeline.run_registry_step",
                    "queue": "pipeline",
                    "params": {"task_id": task.id, "draft_id": task.draft_id,
                               "document_id": document_id, "version_id": version_id},
                },
            )
            run_registry_step.delay(task.id, task.draft_id, document_id, version_id, trace_id=trace_id)

        elif step_name == "registry_creation":
            # Registry done — now dispatch RAG indexing
            await self.task_repo.update_task_status(
                task_id=task.id,
                progress_percent=90,
            )

            from app.tasks.pipeline_formation import run_rag_index_step
            # Extract sections from full_ocr step output for RAG Builder
            sections = None
            for s in steps:
                if s.step_name == "full_ocr" and s.output_data:
                    sections = s.output_data.get("sections")
                    break
            document_id = getattr(task, 'document_id', None) or task.draft_id
            # Fix document_id in sections to match registry document_id (P1F-10)
            # Sections were built with draft_id, but registry may assign a different id
            if sections:
                for s in sections:
                    s['document_id'] = document_id
            logger.info(
                "Enqueuing RAG index step",
                extra={
                    "celery_task": "tasks.pipeline.run_rag_index_step",
                    "queue": "pipeline",
                    "params": {"task_id": task.id, "draft_id": task.draft_id,
                               "document_id": document_id},
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

        # Guard: prevent double-approve (defensive, also checked in endpoint)
        if task.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            raise ValueError(
                f"Cannot approve task {task_id}: already in terminal state {task.status}"
            )

        # --- Step 0: Collect draft metadata from Registry ---
        registry = RegistryServiceClient()
        try:
            draft_result = await registry.get_draft(draft_id)
            draft_data = draft_result.get("data", {})
            preview_result = await registry.get_draft_preview(draft_id)
            preview_data = preview_result.get("data", {})
        except Exception as exc:
            logger.error(f"Failed to get draft data from Registry: {exc}")
            draft_data = {}
            preview_data = {}

        # Build document payload from draft + preview + overrides
        doc_payload = {
            "title": preview_data.get("title") or draft_data.get("title_key", f"Draft {draft_id}"),
            "doc_code": preview_data.get("doc_code") or draft_data.get("document_key", f"DRAFT-{draft_id}"),
            "era": preview_data.get("era"),
            "source_type": preview_data.get("source_type"),
            "jurisdiction": preview_data.get("jurisdiction"),
            "mks_oks_code": preview_data.get("mks_oks_code"),
            "okstu_code": preview_data.get("okstu_code"),
            "issuing_body": preview_data.get("issuing_body"),
            "udk_code": preview_data.get("udk_code"),
            "draft_id": draft_id,
            "status": "uploaded",
        }
        # Apply user overrides on top
        if metadata_overrides:
            doc_payload.update(metadata_overrides)

        # --- Step 1: Create document in Registry (OR-13) ---
        try:
            doc_result = await registry.create_document(doc_payload)
            doc_data = doc_result.get("data", {})
            document_id: Optional[int] = doc_data.get("document_id") if doc_data.get("document_id") is not None else doc_data.get("id")
            if not document_id:
                raise ValueError(
                    f"Registry create_document returned no document_id. "
                    f"Response: {doc_result}"
                )
            # version_id может быть 'v1-75' (строка) или числом
            raw_vid = doc_data.get("version_id")
            if raw_vid is not None:
                try:
                    version_id = int(str(raw_vid).lstrip("v").split("-")[0])
                except (ValueError, IndexError):
                    version_id = int(raw_vid) if isinstance(raw_vid, (int, float)) else None
            else:
                version_id = None
            is_new_document: bool = doc_data.get("is_new_document", True)
        except Exception as exc:
            logger.error(
                f"Failed to create document in Registry: {exc}",
                extra={"draft_id": draft_id, "task_id": task_id},
            )
            raise ValueError(f"Registry create_document failed: {exc}")
        finally:
            await registry.close()

        # Store document_id and version_id on task for later steps
        task.document_id = document_id
        task.version_id = version_id
        await self.db.flush()

        # --- Step 1a: Sync document_id back to Registry draft ---
        try:
            registry_sync = RegistryServiceClient()
            await registry_sync.update_draft_status(
                draft_id=draft_id,
                status=DraftState.APPROVED.value,
                document_id=document_id,
            )
            await registry_sync.close()
        except Exception as sync_err:
            logger.warning(
                f"Failed to sync document_id={document_id} to Registry draft {draft_id}: {sync_err}",
                extra={"draft_id": draft_id, "document_id": document_id},
            )

        # --- Save preview snapshot to Registry (P1F-4 / CV-5) ---
        try:
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
        except Exception as snap_err:
            logger.warning(
                f"Failed to save preview snapshot: {snap_err}",
                extra={"draft_id": draft_id, "task_id": task_id},
            )

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
                input_data={"draft_id": draft_id, "document_id": document_id},
            )

        # Create rag_index step (if not exists)
        if "rag_index" not in existing_step_names:
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="rag_index",
                step_index=6,
                service_name="RAG Builder",
                input_data={"draft_id": draft_id, "document_id": document_id},
            )

        # Refresh steps after potential creation
        steps = await self.task_repo.get_task_steps(task_id)
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
                logger.info(
                    "Enqueued full Converter step (full preview, no Parser/OCR)",
                    extra={"task_id": task_id, "draft_id": draft_id},
                )

        return {
            "document_id": document_id,
            "version_id": version_id,
            "is_new_document": is_new_document,
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
        try:
            registry = RegistryServiceClient()
            await registry.update_draft_status(
                draft_id=draft_id,
                status=DraftState.DISCARDED.value,
            )
            await registry.close()
        except Exception as e:
            logger.warning(
                f"Failed to update draft status: {e}",
                extra={"draft_id": draft_id},
            )

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

        elif task.retry_count < settings.pipeline.MAX_STEP_RETRIES:
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
            # Retries exhausted — fail the task and compensate
            await self.task_repo.update_task_status(
                task_id, status=TaskStatus.FAILED.value
            )

            # Run Saga compensation (rollback completed steps)
            saga = SagaCoordinator(self.db)
            await saga.compensate(task_id, step_name, task=task)

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
        """Find and mark stale running tasks as failed.
        
        Also handles:
        - Stale pending steps (P3S-1: per-state timeout)
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

        # Handle stale pending steps (P3S-1)
        pending_timeout = settings.pipeline.PENDING_STATE_TIMEOUT
        stale_steps = await self.task_repo.get_stale_pending_steps(pending_timeout)
        for step in stale_steps:
            await self.task_repo.fail_task_step(
                step.id,
                error_code="PENDING_TIMEOUT",
                error_message=f"Step pending for >{pending_timeout}s",
            )
            cleaned += 1

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

        if cleaned:
            logger.warning(f"Cleaned up {cleaned} stale pipeline items")

        return cleaned
