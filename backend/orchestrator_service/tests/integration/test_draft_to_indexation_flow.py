"""
Integration test: полный цикл draft → approve → full pipeline → document → indexation.

Сценарии:
  A. Draft → Document (approve + full pipeline completion)
     - approve_draft создаёт документ в Registry
     - on_step_completed для full_ocr → full_converter → registry_creation → rag_index
     - После rag_index: task COMPLETED, document status → "validating"
  
  B. Document → Indexation (background activation)
     - run_activate_document_step poll'ит RAG Builder
     - При indexed + integrity_ok → document status → "active"
     - При indexed + integrity_failed → возвращает integrity_failed
     - При failed → build_failed
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pipeline import TaskRepository
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.core.fsm import TaskStatus, TaskStage


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

async def _create_full_approve_setup(db_session: AsyncSession) -> dict:
    """
    Create a task + upload step so that approve_draft can succeed.
    Returns dict with task, repo, file_key.
    """
    repo = TaskRepository(db_session)
    task = await repo.create_task(
        draft_id=200, pipeline_type="formation", total_steps=7,
    )
    # Mark as preview completed — full phase is needed
    upload = await repo.create_task_step(
        task_id=task.id, step_name="upload", step_index=0,
        service_name="Orchestrator",
        input_data={"file_key": "drafts/200/test.pdf"},
    )
    await repo.complete_task_step(
        upload.id,
        output_data={"draft_id": 200, "task_id": task.id, "file_key": "drafts/200/test.pdf"},
    )
    await repo.create_task_step(
        task_id=task.id, step_name="preview_ocr", step_index=1,
        service_name="Parser Service",
    )
    await repo.create_task_step(
        task_id=task.id, step_name="preview_converter", step_index=2,
        service_name="Converter-validator",
    )
    return {"task": task, "repo": repo, "file_key": "drafts/200/test.pdf"}


def _make_registry_mock(
    document_id: int = 200,
    version_id: int = 1,
) -> AsyncMock:
    """Create a RegistryServiceClient mock for approve_draft."""
    mock = AsyncMock()
    mock.get_draft = AsyncMock(return_value={
        "data": {"title_key": "Test Doc", "document_key": "TEST-200"},
    })
    mock.get_draft_preview = AsyncMock(return_value={"data": {}})
    mock.create_document = AsyncMock(return_value={
        "data": {
            "document_id": document_id,
            "version_id": version_id,
            "is_new_document": True,
        }
    })
    mock.update_draft_status = AsyncMock()
    mock.create_draft_snapshot = AsyncMock()
    mock.update_document_status = AsyncMock()
    mock.get_document_sections = AsyncMock(return_value={
        "data": {"sections": []},
    })
    mock.create_document = AsyncMock(return_value={
        "data": {
            "document_id": document_id,
            "version_id": version_id,
            "is_new_document": True,
        }
    })
    mock.close = AsyncMock()
    return mock


# ===================================================================
#  A. Draft → Document (full pipeline completion)
# ===================================================================

@pytest.mark.asyncio
class TestFullPipelineCompletion:
    """
    Полный цикл: approve_draft → full_ocr → full_converter → 
    registry_creation → rag_index → task COMPLETED.
    """

    async def test_full_pipeline_ends_with_task_completed(
        self, db_session: AsyncSession,
    ):
        """После rag_index task переходит в COMPLETED, document → validating."""
        setup = await _create_full_approve_setup(db_session)
        task = setup["task"]
        repo = setup["repo"]
        registry_mock = _make_registry_mock(document_id=200, version_id=1)

        orchestrator = PipelineOrchestrator(db_session)

        # Step 1: approve_draft (Registry creates document)
        # Use MagicMock for .delay() so we can assert calls
        parser_delay = MagicMock()
        converter_delay = MagicMock()
        registry_delay = MagicMock()
        rag_delay = MagicMock()
        activate_delay = MagicMock()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=registry_mock,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
            parser_delay,
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
            converter_delay,
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
            registry_delay,
        ), patch(
            "app.tasks.pipeline_indexation.run_rag_index_step.delay",
            rag_delay,
        ), patch(
            "app.tasks.pipeline_indexation.run_activate_document_step.delay",
            activate_delay,
        ):
            result = await orchestrator.approve_draft(
                draft_id=200, task_id=task.id,
            )
        # approve_draft больше не создаёт документ — он появится после full_converter
        assert result["document_id"] is None
        assert result["version_id"] is None

        # Verify Celery dispatch: approve triggers full_ocr (parser), not converter/registry/rag
        file_key = setup["file_key"]
        parser_delay.assert_called_once_with(
            task.id, 200, file_key, trace_id="",
        )
        converter_delay.assert_not_called()
        registry_delay.assert_not_called()
        rag_delay.assert_not_called()

        # Verify task is in full stage
        updated = await repo.get_task(task.id)
        assert updated.pipeline_stage == TaskStage.FULL.value
        assert updated.document_id is None

        # Step 2: complete full_ocr step
        # approve_draft создаёт full_ocr как pending — стартуем его
        steps = await repo.get_task_steps(task.id)
        full_ocr = next(s for s in steps if s.step_name == "full_ocr")
        if full_ocr.status == "pending":
            await repo.start_task_step(full_ocr.id)
        # Не делаем manual complete_task_step — on_step_completed сам завершит running шаг

        # on_step_completed → dispatch full_converter
        converter_delay_2 = MagicMock()
        with patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
            converter_delay_2,
        ):
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="full_ocr",
                output_data={"full_result": {"text": "parsed content"}},
            )
        # Verify converter was dispatched after full_ocr completes
        # Note: _drain_queue может повторно диспатчить конвертер, поэтому assert_called, не once
        converter_delay_2.assert_called()
        call_args = converter_delay_2.call_args_list[0]
        assert call_args[0][0] == task.id  # task_id
        assert call_args[0][1] == 200  # draft_id

        # Step 3: complete full_converter step
        steps = await repo.get_task_steps(task.id)
        full_converter = next(
            (s for s in steps if s.step_name == "full_converter"),
            None,
        )
        assert full_converter is not None
        if full_converter.status == "pending":
            await repo.start_task_step(full_converter.id)

        registry_delay_2 = MagicMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=registry_mock,
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
            registry_delay_2,
        ):
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="full_converter",
                output_data={
                    "document": {"content": [{"id": 1, "text": "section1"}]},
                    "metadata": {"title": "Test"},
                },
            )
        # Verify registry step was dispatched after full_converter completes
        registry_delay_2.assert_called_once()

        # full_converter создаёт документ в Registry и устанавливает task.document_id
        updated_after_converter = await repo.get_task(task.id)
        assert updated_after_converter.document_id == 200

        # Step 4: complete registry_creation step
        steps = await repo.get_task_steps(task.id)
        registry_step = next(
            (s for s in steps if s.step_name == "registry_creation"),
            None,
        )
        assert registry_step is not None
        if registry_step.status == "pending":
            await repo.start_task_step(registry_step.id)

        rag_delay_2 = MagicMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=registry_mock,
        ), patch(
            "app.tasks.pipeline_indexation.run_rag_index_step.delay",
            rag_delay_2,
        ):
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="registry_creation",
                output_data={
                    "document_id": 200,
                    "sections": [{"id": 1, "section_id": 1, "text": "section1"}],
                },
            )
        # Verify RAG index was dispatched after registry completes
        rag_delay_2.assert_called_once()

        # Step 5: complete rag_index step
        steps = await repo.get_task_steps(task.id)
        rag_step = next(
            (s for s in steps if s.step_name == "rag_index"),
            None,
        )
        assert rag_step is not None
        if rag_step.status == "pending":
            await repo.start_task_step(rag_step.id)

        # При rag_index → on_step_completed:
        #   - task → COMPLETED
        #   - document status → "validating"
        #   - dispatch run_activate_document_step
        activate_delay_2 = MagicMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=registry_mock,
        ), patch(
            "app.tasks.pipeline_indexation.run_activate_document_step.delay",
            activate_delay_2,
        ):
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="rag_index",
                output_data={},
            )
        # Verify background activation was dispatched after rag_index completes
        activate_delay_2.assert_called_once()

        # Verify task is COMPLETED
        final_task = await repo.get_task(task.id)
        assert final_task is not None
        assert final_task.status == TaskStatus.COMPLETED.value
        assert final_task.progress_percent == 100

        # Verify document status was updated to "validating"
        registry_mock.update_document_status.assert_awaited_with(
            document_id=200,
            status="validating",
        )

    async def test_full_pipeline_skips_full_ocr_when_full_completed(
        self, db_session: AsyncSession,
    ):
        """Когда full_completed=True (полный preview), full_ocr не создаётся."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=201, pipeline_type="formation", total_steps=7,
        )
        task.full_completed = True  # preview already has full data
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
            input_data={"file_key": "drafts/201/test.pdf"},
        )
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 201, "task_id": task.id, "file_key": "drafts/201/test.pdf"},
        )

        registry_mock = _make_registry_mock(document_id=201, version_id=2)
        orchestrator = PipelineOrchestrator(db_session)

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=registry_mock,
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ), patch(
            "app.tasks.pipeline_indexation.run_rag_index_step.delay",
        ), patch(
            "app.tasks.pipeline_indexation.run_activate_document_step.delay",
        ):
            result = await orchestrator.approve_draft(
                draft_id=201, task_id=task.id,
            )
        # approve_draft больше не создаёт документ
        assert result["document_id"] is None

        steps = await repo.get_task_steps(task.id)
        step_names = {s.step_name for s in steps}
        assert "full_ocr" not in step_names, \
            "full_ocr должен быть пропущен при full_completed=True"


# ===================================================================
#  B. Document → Indexation (background activation)
# ===================================================================


class TestDocumentActivation:
    """
    run_activate_document_step: background задача активации документа.
    
    Тесты синхронные, так как Celery-задача использует _run_async
    (синхронная обёртка над async-вызовами).
    """

    def test_activation_success(self):
        """
        RAG Build indexed + integrity_ok = True
        → document status → "active"
        """
        from app.tasks.pipeline_indexation import run_activate_document_step

        mock_rag = AsyncMock()
        mock_rag.get_build_status = AsyncMock(
            return_value={"status": "indexed"}
        )
        mock_rag.check_index = AsyncMock(
            return_value={"integrity_ok": True}
        )
        mock_rag.close = AsyncMock()

        mock_registry = AsyncMock()
        mock_registry.update_document_status = AsyncMock()
        mock_registry.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ):
            # run() — прямой вызов логики задачи (не через delay)
            result = run_activate_document_step.run(job_id="test", document_id=100)

        assert result is not None
        assert result.get("status") == "active"
        assert result.get("document_id") == 100
        mock_registry.update_document_status.assert_awaited_once_with(
            document_id=100,
            status="active",
        )

    def test_activation_integrity_failed(self):
        """
        RAG Build indexed + integrity_ok = False
        → возвращает integrity_failed, registry не вызывается.
        """
        from app.tasks.pipeline_indexation import run_activate_document_step

        mock_rag = AsyncMock()
        mock_rag.get_build_status = AsyncMock(
            return_value={"status": "indexed"}
        )
        mock_rag.check_index = AsyncMock(
            return_value={"integrity_ok": False}
        )
        mock_rag.close = AsyncMock()

        mock_registry = AsyncMock()
        mock_registry.update_document_status = AsyncMock()
        mock_registry.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ):
            result = run_activate_document_step.run(job_id="test", document_id=101)

        assert result is not None
        assert result.get("status") == "integrity_failed"
        # Registry не вызывается при integrity_failed
        mock_registry.update_document_status.assert_not_called()

    def test_activation_build_failed(self):
        """
        RAG Build вернул status=failed
        → возвращает build_failed, registry не вызывается.
        """
        from app.tasks.pipeline_indexation import run_activate_document_step

        mock_rag = AsyncMock()
        mock_rag.get_build_status = AsyncMock(
            return_value={"status": "failed"}
        )
        mock_rag.close = AsyncMock()

        mock_registry = AsyncMock()
        mock_registry.update_document_status = AsyncMock()
        mock_registry.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ):
            result = run_activate_document_step.run(job_id="test", document_id=102)

        assert result is not None
        assert result.get("status") == "build_failed"
        mock_registry.update_document_status.assert_not_called()

    def test_activation_still_indexing_defers_to_poller(self):
        """
        RAG Build всё ещё в процессе (pending) → defer to Poller via external_tasks.
        """
        from app.tasks.pipeline_indexation import run_activate_document_step

        mock_rag = AsyncMock()
        mock_rag.get_build_status = AsyncMock(
            return_value={"status": "pending"}
        )
        mock_rag.close = AsyncMock()

        mock_ext_repo = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation.ExternalTaskRepository",
            return_value=mock_ext_repo,
        ), patch(
            "app.tasks.pipeline_indexation.get_db_context",
        ):
            # job_id должен быть валидным целым числом (str) для int(job_id) в _save_external
            result = run_activate_document_step.run(job_id="12345", document_id=103)

        # No self.retry() call anymore — we defer to Poller
        assert result == {"status": "pending", "document_id": 103}
        mock_ext_repo.create.assert_awaited_once()
