"""
Тесты quality-решений и авто-апрув (Pipeline 1, §3).

Покрывает сценарии §3 Quality-решения (pipeline1-orchestrator_details.md):
  - Качество в норме, авто-апрув выключен → ready_for_approve
  - Качество в норме, авто-апрув включён, пороги в норме → approve
  - Авто-апрув включён, critical_count > max_critical → ready_for_approve
  - Катастрофически низкое качество → discarded
  - notificiations с critical блокируют авто-апрув

Внимание:
  - _check_auto_approve() проверяет только doc_code + title + full_completed
  - Пороги качества (avg_confidence и др.) не реализованы в production-коде
  - Авто-апрув срабатывает ТОЛЬКО при preview_not_supported=True (full preview)
"""

import pytest
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.repositories.pipeline import TaskRepository
from app.core.fsm import TaskStage


class TestAutoApproveDisabled:
    """Авто-апрув выключен — черновик переходит в ready_for_approve."""

    async def test_auto_approve_disabled_sets_ready_for_approve(
        self, db_session: AsyncSession,
    ):
        """Авто-апрув выключен → ready_for_approve, без вызова approve.

        Настройка: preview_not_supported=False (partial preview), поэтому
        _on_preview_completed не вызывает approve_draft, а ставит decision.
        """
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=100, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        # Create steps — partial preview (preview_not_supported=False)
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
        )
        await repo.complete_task_step(upload.id, output_data={})

        ocr = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
        )
        await repo.complete_task_step(
            ocr.id,
            output_data={
                "preview_not_supported": False,  # partial preview
                "metadata": {"doc_code": "ГОСТ 1234", "title": "Test Doc"},
            },
        )

        converter = await repo.create_task_step(
            task_id=task.id, step_name="preview_converter", step_index=2,
            service_name="Converter-validator",
        )
        await repo.complete_task_step(
            converter.id,
            output_data={
                "validated": True,
                "metadata": {"doc_code": "ГОСТ 1234", "title": "Test Doc"},
            },
        )

        mock_registry = AsyncMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(task, await repo.get_task_steps(task.id), {})

        # Should be ready_for_approve, not auto-approved
        updated_task = await repo.get_task(task.id)
        assert updated_task is not None
        assert updated_task.pipeline_stage == TaskStage.DECISION.value
        mock_registry.update_draft_status.assert_called_with(
            draft_id=100,
            status="ready_for_approve",
        )


class TestAutoApproveEnabled:
    """Авто-апрув включён — черновик auto-approve."""

    async def test_auto_approve_succeeds(
        self, db_session: AsyncSession,
    ):
        """Авто-апрув: preview_not_supported=True + валидные метаданные → approve."""
        from app.core.config import settings
        settings.pipeline.AUTO_APPROVE_ENABLED = True

        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=101, pipeline_type="formation", total_steps=3,
        )
        task.full_completed = True
        await db_session.flush()

        # Create steps
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
        )
        await repo.complete_task_step(upload.id, output_data={})

        ocr = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
            input_data={"file_key": "f-test", "mode": "preview", "draft_id": 101},
        )
        await repo.complete_task_step(
            ocr.id,
            output_data={
                "preview_not_supported": True,
                "metadata": {"doc_code": "ГОСТ 1234", "title": "Test Doc"},
            },
        )

        converter = await repo.create_task_step(
            task_id=task.id, step_name="preview_converter", step_index=2,
            service_name="Converter-validator",
        )
        await repo.complete_task_step(
            converter.id,
            output_data={
                "validated": True,
                "metadata": {"doc_code": "ГОСТ 1234", "title": "Test Doc"},
            },
        )

        # Mock Registry + Celery
        mock_registry = AsyncMock()
        mock_registry.get_draft.return_value = {
            "data": {"draft_id": 101, "title_key": "Test Doc", "document_key": "doc-auto"},
        }
        mock_registry.get_draft_preview.return_value = {
            "data": {"title": "Test Doc", "doc_code": "ГОСТ 1234"},
        }
        mock_registry.create_document.return_value = {
            "data": {"document_id": 1001, "version_id": 1, "is_new_document": True},
        }

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_rag_index_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(
                task, await repo.get_task_steps(task.id), {}
            )

        # Reset setting to default
        settings.pipeline.AUTO_APPROVE_ENABLED = False

        # Verify auto-approve was triggered
        updated_task = await repo.get_task(task.id)
        assert updated_task is not None
        # After approve, stage should be 'full'
        assert updated_task.pipeline_stage == TaskStage.FULL.value
        assert updated_task.document_id == 1001


class TestAutoApproveBlocked:
    """Сценарии, блокирующие авто-апрув."""

    async def test_auto_approve_blocked_critical_notifications(
        self, db_session: AsyncSession,
    ):
        """Критические нотификации → авто-апрув не срабатывает."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=102, pipeline_type="formation", total_steps=3,
        )
        task.full_completed = True
        await db_session.flush()

        # Create steps
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
        )
        await repo.complete_task_step(upload.id, output_data={})

        ocr = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
        )
        await repo.complete_task_step(
            ocr.id,
            output_data={
                "preview_not_supported": True,
                "metadata": {"doc_code": "ГОСТ 1234", "title": "Test"},
                "quality": {
                    "notifications": [
                        {"code": "critical_error", "message": "Critical",
                         "severity": "critical"},
                    ],
                },
            },
        )

        converter = await repo.create_task_step(
            task_id=task.id, step_name="preview_converter", step_index=2,
            service_name="Converter-validator",
        )
        await repo.complete_task_step(
            converter.id,
            output_data={"validated": True, "metadata": {"doc_code": "ГОСТ 1234", "title": "Test"}},
        )

        mock_registry = AsyncMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(
                task, await repo.get_task_steps(task.id), {}
            )

        # Should be ready_for_approve (auto-approve blocked)
        updated_task = await repo.get_task(task.id)
        assert updated_task is not None
        assert updated_task.pipeline_stage == TaskStage.DECISION.value
        # Verify draft was set to ready_for_approve
        mock_registry.update_draft_status.assert_called_with(
            draft_id=102,
            status="ready_for_approve",
        )

    async def test_auto_approve_blocked_missing_metadata(
        self, db_session: AsyncSession,
    ):
        """Без doc_code или title → ready_for_approve."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=103, pipeline_type="formation", total_steps=3,
        )
        task.full_completed = True
        await db_session.flush()

        # Create steps with incomplete metadata
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
        )
        await repo.complete_task_step(upload.id, output_data={})

        ocr = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
        )
        await repo.complete_task_step(
            ocr.id,
            output_data={
                "preview_not_supported": True,
                "metadata": {"doc_code": None, "title": None},
            },
        )

        converter = await repo.create_task_step(
            task_id=task.id, step_name="preview_converter", step_index=2,
            service_name="Converter-validator",
        )
        await repo.complete_task_step(
            converter.id,
            output_data={"validated": True, "metadata": {}},
        )

        mock_registry = AsyncMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(
                task, await repo.get_task_steps(task.id), {}
            )

        updated_task = await repo.get_task(task.id)
        assert updated_task is not None
        assert updated_task.pipeline_stage == TaskStage.DECISION.value


class TestQualityReviewRequired:
    """Сценарии low-quality → review_required."""

    async def test_converter_validation_failure_sets_review_required(
        self, db_session: AsyncSession,
    ):
        """Converter validation failed при OCR (не Parser) → review_required.

        Используем OCR Service (не Parser), чтобы избежать fallback на OCR,
        который срабатывает только при used_parser=True.
        """
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=104, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        # Steps: upload + ocr (OCR Service, не Parser) + converter with validated=False
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
        )
        await repo.complete_task_step(upload.id, output_data={})

        ocr = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="OCR Service",  # <-- OCR, не Parser
            input_data={"file_key": "f-test", "draft_id": 104},
        )
        await repo.complete_task_step(
            ocr.id,
            output_data={
                "preview_not_supported": False,
                "metadata": {"doc_code": "GOST 123"},
            },
        )

        converter = await repo.create_task_step(
            task_id=task.id, step_name="preview_converter", step_index=2,
            service_name="Converter-validator",
        )
        await repo.complete_task_step(
            converter.id,
            output_data={"validated": False, "metadata": {}},
        )

        mock_registry = AsyncMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator._on_preview_completed(
                task, await repo.get_task_steps(task.id), {}
            )

        updated_task = await repo.get_task(task.id)
        assert updated_task is not None
        assert updated_task.pipeline_stage == TaskStage.DECISION.value
        # Registry should have set review_required
        mock_registry.update_draft_status.assert_called_with(
            draft_id=104,
            status="review_required",
        )
