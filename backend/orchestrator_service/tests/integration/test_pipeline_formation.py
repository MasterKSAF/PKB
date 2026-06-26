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
        # application/pdf &#8594; Parser Service (digital PDF by default)
        ocr_step = next(s for s in steps if s.step_name == "preview_ocr")
        assert ocr_step.status == "pending"
        assert ocr_step.service_name == "Parser Service"

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

        mock_registry = AsyncMock()
        mock_registry.get_draft = AsyncMock(return_value={"data": {"title_key": "Test", "document_key": "TEST-001"}})
        mock_registry.get_draft_preview = AsyncMock(return_value={"data": {"title": "Full Preview", "doc_code": "GOST 1234"}})
        mock_registry.create_document = AsyncMock(return_value={
            "data": {
                "document_id": 42,
                "version_id": 421,
                "is_new_document": True,
            }
        })
        mock_registry.update_draft_status = AsyncMock()
        mock_registry.close = AsyncMock()

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

        mock_registry = AsyncMock()
        mock_registry.get_draft = AsyncMock(return_value={"data": {"title_key": "Test", "document_key": "TEST-001"}})
        mock_registry.get_draft_preview = AsyncMock(return_value={"data": {}})
        mock_registry.create_document = AsyncMock(return_value={
            "data": {
                "document_id": 100,
                "version_id": 1001,
                "is_new_document": True,
            }
        })
        mock_registry.update_draft_status = AsyncMock()
        mock_registry.close = AsyncMock()

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
            result = await orchestrator.approve_draft(draft_id=100, task_id=task.id)

        # Verify create_document was called
        mock_registry.create_document.assert_awaited_once()
        assert result["document_id"] == 100
        assert result["version_id"] == 1001
        assert result["is_new_document"] is True

        # Verify task stage goes to full
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

        mock_registry = AsyncMock()
        mock_registry.get_draft = AsyncMock(return_value={"data": {"title_key": "Test", "document_key": "TEST-001"}})
        mock_registry.get_draft_preview = AsyncMock(return_value={"data": {"title": "Full Preview"}})
        mock_registry.create_document = AsyncMock(return_value={
            "data": {
                "document_id": 100,
                "version_id": 1001,
                "is_new_document": True,
            }
        })
        mock_registry.update_draft_status = AsyncMock()
        mock_registry.close = AsyncMock()

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
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            result = await orchestrator.approve_draft(draft_id=100, task_id=task.id)

        # Verify create_document was called
        mock_registry.create_document.assert_awaited_once()
        assert result["is_new_document"] is True

        # Verify task stage goes to full
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.pipeline_stage == TaskStage.FULL.value
        assert updated.progress_percent == 50

        # Verify only full_converter + registry_creation (no full_ocr)
        all_steps = await repo.get_task_steps(task.id)
        step_names = [s.step_name for s in all_steps]
        assert "full_ocr" not in step_names
        assert "full_converter" in step_names
        assert "registry_creation" in step_names


class TestApproveDraftVersionId:
    """Verify version_id is persisted in Task model after approve."""

    async def test_version_id_saved_to_task(self, db_session: AsyncSession):
        """version_id from Registry.create_document is saved to Task."""
        task = await _create_task(db_session, full_completed=True, total_steps=3)
        repo = TaskRepository(db_session)

        mock_registry = AsyncMock()
        mock_registry.get_draft = AsyncMock(return_value={"data": {"title_key": "Test", "document_key": "TEST-001"}})
        mock_registry.get_draft_preview = AsyncMock(return_value={"data": {"title": "Full Preview"}})
        mock_registry.create_document = AsyncMock(return_value={
            "data": {
                "document_id": 200,
                "version_id": 2001,
                "is_new_document": True,
            }
        })
        mock_registry.update_draft_status = AsyncMock()
        mock_registry.close = AsyncMock()

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

        # Verify returned values
        assert result["document_id"] == 200
        assert result["version_id"] == 2001
        assert result["is_new_document"] is True

        # Verify version_id PERSISTED in DB (critical: was a bug!)
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.document_id == 200, "document_id should be persisted in Task"
        assert updated.version_id == 2001, "version_id should be persisted in Task"


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
#  start_pipeline — error paths
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

    async def test_start_pipeline_with_image_triggers_ocr_branch(
        self, db_session: AsyncSession
    ):
        """Image mime_type routes to OCR Service branch."""
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

        # Verify OCR branch was taken (parser should NOT be called)
        mock_ocr.assert_called_once()
        mock_parser.assert_not_called()


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

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_reg_cls:
            mock_reg = mock_reg_cls.return_value
            mock_reg.update_draft_status = AsyncMock()
            mock_reg.close = AsyncMock()

            await orchestrator.stop_duplicate_draft(
                draft_id=400, task_id=task.id,
            )

        # Verify draft status was updated to discarded
        mock_reg.update_draft_status.assert_awaited_once_with(
            draft_id=400, status="discarded",
        )

        # Verify task was failed
        repo = TaskRepository(db_session)
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status == TaskStatus.FAILED.value


class TestApproveDraftMetadataOverrides:
    """approve_draft with metadata_overrides."""

    async def test_metadata_overrides_passed_to_create_document(
        self, db_session: AsyncSession
    ):
        """Custom metadata_overrides propagate to Registry.create_document."""
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

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_reg_cls, patch(
            "app.tasks.pipeline_formation.run_ocr_full_step.delay",
            new_callable=MagicMock,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
            new_callable=MagicMock,
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
            new_callable=MagicMock,
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
            new_callable=MagicMock,
        ):
            mock_reg = mock_reg_cls.return_value
            mock_reg.get_draft = AsyncMock(return_value={"data": {"title_key": "Test", "document_key": "TEST-001"}})
            mock_reg.get_draft_preview = AsyncMock(return_value={"data": {"title": "Test"}})
            mock_reg.create_document = AsyncMock(return_value={
                "data": {"document_id": 42, "version_id": 421},
            })
            mock_reg.create_draft_snapshot = AsyncMock()
            mock_reg.close = AsyncMock()
            mock_reg.update_draft_status = AsyncMock()

            result = await orchestrator.approve_draft(
                draft_id=500, task_id=task.id,
                metadata_overrides={"title": "Custom Title", "doc_code": "CUSTOM-001"},
            )

        # Verify create_document received overrides merged into payload
        call_kwargs = mock_reg.create_document.call_args[0][0]
        assert call_kwargs["title"] == "Custom Title"
        assert call_kwargs["doc_code"] == "CUSTOM-001"

        # Verify response contains document_id
        assert result["document_id"] == 42
        assert result["version_id"] == 421


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
            task.id, "preview_ocr", task=task,
        )

        # Verify step was marked as failed
        failed_step = await repo.get_task_steps(task.id)
        assert failed_step[0].status == "failed"
        assert failed_step[0].error_code == "OCR_ERROR"
