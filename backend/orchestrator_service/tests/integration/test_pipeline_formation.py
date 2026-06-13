"""
Integration tests for PipelineOrchestrator.

Tests the core orchestrator methods with a real async DB session
and mocked external service clients (RegistryServiceClient).

Each test creates its own Task and TaskStep records via the
TaskRepository and then exercises orchestrator methods.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.fsm import TaskStage, TaskStatus
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.repositories.pipeline import TaskRepository

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

async def _create_task(
    db: AsyncSession,
    draft_id: int = 100,
    pipeline_type: str = "formation",
    total_steps: int = 3,
    full_completed: bool = False,
    retry_count: int = 0,
) -> "Task":
    """Create a minimal Task record for testing."""
    repo = TaskRepository(db)
    task = await repo.create_task(
        draft_id=draft_id,
        pipeline_type=pipeline_type,
        total_steps=total_steps,
    )
    task.full_completed = full_completed
    task.retry_count = retry_count
    await db.flush()
    return task


async def _create_preview_steps(
    db: AsyncSession,
    task_id: int,
    upload_status: str = "completed",
    ocr_status: str = "running",
    converter_status: str = "pending",
) -> list:
    """Create the three standard preview steps for a task."""
    repo = TaskRepository(db)
    upload = await repo.create_task_step(
        task_id=task_id, step_name="upload", step_index=0,
        service_name="Orchestrator", input_data={"file_key": "test.pdf"},
    )
    ocr = await repo.create_task_step(
        task_id=task_id, step_name="preview_ocr", step_index=1,
        service_name="OCR Service",
        input_data={"file_key": "test.pdf", "mode": "preview", "max_pages": 3},
    )
    converter = await repo.create_task_step(
        task_id=task_id, step_name="preview_converter", step_index=2,
        service_name="Converter-validator",
        input_data={"file_key": "test.pdf", "mode": "preview"},
    )
    if upload_status == "completed":
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 100, "task_id": task_id, "file_key": "test.pdf"},
        )
    if ocr_status == "running":
        await repo.start_task_step(ocr.id)
    elif ocr_status == "completed":
        await repo.start_task_step(ocr.id)
        await repo.complete_task_step(ocr.id)
    if converter_status == "running":
        await repo.start_task_step(converter.id)
    return [upload, ocr, converter]


# ---------------------------------------------------------------------------
#  start_pipeline
# ---------------------------------------------------------------------------


class TestStartPipeline:
    """Orchestrator.start_pipeline() behavior."""

    async def test_creates_steps_and_sets_stage(self, db_session: AsyncSession):
        """start_pipeline creates 3 steps and transitions task to preview."""
        task = await _create_task(db_session)
        task_id = task.id

        with patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_preview_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.start_pipeline(
                draft_id=100,
                task_id=task_id,
                file_key="drafts/100/test.pdf",
                mime_type="application/pdf",
            )

        # Reload task
        repo = TaskRepository(db_session)
        updated = await repo.get_task(task_id)
        assert updated is not None
        assert updated.pipeline_stage == TaskStage.PREVIEW.value
        assert updated.current_step_name == "upload"
        assert updated.current_step_index == 0
        assert updated.progress_percent == 10

        # Verify 3 steps exist
        steps = await repo.get_task_steps(task_id)
        assert len(steps) == 3
        step_names = [s.step_name for s in steps]
        assert step_names == ["upload", "preview_ocr", "preview_converter"]

        # Upload step should be completed
        upload_step = next(s for s in steps if s.step_name == "upload")
        assert upload_step.status == "completed"
        assert upload_step.service_name == "Orchestrator"

        # Preview OCR should be pending (enqueued, not started locally)
        ocr_step = next(s for s in steps if s.step_name == "preview_ocr")
        assert ocr_step.status == "pending"
        assert ocr_step.service_name == "OCR Service"

        # Preview converter should be pending
        conv_step = next(s for s in steps if s.step_name == "preview_converter")
        assert conv_step.status == "pending"
        assert conv_step.service_name == "Converter-validator"


# ---------------------------------------------------------------------------
#  on_step_completed — preview_ocr
# ---------------------------------------------------------------------------


class TestOnStepCompletedPreviewOcr:
    """Orchestrator.on_step_completed() for preview_ocr step."""

    async def test_marks_step_completed_and_updates_progress(
        self, db_session: AsyncSession
    ):
        """Completing preview_ocr updates step status and progress."""
        task = await _create_task(db_session)
        steps = await _create_preview_steps(
            db_session, task.id, ocr_status="running"
        )
        ocr_step = steps[1]
        task_id = task.id

        # Mock RegistryServiceClient to avoid real calls
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_completed(
                task_id=task_id,
                step_name="preview_ocr",
                input_data={"file_key": "test.pdf", "mode": "preview", "max_pages": 3},
                output_data={
                    "preview_not_supported": False,
                    "pages_processed": 3,
                    "metadata": {"doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56"},
                },
            )

        # Reload step
        repo = TaskRepository(db_session)
        updated_step = await repo.get_task_steps(task_id)
        ocr = next(s for s in updated_step if s.step_name == "preview_ocr")
        assert ocr.status == "completed"
        assert ocr.output_data == {
            "preview_not_supported": False,
            "pages_processed": 3,
            "metadata": {"doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56"},
        }

        # Progress should be updated
        task = await repo.get_task(task_id)
        assert task is not None
        assert task.progress_percent > 0


# ---------------------------------------------------------------------------
#  on_step_completed — preview_converter (partial preview)
# ---------------------------------------------------------------------------


class TestOnStepCompletedPreviewConverterPartial:
    """Converter completes with partial preview (preview_not_supported=False)."""

    async def test_sets_decision_stage_and_updates_draft(
        self, db_session: AsyncSession
    ):
        """Partial preview: stage &#8594; decision, draft &#8594; ready_for_approve."""
        task = await _create_task(db_session)
        steps = await _create_preview_steps(
            db_session, task.id, ocr_status="completed", converter_status="running",
        )
        # Set OCR output_data to indicate partial preview
        repo = TaskRepository(db_session)
        ocr_step = steps[1]
        ocr_step.output_data = {"preview_not_supported": False, "pages_processed": 3}
        await db_session.flush()

        converter_output = {
            "validated": True,
            "metadata": {"doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56", "title": "Test"},
        }

        # Mock RegistryServiceClient
        mock_registry = AsyncMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="preview_converter",
                input_data={"file_key": "test.pdf", "mode": "preview"},
                output_data=converter_output,
            )

        # Verify task stage &#8594; decision
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.pipeline_stage == TaskStage.DECISION.value
        assert updated.progress_percent == 50
        assert updated.full_completed is False

        # Verify Registry was called to update draft status
        mock_registry.update_draft_status.assert_awaited_once_with(
            draft_id=task.draft_id,
            status="ready_for_approve",
        )


# ---------------------------------------------------------------------------
#  on_step_completed — preview_converter (full preview + auto-approve)
# ---------------------------------------------------------------------------


class TestOnStepCompletedPreviewConverterFullAutoApprove:
    """Converter completes with full preview (preview_not_supported=True)."""

    async def test_auto_approves_and_starts_full_phase(
        self, db_session: AsyncSession
    ):
        """Full preview: auto-approve triggers full phase steps."""
        task = await _create_task(db_session, total_steps=3)
        steps = await _create_preview_steps(
            db_session, task.id, ocr_status="completed", converter_status="running",
        )
        # Set OCR output to indicate full preview
        repo = TaskRepository(db_session)
        ocr_step = steps[1]
        ocr_step.output_data = {"preview_not_supported": True, "pages_processed": 3}
        await db_session.flush()

        converter_output = {
            "validated": True,
            "metadata": {"doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56", "title": "Test"},
        }

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ), patch(
            "app.tasks.pipeline_formation.run_ocr_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="preview_converter",
                input_data={"file_key": "test.pdf", "mode": "preview"},
                output_data=converter_output,
            )

        # Verify task stage &#8594; decision (auto-approve goes through decision
        # stage but immediately continues to full)
        updated = await repo.get_task(task.id)
        assert updated is not None
        # full_completed flag was set
        assert updated.full_completed is True

        # Should have created additional steps for full phase
        # When full_completed=True, full_ocr is skipped (already done in preview)
        # Only full_converter and registry_creation are added
        all_steps = await repo.get_task_steps(task.id)
        step_names = [s.step_name for s in all_steps]
        assert "full_ocr" not in step_names, \
            "full_ocr should be skipped when full_completed=True"
        assert "full_converter" in step_names
        assert "registry_creation" in step_names


# ---------------------------------------------------------------------------
#  approve_draft — partial preview
# ---------------------------------------------------------------------------


class TestApproveDraftPartial:
    """Approve after partial preview (full_completed=False)."""

    async def test_creates_full_phase_steps(self, db_session: AsyncSession):
        """Partial approve: creates full_ocr, full_converter, registry_creation."""
        task = await _create_task(db_session, full_completed=False, total_steps=3)
        # Create upload step with file_key
        repo = TaskRepository(db_session)
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
            input_data={"file_key": "test.pdf"},
        )
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 100, "task_id": task.id, "file_key": "test.pdf"},
        )

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ), patch(
            "app.tasks.pipeline_formation.run_ocr_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.approve_draft(draft_id=100, task_id=task.id)

        # Verify task stage &#8594; full
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.pipeline_stage == TaskStage.FULL.value
        assert updated.progress_percent == 50

        # Verify new steps created
        all_steps = await repo.get_task_steps(task.id)
        step_names = [s.step_name for s in all_steps]
        assert "full_ocr" in step_names
        assert "full_converter" in step_names
        assert "registry_creation" in step_names

        # Verify full_ocr step is started (running)
        full_ocr = next(s for s in all_steps if s.step_name == "full_ocr")
        assert full_ocr.status == "running"


# ---------------------------------------------------------------------------
#  approve_draft — full preview
# ---------------------------------------------------------------------------


class TestApproveDraftFull:
    """Approve after full preview (full_completed=True)."""

    async def test_skips_full_ocr_step(self, db_session: AsyncSession):
        """Full preview approve: only full_converter + registry_creation."""
        task = await _create_task(db_session, full_completed=True, total_steps=3)

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.approve_draft(draft_id=100, task_id=task.id)

        # Verify new steps
        repo = TaskRepository(db_session)
        all_steps = await repo.get_task_steps(task.id)
        step_names = [s.step_name for s in all_steps]
        assert "full_ocr" not in step_names, \
            "full_ocr should be skipped when full_completed=True"
        assert "full_converter" in step_names
        assert "registry_creation" in step_names


# ---------------------------------------------------------------------------
#  reject_draft
# ---------------------------------------------------------------------------


class TestRejectDraft:
    """Orchestrator.reject_draft() behavior."""

    async def test_marks_task_failed_and_updates_draft(
        self, db_session: AsyncSession
    ):
        """reject_draft sets status=failed, stage=decision, draft=discarded."""
        task = await _create_task(db_session)
        mock_registry = AsyncMock()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.reject_draft(draft_id=100, task_id=task.id)

        # Verify task status
        repo = TaskRepository(db_session)
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status == TaskStatus.FAILED.value
        assert updated.pipeline_stage == TaskStage.DECISION.value

        # Verify Registry was called to set discarded
        mock_registry.update_draft_status.assert_awaited_once_with(
            draft_id=100,
            status="discarded",
        )


# ---------------------------------------------------------------------------
#  on_step_failed — retry exhaustion
# ---------------------------------------------------------------------------


class TestOnStepFailedRetryExhausted:
    """Step failure when retry_count exceeds max retries."""

    async def test_fails_task_and_triggers_saga_compensation(
        self, db_session: AsyncSession
    ):
        """When retries exhausted, task fails and SagaCoordinator.compensate called."""
        max_retries = settings.pipeline.MAX_STEP_RETRIES
        # Set retry_count >= max_retries so retries are considered exhausted
        task = await _create_task(
            db_session, retry_count=max_retries, total_steps=3,
        )
        # Create a running step
        repo = TaskRepository(db_session)
        step = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="OCR Service",
        )
        await repo.start_task_step(step.id)

        # Mock SagaCoordinator and RegistryServiceClient
        with patch(
            "app.core.pipeline.orchestrator.SagaCoordinator",
        ) as mock_saga_cls, patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ):
            mock_saga = mock_saga_cls.return_value
            mock_saga.compensate = AsyncMock()

            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_failed(
                task_id=task.id,
                step_name="preview_ocr",
                error_code="OCR_ERROR",
                error_message="Service unavailable",
            )

        # Verify task status &#8594; failed
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status == TaskStatus.FAILED.value

        # Verify Saga compensation was triggered
        mock_saga.compensate.assert_awaited_once_with(
            task.id, "preview_ocr",
        )

        # Verify step was marked as failed
        failed_step = await repo.get_task_steps(task.id)
        assert failed_step[0].status == "failed"
        assert failed_step[0].error_code == "OCR_ERROR"
