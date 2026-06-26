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

        1. Validates task exists
        2. Creates TaskSteps for preview phase
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

        # Determine which service handles the preview based on mime_type
        # image/* → OCR Service; application/pdf with text layer → Parser Service
        # For now: image/* → OCR, PDF → Parser (digital PDF detection via mime sub-type)
        is_image = mime_type in ("image/png", "image/jpeg", "image/tiff")
        is_digital_pdf = mime_type == "application/pdf"
        is_scanned_pdf = mime_type in (
            "application/pdf+scanned", "application/x-pdf-scanned"
        )

        if is_image or is_scanned_pdf:
            preview_service = "OCR Service"
            use_ocr = True
        else:
            # Digital PDF or unknown → Parser Service
            preview_service = "Parser Service"
            use_ocr = False

        preview_step = "preview_ocr"  # both use same step name

        # Create TaskSteps
        # Step 0: upload
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

        # Step 1: preview OCR/Parser
        ocr_step = await self.task_repo.create_task_step(
            task_id=task_id,
            step_name=preview_step,
            step_index=1,
            service_name=preview_service,
            input_data={"file_key": file_key, "mode": "preview", "max_pages": 3, "draft_id": draft_id},
        )

        # Step 2: preview Converter-validator
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
        if use_ocr:
            run_ocr_preview_step.delay(task_id, draft_id, file_key, max_pages=3, trace_id=current_trace_id)
        else:
            run_parser_preview_step.delay(task_id, draft_id, file_key, max_pages=3, trace_id=current_trace_id)

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
        run_converter_preview_step.delay(
            task_id, draft_id, file_key, trace_id=trace_id, raw_json=raw_json,
        )
        logger.info(
            "Converter preview dispatched after parser",
            extra={"task_id": task_id, "draft_id": draft_id},
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
            # Maybe the step was already completed (upload step)
            for step in steps:
                if step.step_name == step_name:
                    current_step = step
                    break

        if current_step:
            logger.debug(
                f"Completing step {step_name} (id={current_step.id})",
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
        elif step_name in ("full_ocr", "full_converter", "registry_creation"):
            await self._on_full_step_completed(task, step_name, steps)

    async def _on_preview_completed(
        self, task, steps, converter_output: Optional[dict]
    ) -> None:
        """Handle completion of the preview phase."""
        logger.info(
            "Preview phase completed",
            extra={"task_id": task.id, "draft_id": task.draft_id},
        )
        # Find the OCR/Parser step output
        preview_step = None
        for step in steps:
            if step.step_name == "preview_ocr":
                preview_step = step
                break

        preview_not_supported = False
        quality_data = {}
        if preview_step and preview_step.output_data:
            preview_not_supported = preview_step.output_data.get(
                "preview_not_supported", False
            )
            quality_data = preview_step.output_data.get("quality", {})

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
        converter_step = next(
            (s for s in steps if s.step_name == "preview_converter"), None
        )
        is_validated = True
        if converter_step and converter_step.output_data:
            is_validated = converter_step.output_data.get("validated", True)

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
                "skipping full OCR/Parser phase",
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
        # Try to get metadata from converter step first (validated metadata)
        # then fallback to OCR/Parser step
        converter_step = None
        preview_step = None
        for step in steps:
            if step.step_name == "preview_converter":
                converter_step = step
            elif step.step_name == "preview_ocr":
                preview_step = step

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

        if step_name == "full_ocr":
            await self.task_repo.update_task_status(
                task_id=task.id,
                progress_percent=65,
            )
            # Converter should already be enqueued or will run next

            from app.tasks.pipeline_formation import run_converter_full_step
            run_converter_full_step.delay(task.id, task.draft_id, trace_id=trace_id)

        elif step_name == "full_converter":
            await self.task_repo.update_task_status(
                task_id=task.id,
                progress_percent=85,
            )

            from app.tasks.pipeline_formation import run_registry_step
            # Pass document_id and version_id to registry step
            document_id = getattr(task, 'document_id', None) or task.draft_id
            version_id = getattr(task, 'version_id', None)
            run_registry_step.delay(task.id, task.draft_id, document_id, version_id, trace_id=trace_id)

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
            document_id: Optional[int] = doc_data.get("document_id") or doc_data.get("id")
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
        upload_step = next((s for s in steps if s.step_name == "upload"), None)
        file_key = None
        if upload_step and upload_step.output_data:
            file_key = upload_step.output_data.get("file_key")

        current_trace_id = task.trace_id or ""

        # Determine full phase mode (P1F-9)
        full_mode = settings.pipeline.FULL_PHASE_MODE
        need_full_ocr = False
        if full_mode == "partial":
            need_full_ocr = True
        elif full_mode == "full":
            need_full_ocr = False
        else:  # "auto" — use full_completed flag
            need_full_ocr = not task.full_completed

        if need_full_ocr:
            # Partial preview or forced — need full OCR/Parser
            await self.task_repo.create_task_step(
                task_id=task_id,
                step_name="full_ocr",
                step_index=3,
                service_name="OCR Service",
                input_data={"file_key": file_key, "mode": "full", "draft_id": draft_id},
            )
            run_ocr_full_step.delay(task_id, draft_id, file_key, trace_id=current_trace_id)

        # Create full_converter step (always)
        await self.task_repo.create_task_step(
            task_id=task_id,
            step_name="full_converter",
            step_index=4,
            service_name="Converter-validator",
            input_data={"file_key": file_key, "mode": "full", "draft_id": draft_id},
        )

        # Create registry_creation step (now with document_id)
        await self.task_repo.create_task_step(
            task_id=task_id,
            step_name="registry_creation",
            step_index=5,
            service_name="Registry",
            input_data={"draft_id": draft_id, "document_id": document_id},
        )

        # Start the first step
        steps = await self.task_repo.get_task_steps(task_id)
        if need_full_ocr:
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
                    "Enqueued full Converter step (full preview, no OCR)",
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
