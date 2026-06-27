"""
Integration tests for Parser-first strategy with OCR fallback.

Tests:
  - Parser-first: Parser is always tried first when enabled
  - Parser disabled → OCR used directly
  - Both disabled → error
  - Parser fails → OCR fallback
  - Parser returns preview_not_supported → OCR fallback
  - OCR fallback disabled → normal retry/compensation
"""

import pytest
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.repositories.pipeline import TaskRepository

pytestmark = pytest.mark.asyncio


# ============================================================================
#  Parser-first selection in start_pipeline
# ============================================================================


class TestParserFirstSelection:
    """Verify which service is selected when start_pipeline is called."""

    async def _create_task(self, db_session: AsyncSession, draft_id: int = 600):
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=draft_id, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()
        return task, repo

    async def test_parser_first_both_enabled(self, db_session: AsyncSession):
        """When both Parser and OCR are enabled, Parser is tried first."""
        task, repo = await self._create_task(db_session, draft_id=600)

        with patch(
            "app.tasks.pipeline_formation.run_parser_preview_step.delay",
        ) as mock_parser_delay, patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ) as mock_ocr_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.start_pipeline(
                draft_id=600,
                task_id=task.id,
                file_key="drafts/600/file.pdf",
                mime_type="application/pdf",
            )

        # Parser should be called, OCR should NOT
        mock_parser_delay.assert_called_once()
        mock_ocr_delay.assert_not_called()

        # Verify step has Parser service name
        steps = await repo.get_task_steps(task.id)
        preview = next(s for s in steps if s.step_name == "preview_ocr")
        assert preview.service_name == "Parser Service"

    async def test_parser_first_image(self, db_session: AsyncSession):
        """Even for image mime type, Parser is tried first when enabled."""
        task, repo = await self._create_task(db_session, draft_id=601)

        with patch(
            "app.tasks.pipeline_formation.run_parser_preview_step.delay",
        ) as mock_parser_delay, patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ) as mock_ocr_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.start_pipeline(
                draft_id=601,
                task_id=task.id,
                file_key="drafts/601/file.png",
                mime_type="image/png",
            )

        # Parser should be called first even for images
        mock_parser_delay.assert_called_once()
        mock_ocr_delay.assert_not_called()

    async def test_parser_disabled_uses_ocr(self, db_session: AsyncSession):
        """When Parser is disabled, OCR is used directly."""
        task, repo = await self._create_task(db_session, draft_id=602)

        with patch(
            "app.core.pipeline.orchestrator.settings.services.PARSER_ENABLED",
            False,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_preview_step.delay",
        ) as mock_parser_delay, patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ) as mock_ocr_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.start_pipeline(
                draft_id=602,
                task_id=task.id,
                file_key="drafts/602/file.pdf",
                mime_type="application/pdf",
            )

        # OCR should be used, Parser should NOT
        mock_parser_delay.assert_not_called()
        mock_ocr_delay.assert_called_once()

        steps = await repo.get_task_steps(task.id)
        preview = next(s for s in steps if s.step_name == "preview_ocr")
        assert preview.service_name == "OCR Service"

    async def test_ocr_disabled_uses_parser(self, db_session: AsyncSession):
        """When OCR is disabled, Parser is used (no fallback possible)."""
        task, repo = await self._create_task(db_session, draft_id=603)

        with patch(
            "app.core.pipeline.orchestrator.settings.services.OCR_ENABLED",
            False,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_preview_step.delay",
        ) as mock_parser_delay, patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ) as mock_ocr_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.start_pipeline(
                draft_id=603,
                task_id=task.id,
                file_key="drafts/603/file.pdf",
                mime_type="application/pdf",
            )

        # Parser should be used (OCR disabled but parser is still the first choice)
        mock_parser_delay.assert_called_once()
        mock_ocr_delay.assert_not_called()

    async def test_both_disabled_raises_error(self, db_session: AsyncSession):
        """When both Parser and OCR are disabled, start_pipeline raises ValueError."""
        task, repo = await self._create_task(db_session, draft_id=604)

        with patch(
            "app.core.pipeline.orchestrator.settings.services.PARSER_ENABLED",
            False,
        ), patch(
            "app.core.pipeline.orchestrator.settings.services.OCR_ENABLED",
            False,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            with pytest.raises(ValueError, match="both Parser and OCR are disabled"):
                await orchestrator.start_pipeline(
                    draft_id=604,
                    task_id=task.id,
                    file_key="drafts/604/file.pdf",
                    mime_type="application/pdf",
                )


# ============================================================================
#  Parser → OCR fallback on failure
# ============================================================================


class TestParserFallbackOnFailure:
    """Verify fallback from Parser to OCR when Parser fails."""

    async def test_parser_fallback_on_step_failed(self, db_session: AsyncSession):
        """When Parser preview fails, OCR fallback is enqueued."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=610, pipeline_type="formation", total_steps=3,
        )
        # Simulate: task started with Parser Service
        task.current_step_name = "Parser Service"
        await db_session.flush()

        # Create parser step and mark it as running
        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "drafts/610/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 610},
        )
        await repo.start_task_step(parser_step.id)
        await db_session.commit()

        with patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ) as mock_ocr_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_failed(
                task_id=task.id,
                step_name="preview_ocr",
                error_code="PARSER_ERROR",
                error_message="Parser service unavailable",
            )

        # OCR fallback should be enqueued
        mock_ocr_delay.assert_called_once()

        # Verify new step for OCR was created
        steps = await repo.get_task_steps(task.id)
        ocr_steps = [s for s in steps if s.service_name == "OCR Service" and s.step_name == "preview_ocr"]
        assert len(ocr_steps) == 1
        assert ocr_steps[0].status == "pending"

        # Verify retry count was reset
        updated_task = await repo.get_task(task.id)
        assert updated_task.retry_count == 0

    async def test_parser_fallback_full_phase(self, db_session: AsyncSession):
        """When Parser full step fails, OCR fallback is enqueued for full phase."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=611, pipeline_type="formation", total_steps=5,
        )
        task.current_step_name = "Parser Service"
        await db_session.flush()

        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="full_ocr",
            step_index=3,
            service_name="Parser Service",
            input_data={"file_key": "drafts/611/file.pdf", "mode": "full", "draft_id": 611},
        )
        await repo.start_task_step(parser_step.id)
        await db_session.commit()

        with patch(
            "app.tasks.pipeline_formation.run_ocr_full_step.delay",
        ) as mock_ocr_delay:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_failed(
                task_id=task.id,
                step_name="full_ocr",
                error_code="PARSER_ERROR",
                error_message="Parser full failed",
            )

        mock_ocr_delay.assert_called_once()

    async def test_no_ocr_fallback_when_disabled(self, db_session: AsyncSession):
        """When OCR is disabled, Parser failure does NOT fall back to OCR."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=612, pipeline_type="formation", total_steps=3,
        )
        task.current_step_name = "Parser Service"
        await db_session.flush()

        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "drafts/612/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 612},
        )
        await repo.start_task_step(parser_step.id)
        await db_session.commit()

        with patch(
            "app.core.pipeline.orchestrator.settings.services.OCR_ENABLED",
            False,
        ), patch(
            "app.core.pipeline.orchestrator.settings.services.PARSER_FALLBACK_TO_OCR",
            True,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_failed(
                task_id=task.id,
                step_name="preview_ocr",
                error_code="PARSER_ERROR",
                error_message="Parser failed",
            )

        # Verify that Parser step was re-created (normal retry), not OCR
        steps = await repo.get_task_steps(task.id)
        latest_preview_steps = [
            s for s in steps
            if s.step_name == "preview_ocr" and s.status == "pending"
        ]
        # Should have a retry step for Parser, not OCR
        assert len(latest_preview_steps) >= 1
        for step in latest_preview_steps:
            assert step.service_name == "Parser Service"

    async def test_no_fallback_when_flag_false(self, db_session: AsyncSession):
        """When PARSER_FALLBACK_TO_OCR is False, Parser failure does not fall back."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=613, pipeline_type="formation", total_steps=3,
        )
        task.current_step_name = "Parser Service"
        await db_session.flush()

        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "drafts/613/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 613},
        )
        await repo.start_task_step(parser_step.id)
        await db_session.commit()

        with patch(
            "app.core.pipeline.orchestrator.settings.services.PARSER_FALLBACK_TO_OCR",
            False,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_failed(
                task_id=task.id,
                step_name="preview_ocr",
                error_code="PARSER_ERROR",
                error_message="Parser failed",
            )

        # Verify Parser retry step was created, not OCR
        steps = await repo.get_task_steps(task.id)
        pending_steps = [
            s for s in steps
            if s.step_name == "preview_ocr" and s.status == "pending"
        ]
        assert len(pending_steps) >= 1
        for step in pending_steps:
            assert step.service_name == "Parser Service"


# ============================================================================
#  Parser → OCR fallback on preview_not_supported
# ============================================================================


class TestPreviewNotSupportedNoFallback:
    """preview_not_supported does NOT trigger OCR fallback (by design).

    preview_not_supported — технический флаг: Parser/OCR не умеет
    постраничный preview, вернул полный документ. Это не показатель
    качества. OCR fallback — только по результату Converter (validated).
    """

    async def test_preview_not_supported_sets_full_completed(
        self, db_session: AsyncSession,
    ):
        """Parser preview_not_supported → full_completed=True, no OCR fallback."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=620, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "drafts/620/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 620},
        )
        parser_step.status = "completed"
        parser_step.output_data = {
            "preview_not_supported": True,
            "pages_processed": 0,
            "metadata": {},
            "quality": {"score": 0, "notifications": []},
        }
        await db_session.flush()

        with patch(
            "app.core.pipeline.orchestrator.PipelineOrchestrator._run_ocr_fallback",
        ) as mock_fallback, patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_registry:
            mock_registry_instance = AsyncMock()
            mock_registry.return_value = mock_registry_instance

            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(task, [parser_step], None)

            # No OCR fallback from preview_not_supported
            mock_fallback.assert_not_called()
            # full_completed is set
            assert task.full_completed is True

    async def test_preview_not_supported_ocr_step_sets_full_completed(
        self, db_session: AsyncSession,
    ):
        """OCR preview_not_supported → full_completed=True (no double fallback)."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=622, pipeline_type="formation", total_steps=3,
        )
        task.document_id = None
        await db_session.flush()

        ocr_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="OCR Service",
            input_data={"file_key": "drafts/622/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 622},
        )
        ocr_step.status = "completed"
        ocr_step.output_data = {
            "preview_not_supported": True,
            "pages_processed": 20,
            "metadata": {"doc_code": "GOST", "title": "Doc"},
            "quality": {"score": 0.9, "notifications": [],},
        }
        await db_session.flush()

        with patch(
            "app.core.pipeline.orchestrator.PipelineOrchestrator._run_ocr_fallback",
        ) as mock_fallback, patch(
            "app.core.pipeline.orchestrator.PipelineOrchestrator.approve_draft",
        ) as mock_approve, patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_registry:
            mock_registry_instance = AsyncMock()
            mock_registry.return_value = mock_registry_instance
            mock_registry_instance.update_draft_status = AsyncMock()
            mock_registry_instance.update_draft_metadata = AsyncMock()
            mock_registry_instance.close = AsyncMock()

            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(task, [ocr_step], None)

            mock_fallback.assert_not_called()
            assert task.full_completed is True


class TestConverterResultTriggersFallback:
    """OCR fallback triggered by Converter result (not preview_not_supported).

    Flow: Parser → Converter → если Converter.validated=False → OCR fallback
    """

    async def test_converter_validated_false_triggers_ocr_fallback(
        self, db_session: AsyncSession,
    ):
        """Converter validated=False after Parser → OCR fallback enqueued."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=630, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        # Parser step — completed (content extracted, but converter may reject)
        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "drafts/630/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 630},
        )
        parser_step.status = "completed"
        parser_step.output_data = {
            "preview_not_supported": False,
            "pages_processed": 3,
            "metadata": {"doc_code": "GOST", "title": "Test"},
            "quality": {"score": 0.5, "notifications": []},
        }
        await db_session.flush()

        # Converter step — validated=False (low quality, needs OCR fallback)
        conv_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_converter",
            step_index=2,
            service_name="Converter-validator",
        )
        conv_step.status = "completed"
        conv_step.output_data = {
            "validated": False,
            "metadata": {},
        }
        await db_session.flush()

        with patch(
            "app.core.pipeline.orchestrator.PipelineOrchestrator._run_ocr_fallback",
        ) as mock_fallback:
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(
                task, [parser_step, conv_step], None,
            )

            # OCR fallback should be triggered
            mock_fallback.assert_called_once()
            # full_completed should NOT be set (still waiting for OCR)
            assert task.full_completed is False

    async def test_converter_validated_false_no_fallback_when_ocr_disabled(
        self, db_session: AsyncSession,
    ):
        """Converter validated=False but OCR disabled → review_required, not fallback."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=631, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "drafts/631/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 631},
        )
        parser_step.status = "completed"
        parser_step.output_data = {
            "preview_not_supported": False,
            "pages_processed": 3,
            "metadata": {},
            "quality": {"score": 0.4, "notifications": []},
        }
        await db_session.flush()

        conv_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_converter",
            step_index=2,
            service_name="Converter-validator",
        )
        conv_step.status = "completed"
        conv_step.output_data = {"validated": False}
        await db_session.flush()

        with patch(
            "app.core.pipeline.orchestrator.settings.services.OCR_ENABLED",
            False,
        ), patch(
            "app.core.pipeline.orchestrator.PipelineOrchestrator._run_ocr_fallback",
        ) as mock_fallback, patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_registry:
            mock_registry_instance = AsyncMock()
            mock_registry.return_value = mock_registry_instance

            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(
                task, [parser_step, conv_step], None,
            )

            # No fallback when OCR disabled
            mock_fallback.assert_not_called()
            # Should set review_required (the fallback path for validated=False)
            mock_registry_instance.update_draft_status.assert_called_with(
                draft_id=631, status="review_required",
            )

    async def test_converter_validated_false_no_fallback_when_flag_false(
        self, db_session: AsyncSession,
    ):
        """Converter validated=False but PARSER_FALLBACK_TO_OCR=False → review_required."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=632, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "drafts/632/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 632},
        )
        parser_step.status = "completed"
        parser_step.output_data = {
            "preview_not_supported": False,
            "pages_processed": 3,
            "metadata": {},
            "quality": {"score": 0.4, "notifications": []},
        }
        await db_session.flush()

        conv_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_converter",
            step_index=2,
            service_name="Converter-validator",
        )
        conv_step.status = "completed"
        conv_step.output_data = {"validated": False}
        await db_session.flush()

        with patch(
            "app.core.pipeline.orchestrator.settings.services.PARSER_FALLBACK_TO_OCR",
            False,
        ), patch(
            "app.core.pipeline.orchestrator.PipelineOrchestrator._run_ocr_fallback",
        ) as mock_fallback, patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_registry:
            mock_registry_instance = AsyncMock()
            mock_registry.return_value = mock_registry_instance

            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(
                task, [parser_step, conv_step], None,
            )

            mock_fallback.assert_not_called()
            mock_registry_instance.update_draft_status.assert_called_with(
                draft_id=632, status="review_required",
            )

    async def test_converter_validated_true_no_fallback(
        self, db_session: AsyncSession,
    ):
        """Converter validated=True after Parser → no fallback, normal flow."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=633, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        parser_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "drafts/633/file.pdf", "mode": "preview", "max_pages": 3, "draft_id": 633},
        )
        parser_step.status = "completed"
        parser_step.output_data = {
            "preview_not_supported": False,
            "pages_processed": 3,
            "metadata": {"doc_code": "GOST", "title": "Good"},
            "quality": {"score": 0.95, "notifications": []},
        }
        await db_session.flush()

        conv_step = await repo.create_task_step(
            task_id=task.id,
            step_name="preview_converter",
            step_index=2,
            service_name="Converter-validator",
        )
        conv_step.status = "completed"
        conv_step.output_data = {
            "validated": True,
            "metadata": {"doc_code": "GOST", "title": "Good"},
        }
        await db_session.flush()

        with patch(
            "app.core.pipeline.orchestrator.PipelineOrchestrator._run_ocr_fallback",
        ) as mock_fallback, patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_registry:
            mock_registry_instance = AsyncMock()
            mock_registry.return_value = mock_registry_instance
            mock_registry_instance.update_draft_status = AsyncMock()
            mock_registry_instance.update_draft_metadata = AsyncMock()
            mock_registry_instance.close = AsyncMock()

            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(
                task, [parser_step, conv_step], None,
            )

            # No fallback — converter validated successfully
            mock_fallback.assert_not_called()


# ============================================================================
#  Full phase: Parser-first in approve_draft
# ============================================================================


class TestParserFirstFullPhase:
    """Verify Parser-first is applied in full phase (approve_draft)."""

    async def test_full_phase_uses_parser_first(self, db_session: AsyncSession):
        """Full phase uses Parser Service when Parser is enabled."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=630, pipeline_type="formation", total_steps=5,
        )
        task.full_completed = False
        task.document_id = 630
        task.version_id = 1
        await db_session.flush()

        # Create upload step with file_key
        upload_step = await repo.create_task_step(
            task_id=task.id,
            step_name="upload",
            step_index=0,
            service_name="Orchestrator",
        )
        upload_step.status = "completed"
        upload_step.output_data = {"file_key": "drafts/630/file.pdf", "draft_id": 630, "task_id": task.id}
        await db_session.flush()
        await db_session.commit()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_registry, patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
        ) as mock_parser_full, patch(
            "app.tasks.pipeline_formation.run_ocr_full_step.delay",
        ) as mock_ocr_full:
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_draft.return_value = {"data": {}}
            mock_registry_instance.get_draft_preview.return_value = {"data": {}}
            mock_registry_instance.create_document.return_value = {
                "data": {"document_id": 630, "version_id": 1, "is_new_document": True},
            }
            mock_registry.return_value = mock_registry_instance

            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.approve_draft(draft_id=630, task_id=task.id)

        # Parser full should be called, OCR full should NOT
        mock_parser_full.assert_called_once()
        mock_ocr_full.assert_not_called()

    async def test_full_phase_ocr_when_parser_disabled(self, db_session: AsyncSession):
        """Full phase uses OCR when Parser is disabled."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=631, pipeline_type="formation", total_steps=5,
        )
        task.full_completed = False
        task.document_id = 631
        task.version_id = 1
        await db_session.flush()

        upload_step = await repo.create_task_step(
            task_id=task.id,
            step_name="upload",
            step_index=0,
            service_name="Orchestrator",
        )
        upload_step.status = "completed"
        upload_step.output_data = {"file_key": "drafts/631/file.pdf", "draft_id": 631, "task_id": task.id}
        await db_session.flush()
        await db_session.commit()

        with patch(
            "app.core.pipeline.orchestrator.settings.services.PARSER_ENABLED",
            False,
        ), patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_registry, patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
        ) as mock_parser_full, patch(
            "app.tasks.pipeline_formation.run_ocr_full_step.delay",
        ) as mock_ocr_full:
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_draft.return_value = {"data": {}}
            mock_registry_instance.get_draft_preview.return_value = {"data": {}}
            mock_registry_instance.create_document.return_value = {
                "data": {"document_id": 631, "version_id": 1, "is_new_document": True},
            }
            mock_registry.return_value = mock_registry_instance

            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.approve_draft(draft_id=631, task_id=task.id)

        # OCR full should be used, Parser full should NOT
        mock_parser_full.assert_not_called()
        mock_ocr_full.assert_called_once()
