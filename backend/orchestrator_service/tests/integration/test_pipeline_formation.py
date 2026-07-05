"""
Integration tests for PipelineOrchestrator.

Tests the core orchestrator methods with a real async DB session
and mocked external service clients (RegistryServiceClient).

Each test creates its own Task and TaskStep records via the
TaskRepository and then exercises orchestrator methods.
"""

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.shared.mock_registry_client import MockRegistryClient

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
        assert updated.current_step_name == "Parser Service"
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
        # application/pdf &#8594; Parser Service (digital PDF by default)
        ocr_step = next(s for s in steps if s.step_name == "preview_ocr")
        assert ocr_step.status == "pending"
        assert ocr_step.service_name == "Parser Service"

        # Preview converter should be pending
        conv_step = next(s for s in steps if s.step_name == "preview_converter")
        assert conv_step.status == "pending"
        assert conv_step.service_name == "Converter-validator"


# ---------------------------------------------------------------------------
#  on_step_completed --- preview_ocr
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
#  on_step_completed --- preview_converter (partial preview)
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
        mock_registry = MockRegistryClient()
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

        # Verify task stage —> decision
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.pipeline_stage == TaskStage.DECISION.value
        assert updated.progress_percent == 50
        assert updated.full_completed is False

        # Verify Registry was called to update draft status
        mock_registry.assert_draft_status(draft_id=task.draft_id, expected_status="ready_for_approve")


# ---------------------------------------------------------------------------
#  on_step_completed --- preview_converter (full preview + auto-approve)
# ---------------------------------------------------------------------------


class TestOnStepCompletedPreviewConverterFullAutoApprove:
    """Converter completes with full preview (preview_not_supported=True)."""

    async def test_auto_approves_and_starts_full_phase(
        self, db_session: AsyncSession
    ):
        """Full preview: auto-approve triggers full phase steps."""
        from app.core.config import settings
        settings.pipeline.AUTO_APPROVE_ENABLED = True
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

        mock_registry = MockRegistryClient()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
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

        # Verify task stage goes to decision (auto-approve goes through decision
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
#  approve_draft --- partial preview
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

        mock_registry = MockRegistryClient()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
        ) as mock_parser_delay, patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            result = await orchestrator.approve_draft(draft_id=100, task_id=task.id)

        # Approve no longer creates document — verify None fields
        assert result["document_id"] is None
        assert result["version_id"] is None
        assert result["is_new_document"] is False

        # --- Critical: task must NOT be in terminal state after approve ---
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status != TaskStatus.COMPLETED.value, (
            "Task must NOT be completed after approve --- processing just started"
        )
        assert updated.pipeline_stage == TaskStage.FULL.value, (
            f"Pipeline stage must be FULL after approve, got {updated.pipeline_stage}"
        )
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

        # --- Celery task WAS dispatched (critical) ---
        mock_parser_delay.assert_called_once()
        call_args = mock_parser_delay.call_args
        assert call_args[0][0] == task.id, "task_id must be passed to parser delay"
        assert call_args[0][1] == 100, "draft_id must be passed to parser delay"
        assert call_args[0][2] == "test.pdf", "file_key must be passed to parser delay"


# ---------------------------------------------------------------------------
#  approve_draft --- full preview
# ---------------------------------------------------------------------------


class TestApproveDraftFull:
    """Approve after full preview (full_completed=True)."""

    async def test_skips_full_ocr_step(self, db_session: AsyncSession):
        """Full preview approve: only full_converter + registry_creation."""
        task = await _create_task(db_session, full_completed=True, total_steps=3)

        mock_registry = MockRegistryClient()

        # Create upload step with file_key (needed for approve_draft)
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
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ) as mock_converter_delay, patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            result = await orchestrator.approve_draft(draft_id=100, task_id=task.id)

        # Approve no longer creates document
        assert result["is_new_document"] is False

        # --- Critical: task must NOT be in terminal state after approve ---
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status != TaskStatus.COMPLETED.value, (
            "Task must NOT be completed after approve --- processing just started"
        )
        assert updated.pipeline_stage == TaskStage.FULL.value, (
            f"Pipeline stage must be FULL after approve, got {updated.pipeline_stage}"
        )
        assert updated.progress_percent == 50

        # Verify only full_converter + registry_creation (no full_ocr)
        all_steps = await repo.get_task_steps(task.id)
        step_names = [s.step_name for s in all_steps]
        assert "full_ocr" not in step_names
        assert "full_converter" in step_names
        assert "registry_creation" in step_names

        # Verify converter task WAS dispatched (fix for full_preview missing dispatch)
        mock_converter_delay.assert_called_once()


class TestApproveDraftVersionId:
    """Verify version_id is persisted in Task model after approve."""

    async def test_version_id_not_set_by_approve(self, db_session: AsyncSession):
        """approve_draft no longer sets document_id/version_id on Task.

        Document creation moved to _on_full_step_completed("full_converter").
        approve_draft now returns None for both fields.
        """
        task = await _create_task(db_session, full_completed=True, total_steps=3)
        repo = TaskRepository(db_session)

        mock_registry = MockRegistryClient()

        # Create upload step
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
        )
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 100, "task_id": task.id, "file_key": "test.pdf"},
        )

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            result = await orchestrator.approve_draft(draft_id=100, task_id=task.id)

        # Approve returns None for document fields (creation deferred to full_converter)
        assert result["document_id"] is None
        assert result["version_id"] is None
        assert result["is_new_document"] is False

        # Verify document_id/version_id are NOT persisted by approve
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.document_id is None, "document_id should remain None after approve"
        assert updated.version_id is None, "version_id should remain None after approve"


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
        mock_registry = MockRegistryClient()

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
        mock_registry.assert_draft_status(draft_id=100, expected_status="discarded")


# ---------------------------------------------------------------------------
#  start_pipeline --- error paths
# ---------------------------------------------------------------------------


class TestStartPipelineErrors:
    """Edge cases for start_pipeline."""

    async def test_task_not_found_raises_value_error(
        self, db_session: AsyncSession
    ):
        """start_pipeline with non-existent task raises ValueError."""
        orchestrator = PipelineOrchestrator(db_session)
        with pytest.raises(ValueError, match="Task not found: 99999"):
            await orchestrator.start_pipeline(
                draft_id=999, task_id=99999, file_key="f-test.pdf",
                mime_type="application/pdf",
            )

    async def test_start_pipeline_with_image_triggers_parser_first(
        self, db_session: AsyncSession
    ):
        """Image mime_type routes to Parser first (Parser-first strategy)."""
        task = await _create_task(db_session, draft_id=300, total_steps=3)
        orchestrator = PipelineOrchestrator(db_session)

        with patch(
            "app.core.pipeline.orchestrator.get_trace_id",
            return_value="trace-img-001",
        ), patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
            new_callable=MagicMock,
        ) as mock_ocr, patch(
            "app.tasks.pipeline_formation.run_parser_preview_step.delay",
            new_callable=MagicMock,
        ) as mock_parser:
            await orchestrator.start_pipeline(
                draft_id=300, task_id=task.id,
                file_key="f-image.png",
                mime_type="image/png",
            )

        # Parser-first: Parser is called even for images
        mock_parser.assert_called_once()
        mock_ocr.assert_not_called()


# ---------------------------------------------------------------------------
#  stop_duplicate / reject
# ---------------------------------------------------------------------------


class TestStopDuplicateDraft:
    """stop_duplicate_draft flow."""

    async def test_stop_duplicate_sets_status(
        self, db_session: AsyncSession
    ):
        """stop_duplicate discards the draft and fails the task."""
        task = await _create_task(db_session, draft_id=400, total_steps=1)
        orchestrator = PipelineOrchestrator(db_session)

        mock_reg = MockRegistryClient()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_reg,
        ):
            await orchestrator.stop_duplicate_draft(
                draft_id=400, task_id=task.id,
            )

        # Verify draft status was updated to discarded
        mock_reg.assert_draft_status(draft_id=400, expected_status="discarded")

        # Verify task was failed
        repo = TaskRepository(db_session)
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status == TaskStatus.FAILED.value


class TestApproveDraftMetadataOverrides:
    """approve_draft with metadata_overrides."""

    async def test_metadata_overrides_saved_to_snapshot(
        self, db_session: AsyncSession
    ):
        """Custom metadata_overrides are saved to snapshot (not create_document).

        approve_draft no longer creates document; overrides go into
        create_draft_snapshot instead.
        """
        task = await _create_task(
            db_session, draft_id=500, total_steps=3,
        )
        # Advance to decision stage
        repo = TaskRepository(db_session)
        await repo.update_task_status(
            task_id=task.id,
            stage=TaskStage.DECISION.value,
            step_name="preview_converter",
            step_index=1,
        )

        orchestrator = PipelineOrchestrator(db_session)

        mock_registry = MockRegistryClient()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
            new_callable=MagicMock,
        ) as mock_parser_delay, patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
            new_callable=MagicMock,
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
            new_callable=MagicMock,
        ):
            result = await orchestrator.approve_draft(
                draft_id=500, task_id=task.id,
                metadata_overrides={"title": "Custom Title", "doc_code": "CUSTOM-001"},
            )

        # Verify snapshot was created (approve no longer calls create_document)
        assert any(
            method == "create_draft_snapshot"
            for method, _ in mock_registry.call_log
        ), "create_draft_snapshot should be called in approve_draft"

        # Verify approve returns None for document fields
        assert result["document_id"] is None
        assert result["version_id"] is None

        # --- Critical: task must NOT be completed after approve ---
        repo = TaskRepository(db_session)
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status != TaskStatus.COMPLETED.value, (
            "Task must NOT be completed after approve with metadata_overrides"
        )
        assert updated.pipeline_stage == TaskStage.FULL.value

        # --- Celery task WAS dispatched (critical) ---
        mock_parser_delay.assert_called_once()


# ---------------------------------------------------------------------------
#  on_step_completed --- full_converter (document creation)
# ---------------------------------------------------------------------------


class TestOnFullStepCompletedConverter:
    """Full_converter step now creates document in Registry.

    Document creation was moved from approve_draft to
    _on_full_step_completed("full_converter").
    """

    async def test_creates_document_and_sets_task_ids(self, db_session: AsyncSession):
        """full_converter completion creates doc, sets task.document_id/version_id."""
        task = await _create_task(db_session, full_completed=True, total_steps=3)
        repo = TaskRepository(db_session)

        # Create upload + full_converter steps
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator", input_data={"file_key": "test.pdf"},
        )
        await repo.complete_task_step(upload.id, output_data={
            "draft_id": 100, "task_id": task.id, "file_key": "test.pdf",
        })

        conv = await repo.create_task_step(
            task_id=task.id, step_name="full_converter", step_index=4,
            service_name="Converter-validator",
        )
        await repo.start_task_step(conv.id)

        mock_registry = MockRegistryClient()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="full_converter",
                output_data={
                    "document": {"content": [{"text": "test"}]},
                    "metadata": {"title": "Test Doc", "doc_code": "GOST 1234"},
                },
            )

        # Verify document was created and task IDs were set
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.document_id is not None, \
            "document_id should be set after full_converter"
        assert updated.version_id is not None, \
            "version_id should be set after full_converter"

        # Verify draft status was synced to approved
        mock_registry.assert_draft_status(draft_id=100, expected_status="approved")

        # Verify create_document was called
        assert any(
            method == "create_document"
            for method, _ in mock_registry.call_log
        ), "create_document should be called in full_converter handler"


# ---------------------------------------------------------------------------
#  on_step_failed --- retry exhaustion
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
            task.id, "preview_ocr", task=task,
        )

        # Verify step was marked as failed
        failed_step = await repo.get_task_steps(task.id)
        assert failed_step[0].status == "failed"
        assert failed_step[0].error_code == "OCR_ERROR"


# ---------------------------------------------------------------------------
#  _run_ocr_fallback --- guard against duplicate OCR (B1)
# ---------------------------------------------------------------------------


class TestRunOcrFallback:
    """Tests for _run_ocr_fallback guard (B1: OCR cycle prevention)."""

    async def test_skips_when_ocr_already_completed(self, db_session: AsyncSession):
        """_run_ocr_fallback returns early if OCR already completed."""
        task = await _create_task(db_session, draft_id=100, total_steps=3)
        repo = TaskRepository(db_session)
        # Create Parser preview_ocr (completed)
        parser_step = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "test.pdf", "mode": "preview"},
        )
        await repo.start_task_step(parser_step.id)
        await repo.complete_task_step(parser_step.id, output_data={"pages": 3})

        # Create OCR preview_ocr (already completed --- this is the guard)
        ocr_step = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="OCR Service",
            input_data={"file_key": "test.pdf", "mode": "preview"},
        )
        await repo.start_task_step(ocr_step.id)
        await repo.complete_task_step(ocr_step.id, output_data={"pages": 3})

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ), patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ) as mock_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._run_ocr_fallback(task, file_key="test.pdf")

        # Verify that delay was NOT called (guard prevented new OCR)
        mock_delay.assert_not_called()

        # Verify no new step was created
        steps = await repo.get_task_steps(task.id)
        ocr_completed = [
            s for s in steps
            if s.step_name == "preview_ocr"
            and s.service_name == "OCR Service"
            and s.status == "completed"
        ]
        assert len(ocr_completed) == 1  # still only one OCR step

    async def test_creates_new_step_when_no_completed_ocr(self, db_session: AsyncSession):
        """_run_ocr_fallback creates new OCR step when none exists."""
        task = await _create_task(db_session, draft_id=100, total_steps=3)
        repo = TaskRepository(db_session)
        # Only Parser step exists (completed)
        parser_step = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "test.pdf", "mode": "preview"},
        )
        await repo.start_task_step(parser_step.id)
        await repo.complete_task_step(parser_step.id, output_data={"pages": 3})

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ), patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ) as mock_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._run_ocr_fallback(task, file_key="test.pdf")

        # Verify delay was called
        mock_delay.assert_called_once()

        # Verify new OCR step was created AND started (running, not just pending)
        steps = await repo.get_task_steps(task.id)
        ocr_running = [
            s for s in steps
            if s.step_name == "preview_ocr"
            and s.service_name == "OCR Service"
            and s.status == "running"
        ]
        assert len(ocr_running) == 1, \
            f"Expected 1 running OCR step, got {len(ocr_running)}. Steps: {[(s.step_name, s.service_name, s.status) for s in steps]}"

    async def test_starts_existing_pending_step(self, db_session: AsyncSession):
        """_run_ocr_fallback starts existing pending OCR step instead of creating duplicate."""
        task = await _create_task(db_session, draft_id=100, total_steps=3)
        repo = TaskRepository(db_session)
        # Create Parser step (completed)
        parser_step = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "test.pdf", "mode": "preview"},
        )
        await repo.start_task_step(parser_step.id)
        await repo.complete_task_step(parser_step.id, output_data={"pages": 3})

        # Create an existing OCR step left in "pending" (from a previous fallback attempt)
        existing_ocr = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="OCR Service",
            input_data={"file_key": "test.pdf", "mode": "preview", "max_pages": 3, "draft_id": 100},
        )
        # Step stays pending --- not started

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ), patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ) as mock_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._run_ocr_fallback(task, file_key="test.pdf")

        # Verify delay was called
        mock_delay.assert_called_once()

        # Verify NO new step was created (existing pending step was reused)
        steps = await repo.get_task_steps(task.id)
        ocr_steps = [
            s for s in steps
            if s.step_name == "preview_ocr"
            and s.service_name == "OCR Service"
        ]
        assert len(ocr_steps) == 1, \
            f"Expected 1 OCR step, got {len(ocr_steps)}"

        # Verify existing step is now RUNNING (was started, not left pending)
        assert ocr_steps[0].status == "running", \
            f"Expected step to be running, got {ocr_steps[0].status}"


# ---------------------------------------------------------------------------
#  cleanup_stale_tasks --- stale running steps with health check (B2)
# ---------------------------------------------------------------------------


class TestCleanupStaleRunningSteps:
    """Tests for stale running steps detection in cleanup."""

    async def test_fails_step_when_service_dead(self, db_session: AsyncSession):
        """
        cleanup_stale_tasks fails a stale running step
        when the service health check fails (dead service).
        """
        task = await _create_task(db_session, draft_id=100, total_steps=3)
        repo = TaskRepository(db_session)
        step = await repo.create_task_step(
            task_id=task.id, step_name="full_ocr", step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "test.pdf"},
        )
        await repo.start_task_step(step.id)

        # Set started_at far in the past
        from datetime import datetime, timedelta, timezone
        db_step = await db_session.get(type(step), step.id)
        db_step.started_at = datetime.now(timezone.utc) - timedelta(minutes=15)
        await db_session.flush()

        with patch(
            "app.core.pipeline.orchestrator.settings.pipeline.RUNNING_STEP_TIMEOUT",
            600,
        ), patch.object(
            PipelineOrchestrator, "_check_service_health",
            return_value=False,  # service is dead
        ), patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            cleaned = await orchestrator.cleanup_stale_tasks()

        assert cleaned >= 1
        # Verify step was failed
        failed = await repo.get_task_steps(task.id)
        assert failed[0].status == "failed"
        assert failed[0].error_code == "SERVICE_DEAD"

    async def test_skips_step_when_service_alive(self, db_session: AsyncSession):
        """
        cleanup_stale_tasks does NOT fail a stale running step
        when the service health check succeeds (just slow).
        """
        task = await _create_task(db_session, draft_id=100, total_steps=3)
        repo = TaskRepository(db_session)
        step = await repo.create_task_step(
            task_id=task.id, step_name="full_ocr", step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "test.pdf"},
        )
        await repo.start_task_step(step.id)

        from datetime import datetime, timedelta, timezone
        db_step = await db_session.get(type(step), step.id)
        db_step.started_at = datetime.now(timezone.utc) - timedelta(minutes=15)
        await db_session.flush()

        with patch(
            "app.core.pipeline.orchestrator.settings.pipeline.RUNNING_STEP_TIMEOUT",
            600,
        ), patch.object(
            PipelineOrchestrator, "_check_service_health",
            return_value=True,  # service is alive
        ), patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            cleaned = await orchestrator.cleanup_stale_tasks()

        # May clean up other stale items, but NOT our step
        all_steps = await repo.get_task_steps(task.id)
        our_step = next(s for s in all_steps if s.id == step.id)
        assert our_step.status == "running"  # not failed


class TestCheckServiceHealth:
    """Tests for _check_service_health."""

    async def test_returns_true_when_service_responds(self, db_session: AsyncSession):
        """_check_service_health returns True for healthy service."""
        class _MockHttpxClient:
            """Fake httpx.AsyncClient that returns 200 for any GET."""
            def __init__(self, *args, **kwargs):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def get(self, url, **kwargs):
                class MockResponse:
                    status_code = 200
                return MockResponse()

        with patch("httpx.AsyncClient", _MockHttpxClient):
            orchestrator = PipelineOrchestrator(db_session)
            result = await orchestrator._check_service_health("Parser Service")
            assert result is True

    async def test_returns_false_when_service_unreachable(self, db_session: AsyncSession):
        """_check_service_health returns False for unreachable service."""
        class _MockDeadHttpxClient:
            """Fake httpx.AsyncClient that raises ConnectError."""
            def __init__(self, *args, **kwargs):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def get(self, url, **kwargs):
                raise httpx.ConnectError("Connection refused")

        with patch("httpx.AsyncClient", _MockDeadHttpxClient):
            orchestrator = PipelineOrchestrator(db_session)
            result = await orchestrator._check_service_health("Parser Service")
            assert result is False

    async def test_returns_true_for_unknown_service(self, db_session: AsyncSession):
        """Returns True when service name not in health check list."""
        orchestrator = PipelineOrchestrator(db_session)
        result = await orchestrator._check_service_health("unknown-service")
        assert result is True


# ---------------------------------------------------------------------------
#  confirm_draft --- review_required &#8594; validation
# ---------------------------------------------------------------------------


class TestConfirmDraft:
    """Orchestrator.confirm_draft() behavior.

    Critical: confirm_draft must dispatch actual processing (parser/OCR &#8594; converter)
    and NOT mark the task as completed. The draft must stay visible in UI
    until real processing finishes.
    """

    async def test_confirm_after_review_required_starts_processing(
        self, db_session: AsyncSession
    ):
        """Confirm transitions task to full stage and dispatches parser."""
        task = await _create_task(db_session, full_completed=False, total_steps=3)
        # Set task to the correct state for confirm
        task.status = TaskStatus.ACTIVE.value
        task.pipeline_stage = TaskStage.DECISION.value
        await db_session.flush()

        repo = TaskRepository(db_session)
        # Create upload step with file_key (needed for confirm_draft)
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator", input_data={"file_key": "test.pdf"},
        )
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 100, "task_id": task.id, "file_key": "test.pdf"},
        )

        mock_registry = MockRegistryClient()
        mock_registry._ensure_draft(draft_id=100, status="review_required")

        # Spy on celery task dispatch to verify it's actually called
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
        ) as mock_parser_delay, patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            result = await orchestrator.confirm_draft(
                draft_id=100, task_id=task.id,
            )

        # --- Critical assertions: task NOT in terminal state ---
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status != TaskStatus.COMPLETED.value, (
            "Task must NOT be completed after confirm --- processing just started"
        )
        assert updated.status != TaskStatus.FAILED.value, (
            "Task must NOT be failed after confirm"
        )
        # Pipeline stage must be FULL, not REGISTRY or INDEXATION
        assert updated.pipeline_stage == TaskStage.FULL.value, (
            f"Pipeline stage must be FULL after confirm, got {updated.pipeline_stage}"
        )

        # --- Steps created ---
        all_steps = await repo.get_task_steps(task.id)
        step_names = [s.step_name for s in all_steps]
        assert "full_ocr" in step_names, "full_ocr step must be created"
        assert "full_converter" in step_names, "full_converter step must be created"

        # Steps must NOT be completed yet
        full_ocr = next(s for s in all_steps if s.step_name == "full_ocr")
        assert full_ocr.status in ("pending", "running"), (
            f"full_ocr must be pending/running, got {full_ocr.status}"
        )

        # --- Celery task WAS dispatched (critical: was silently skipped in tests) ---
        mock_parser_delay.assert_called_once()
        call_args = mock_parser_delay.call_args
        assert call_args[0][0] == task.id, "task_id must be passed to parser delay"
        assert call_args[0][1] == 100, "draft_id must be passed to parser delay"
        assert call_args[0][2] == "test.pdf", "file_key must be passed to parser delay"

        # --- Registry was notified ---
        mock_registry.assert_draft_status(draft_id=100, expected_status="validation")

        # --- Return value ---
        assert result["status"] == "validation", (
            f"confirm must return status='validation', got {result['status']}"
        )
        assert result["queued"] is False, "should not be queued"
        assert result["draft_id"] == 100
        assert result["task_id"] == task.id

    async def test_confirm_already_terminal_raises_error(
        self, db_session: AsyncSession
    ):
        """Confirm on completed/failed task must raise ValueError."""
        task = await _create_task(db_session)
        task.status = TaskStatus.COMPLETED.value
        await db_session.flush()

        mock_registry = MockRegistryClient()
        mock_registry._ensure_draft(draft_id=100, status="review_required")

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            with pytest.raises(ValueError, match="already in terminal state"):
                await orchestrator.confirm_draft(
                    draft_id=100, task_id=task.id,
                )

    async def test_confirm_wrong_draft_status_raises_error(
        self, db_session: AsyncSession
    ):
        """Confirm on draft not in review_required must raise ValueError."""
        task = await _create_task(db_session)
        task.status = TaskStatus.ACTIVE.value
        task.pipeline_stage = TaskStage.DECISION.value
        await db_session.flush()

        upload = await TaskRepository(db_session).create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator", input_data={"file_key": "test.pdf"},
        )
        await TaskRepository(db_session).complete_task_step(
            upload.id,
            output_data={"draft_id": 100, "task_id": task.id, "file_key": "test.pdf"},
        )

        mock_registry = MockRegistryClient()
        # Draft is NOT in review_required --- should be "ready_for_approve"
        mock_registry._ensure_draft(draft_id=100, status="ready_for_approve")

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            with pytest.raises(ValueError, match="Confirm requires draft status"):
                await orchestrator.confirm_draft(
                    draft_id=100, task_id=task.id,
                )

    async def test_confirm_queued_when_no_free_slot(
        self, db_session: AsyncSession
    ):
        """Confirm when max concurrent tasks reached must queue."""
        task = await _create_task(db_session, full_completed=False, total_steps=3)
        task.status = TaskStatus.ACTIVE.value
        task.pipeline_stage = TaskStage.DECISION.value
        await db_session.flush()

        repo = TaskRepository(db_session)
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator", input_data={"file_key": "test.pdf"},
        )
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 100, "task_id": task.id, "file_key": "test.pdf"},
        )

        mock_registry = MockRegistryClient()
        mock_registry._ensure_draft(draft_id=100, status="review_required")

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ), patch.object(
            PipelineOrchestrator, "_has_free_slot",
            return_value=False,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            result = await orchestrator.confirm_draft(
                draft_id=100, task_id=task.id,
            )

        # Task should be queued
        assert result["queued"] is True
        assert result["status"] == "queued"

        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status == TaskStatus.QUEUED.value
