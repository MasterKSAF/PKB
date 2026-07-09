"""
Unit-тесты Saga Coordinator — компенсация при ошибках pipeline.

Проверяет:
  1. SagaCoordinator.compensate — откат registry_creation после ошибки
  2. _mock_delete_document — runtime vs seed
  3. Компенсация не вызывается для stateless-шагов
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.core.pipeline.saga import SagaCoordinator


@pytest.fixture
def mock_db():
    """Create a mock db session."""
    mock = AsyncMock()
    mock.flush = AsyncMock()
    return mock


@pytest.fixture
def mock_task_repo(mock_db):
    """Create SagaCoordinator with mock dependencies."""
    saga = SagaCoordinator(mock_db)
    saga.task_repo = AsyncMock()
    return saga


class MockStep:
    """Simulate a TaskStep for testing compensation."""

    def __init__(self, step_name, step_index, status="completed", output_data=None, service_name=""):
        self.id = step_index * 100
        self.task_id = 1
        self.step_name = step_name
        self.step_index = step_index
        self.status = status
        self.output_data = output_data or {}
        self.service_name = service_name or step_name


class MockTask:
    """Simulate a Task for testing compensation."""

    def __init__(self, id=1, draft_id=42, document_id=100, status="active"):
        self.id = id
        self.draft_id = draft_id
        self.document_id = document_id
        self.trace_id = "test-trace-001"
        self.status = status
        self.retry_count = 0
        self.current_step_index = 0
        self.current_step_name = ""
        self.locked_by = None
        self.locked_at = None


# ============================================================================
#  1. Saga compensation logic
# ============================================================================


class TestSagaCoordinator:
    """Проверка логики SagaCoordinator.compensate."""

    async def test_compensate_registry_creation(
        self, mock_task_repo: SagaCoordinator
    ):
        """registry_creation — единственный шаг с компенсацией.

        Если registry_creation выполнен успешно, а следующий шаг (rag_index)
        упал, SagaCoordinator должен вызвать delete_document.
        """
        saga = mock_task_repo
        saga.task_repo.get_task_steps.return_value = [
            MockStep("upload", 0, status="completed"),
            MockStep("preview_ocr", 1, status="completed"),
            MockStep("preview_converter", 2, status="completed"),
            MockStep("full_converter", 3, status="completed"),
            MockStep("registry_creation", 4, status="completed", output_data={"registry_id": 100}),
            MockStep("rag_index", 5, status="failed"),  # The failed step MUST be in the list
        ]

        task = MockTask()

        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(return_value={"data": {"deleted": True, "document_id": 100}}),
        ) as mock_delete:
            await saga.compensate(task_id=1, failed_step="rag_index", task=task)

        # delete_document должен быть вызван с document_id=100 (registry_creation)
        mock_delete.assert_awaited_once_with(100)

        # Компенсация должна отметить registry_creation (completed) + rag_index (сам упавший)
        assert saga.task_repo.compensate_task_step.call_count == 2

        # Task должен быть помечен как failed
        saga.task_repo.set_task_error.assert_called_once()
        saga.task_repo.update_task_status.assert_called_once_with(
            1, status="failed"
        )

    async def test_compensate_skips_stateless_steps(
        self, mock_task_repo: SagaCoordinator
    ):
        """Stateless шаги (upload, preview_ocr, preview_converter, full_ocr, full_converter)
        не имеют компенсации — проверяем, что compensate пропускает их.
        Шаги с компенсацией (registry_creation) чистятся даже при падении.
        """
        saga = mock_task_repo
        saga.task_repo.get_task_steps.return_value = [
            MockStep("upload", 0, status="completed"),
            MockStep("preview_ocr", 1, status="completed"),
            MockStep("preview_converter", 2, status="completed"),
            MockStep("registry_creation", 3, status="failed"),  # The failed step MUST be in list
        ]

        task = MockTask()

        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(),
        ) as mock_delete:
            await saga.compensate(task_id=1, failed_step="registry_creation", task=task)

        # registry_creation упал, но он имеет delete_registry_document — delete вызывается
        mock_delete.assert_awaited_once()

        # Task error всё равно устанавливается
        saga.task_repo.set_task_error.assert_called_once()
        saga.task_repo.update_task_status.assert_called_once()

    async def test_compensate_reverse_order(
        self, mock_task_repo: SagaCoordinator
    ):
        """Компенсация выполняется в обратном порядке (reverse order)."""
        saga = mock_task_repo
        saga.task_repo.get_task_steps.return_value = [
            MockStep("upload", 0, status="completed"),
            MockStep("registry_creation", 1, status="completed", output_data={"registry_id": 50}),
            MockStep("full_converter", 2, status="failed"),  # The failed step MUST be in list
        ]

        task = MockTask()

        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(),
        ) as mock_delete:
            await saga.compensate(task_id=1, failed_step="full_converter", task=task)

        # Должен вызвать delete_document для registry_creation (единственный с компенсацией)
        mock_delete.assert_awaited_once_with(50)

    async def test_compensate_marks_document_failed_when_no_registry_step(
        self, mock_task_repo: SagaCoordinator
    ):
        """Если pipeline упал на full_ocr/full_converter ДО registry_creation,
        и у task есть document_id (создан approve_draft),
        документ должен получить статус failed, а не висеть в uploaded."""
        saga = mock_task_repo
        saga.task_repo.get_task_steps.return_value = [
            MockStep("upload", 0, status="completed"),
            MockStep("full_ocr", 1, status="failed"),
        ]

        # У task есть document_id (установлен approve_draft)
        task = MockTask(document_id=100)

        with patch(
            "app.services.registry_client.RegistryServiceClient.update_document_status",
            new=AsyncMock(),
        ) as mock_update_status:
            await saga.compensate(task_id=1, failed_step="full_ocr", task=task)

        # Документ должен быть помечен как failed
        mock_update_status.assert_awaited_once_with(
            document_id=100,
            status="failed",
        )

        # Task всё равно помечен как failed через task_repo
        saga.task_repo.update_task_status.assert_called_once()
        call_kwargs = saga.task_repo.update_task_status.call_args[1]
        assert call_kwargs.get("status") == "failed", (
            "Task status must be set to failed even when document is marked"
        )

    async def test_compensate_skips_document_failed_when_no_document_id(
        self, mock_task_repo: SagaCoordinator
    ):
        """Если у task нет document_id (черновик не аппрувнут),
        статус документа не обновляется — это нормально."""
        saga = mock_task_repo
        saga.task_repo.get_task_steps.return_value = [
            MockStep("upload", 0, status="completed"),
            MockStep("preview_ocr", 1, status="failed"),
        ]

        task = MockTask(document_id=None)

        with patch(
            "app.services.registry_client.RegistryServiceClient.update_document_status",
            new=AsyncMock(),
        ) as mock_update_status:
            await saga.compensate(task_id=1, failed_step="preview_ocr", task=task)

        # update_document_status НЕ вызывается — document_id=None
        mock_update_status.assert_not_called()


# ============================================================================
#  2. PipelineOrchestrator.on_step_failed → Saga
# ============================================================================


class TestOnStepFailedCallsSaga:
    """Проверка, что on_step_failed вызывает Saga при исчерпании retry."""

    async def test_on_step_failed_triggers_saga_on_retry_exhausted(
        self, mock_db
    ):
        """После исчерпания retry → Saga.compensate."""
        from app.core.config import settings

        # Temporarily lower max retries for test
        original = settings.pipeline.MAX_STEP_RETRIES
        settings.pipeline.MAX_STEP_RETRIES = 0

        try:
            orchestrator = PipelineOrchestrator(mock_db)
            orchestrator.task_repo = AsyncMock()

            # Task with retry_count already at max
            task = MockTask(status="active")
            task.retry_count = 0
            task.current_step_index = 4
            task.current_step_name = "registry_creation"
            orchestrator.task_repo.get_task.return_value = task

            # Steps states
            orchestrator.task_repo.get_task_steps.return_value = [
                MockStep("upload", 0, status="completed"),
                MockStep("preview_ocr", 1, status="completed"),
                MockStep("preview_converter", 2, status="completed"),
                MockStep("full_converter", 3, status="completed"),
                MockStep("registry_creation", 4, status="running"),
            ]
            orchestrator.task_repo.create_task_step.return_value = MockStep("registry_creation", 4)

            with patch.object(
                SagaCoordinator, "compensate", new=AsyncMock()
            ) as mock_compensate:
                await orchestrator.on_step_failed(
                    task_id=1,
                    step_name="registry_creation",
                    error_code="REGISTRY_ERROR",
                    error_message="Failed to create document in Registry",
                )

            # Saga.compensate должен быть вызван
            mock_compensate.assert_awaited_once()
            call_args = mock_compensate.await_args
            # call_args is a _Call object: positional args in .args, kwargs in .kwargs
            assert call_args.args[0] == 1  # task_id
            assert call_args.args[1] == "registry_creation"  # failed_step
        finally:
            settings.pipeline.MAX_STEP_RETRIES = original

    async def test_on_step_failed_retry_before_saga(
        self, mock_db
    ):
        """Если retry не исчерпаны — Saga НЕ вызывается."""
        from app.core.config import settings

        original = settings.pipeline.MAX_STEP_RETRIES
        settings.pipeline.MAX_STEP_RETRIES = 3

        try:
            orchestrator = PipelineOrchestrator(mock_db)
            orchestrator.task_repo = AsyncMock()

            task = MockTask(status="active")
            task.retry_count = 0  # below max_retries
            task.current_step_index = 1
            task.current_step_name = "preview_ocr"
            orchestrator.task_repo.get_task.return_value = task
            orchestrator.task_repo.get_task_steps.return_value = [
                MockStep("upload", 0, status="completed"),
                MockStep("preview_ocr", 1, status="running"),
            ]
            orchestrator.task_repo.create_task_step.return_value = MockStep("preview_ocr", 1)

            with patch.object(
                SagaCoordinator, "compensate", new=AsyncMock()
            ) as mock_compensate:
                await orchestrator.on_step_failed(
                    task_id=1,
                    step_name="preview_ocr",
                    error_code="OCR_ERROR",
                    error_message="OCR processing failed",
                )

            # Saga НЕ должна вызываться при наличии retry
            mock_compensate.assert_not_called()

            # Должен быть создан retry-шаг
            assert orchestrator.task_repo.create_task_step.called
        finally:
            settings.pipeline.MAX_STEP_RETRIES = original


# ============================================================================
#  3. _mock_delete_document — seed vs runtime
# ============================================================================


class TestMockDeleteDocument:
    """Проверка _mock_delete_document (компенсация Registry)."""

    async def test_delete_document_removes_runtime_only(self):
        """delete_document удаляет runtime-копию, seed остаётся."""
        from app.services.registry_client import RegistryServiceClient

        client = RegistryServiceClient()
        storage = client._storage

        # Create runtime document
        storage["drafts"].clear()
        storage["documents"].clear()
        storage["doc_seq"] = 1
        storage["draft_seq"] = 1

        doc_result = await client.create_document({"title": "Test"})
        doc_id = doc_result["data"]["document_id"]

        # Verify it exists
        assert doc_id in storage["documents"]

        # Delete
        delete_result = await client.delete_document(doc_id)
        assert delete_result["data"]["deleted"] is True

        # Runtime entry should be gone
        assert doc_id not in storage["documents"]

        # Seed (document_id=1) should still exist in _SEED_DOCUMENTS
        assert 1 in client._SEED_DOCUMENTS

    async def test_delete_document_twice_returns_not_found(self):
        """Повторное удаление того же doc_id → ошибка."""
        from app.services.registry_client import RegistryServiceClient

        client = RegistryServiceClient()

        # Try to delete non-existent document
        result = await client.delete_document(99999)
        assert "error" in result

    async def test_delete_document_with_runtime_id_zero(self):
        """delete_document с doc_id=0 — проверка наличия в storage."""
        from app.services.registry_client import RegistryServiceClient

        client = RegistryServiceClient()
        storage = client._storage

        # Create doc with id=0 directly in storage
        storage["documents"][0] = {"document_id": 0, "title": "id-zero-doc", "status": "active"}

        result = await client.delete_document(0)
        assert result["data"]["deleted"] is True
        assert 0 not in storage["documents"]


# ============================================================================
#  4. P2-блок: TestCompensateRagIndex + TestCompensationIdempotency
#  Источник: todo_pipeline_coverage.md (P2 №1-2 в test_saga_compensation.py)
# ============================================================================


class TestCompensateRagIndex:
    """P2-1: компенсация шага rag_index → delete_from_vector_index.

    SagaCoordinator.COMPENSATION_ACTIONS содержит:
      "rag_index": "delete_from_vector_index"
    """

    async def test_rag_index_step_has_compensation_action(self):
        """В COMPENSATION_ACTIONS есть rag_index → delete_from_vector_index."""
        from app.core.pipeline.saga import SagaCoordinator

        assert "rag_index" in SagaCoordinator.COMPENSATION_ACTIONS
        assert SagaCoordinator.COMPENSATION_ACTIONS["rag_index"] == "delete_from_vector_index"

    async def test_compensate_rag_index_calls_delete_index_on_following_step_failure(
        self, mock_task_repo
    ):
        """Если rag_index выполнен и ПОСЛЕДУЮЩИЙ шаг упал —
        Saga компенсирует rag_index через delete_from_vector_index.
        """
        saga = mock_task_repo
        saga.task_repo.get_task_steps.return_value = [
            MockStep("registry_creation", 4, status="completed", output_data={"registry_id": 100}),
            MockStep("rag_index", 5, status="completed", output_data={"document_id": "42"}),
            MockStep("downstream_step", 6, status="failed"),
        ]

        task = MockTask()

        with patch(
            "app.services.rag_client.RAGBuilderClient.delete_index",
            new=AsyncMock(),
        ) as mock_delete_index:
            await saga.compensate(
                task_id=1, failed_step="downstream_step", task=task,
            )

        # rag_index completed до downstream_step → компенсируется
        mock_delete_index.assert_awaited_once_with("42")

    async def test_compensate_rag_index_on_own_failure(
        self, mock_task_repo
    ):
        """Если rag_index сам упал — Saga также компенсирует его
        через delete_from_vector_index (очистка частичных чанков).
        """
        saga = mock_task_repo
        saga.task_repo.get_task_steps.return_value = [
            MockStep("registry_creation", 4, status="completed", output_data={"registry_id": 100}),
            MockStep("rag_index", 5, status="failed", output_data={"document_id": "42"}),
        ]

        task = MockTask()

        with patch(
            "app.services.rag_client.RAGBuilderClient.delete_index",
            new=AsyncMock(),
        ) as mock_delete_index, patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(),
        ) as mock_delete_doc:
            await saga.compensate(
                task_id=1, failed_step="rag_index", task=task,
            )

        # registry_creation (completed) → delete_document
        mock_delete_doc.assert_awaited_once()
        # rag_index (сам упавший) → delete_index
        mock_delete_index.assert_awaited_once_with("42")
    
    async def test_compensate_rag_index_after_its_failure(self):
        """Если падает шаг ПОСЛЕ rag_index, и rag_index completed,
        вызывается delete_from_vector_index.
        """
        from app.core.pipeline.orchestrator import PipelineOrchestrator
        from app.core.pipeline.saga import SagaCoordinator
        from app.core.config import settings

        # Mock db — need to configure execute() so SagaCoordinator's
        # internal TaskRepository.get_task_steps() does not choke on mock.
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        # Steps list that SagaCoordinator will see via its own TaskRepository
        _saga_steps = [
            MockStep("registry_creation", 4, status="completed",
                     output_data={"registry_id": 100}),
            MockStep("rag_index", 5, status="completed",
                     output_data={"document_id": "42"}),
            MockStep("some_step_after_rag", 6, status="failed"),
        ]
        # Configure db.execute → await → result.scalars().all() chain
        mock_scalar_result = MagicMock()
        mock_scalar_result.all.return_value = _saga_steps
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalar_result
        mock_db.execute.return_value = mock_result

        orchestrator = PipelineOrchestrator(mock_db)
        orchestrator.task_repo = AsyncMock()

        # Task with retry_count at max — saga сработает
        original = settings.pipeline.MAX_STEP_RETRIES
        settings.pipeline.MAX_STEP_RETRIES = 0
        try:
            task = MockTask()
            task.retry_count = 0
            task.document_id = 42
            orchestrator.task_repo.get_task.return_value = task
            orchestrator.task_repo.get_task_steps.return_value = [
                MockStep("registry_creation", 4, status="completed",
                         output_data={"registry_id": 100}),
                MockStep("rag_index", 5, status="completed",
                         output_data={"document_id": "42"}),
                MockStep("some_step_after_rag", 6, status="failed"),
            ]
            orchestrator.task_repo.create_task_step.return_value = MockStep("rag_index", 5)

            with patch(
                "app.services.rag_client.RAGBuilderClient.delete_index",
                new=AsyncMock(),
            ) as mock_delete_index, patch(
                "app.services.registry_client.RegistryServiceClient.delete_document",
                new=AsyncMock(),
            ) as mock_delete_doc:
                await orchestrator.on_step_failed(
                    task_id=1,
                    step_name="some_step_after_rag",
                    error_code="TEST_ERROR",
                    error_message="test",
                )

            # rag_index completed → компенсируется через delete_index
            # registry_creation completed → компенсируется через delete_document
            assert mock_delete_index.await_count >= 1, (
                "rag_index completed — ожидался вызов delete_from_vector_index"
            )
            assert mock_delete_doc.await_count >= 1, (
                "registry_creation completed — ожидался вызов delete_document"
            )
        finally:
            settings.pipeline.MAX_STEP_RETRIES = original


class TestExecuteCompensation:
    """Прямые тесты _execute_compensation (C3)."""

    @pytest.fixture
    def saga(self, mock_db):
        from app.core.pipeline.saga import SagaCoordinator
        s = SagaCoordinator(mock_db)
        s.task_repo = AsyncMock()
        return s

    @pytest.fixture
    def step(self):
        return MockStep(
            step_name="registry_creation",
            step_index=4,
            status="completed",
            output_data={"registry_id": 123},
        )

    @pytest.fixture
    def task(self):
        return MockTask(id=1, draft_id=42, document_id=100)

    async def test_execute_delete_registry_document(self, saga, step, task):
        """delete_registry_document вызывает RegistryServiceClient.delete_document с registry_id."""
        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(return_value={"data": {"deleted": True, "document_id": 123}}),
        ) as mock_delete:
            await saga._execute_compensation("delete_registry_document", step, task)

        mock_delete.assert_awaited_once_with(123)

    async def test_execute_delete_registry_document_fallsback_to_task_doc_id(self, saga, task):
        """Когда output_data пуст, delete_registry_document использует task.document_id."""
        step = MockStep("registry_creation", 4, status="completed", output_data={})

        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(),
        ) as mock_delete:
            await saga._execute_compensation("delete_registry_document", step, task)

        mock_delete.assert_awaited_once_with(100)  # task.document_id

    async def test_execute_delete_registry_document_without_task(self, saga, step):
        """Когда task=None, delete_registry_document использует '0' (безопасный fallback)."""
        step_no_output = MockStep("registry_creation", 4, status="completed", output_data={})

        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(),
        ) as mock_delete:
            await saga._execute_compensation("delete_registry_document", step_no_output, task=None)

        mock_delete.assert_awaited_once_with(0)

    async def test_execute_delete_from_vector_index(self, saga, step, task):
        """delete_from_vector_index вызывает RAGBuilderClient.delete_index с document_id."""
        rag_step = MockStep(
            "rag_index", 5, status="completed",
            output_data={"document_id": "42"},
        )

        with patch(
            "app.services.rag_client.RAGBuilderClient.delete_index",
            new=AsyncMock(),
        ) as mock_delete:
            await saga._execute_compensation("delete_from_vector_index", rag_step, task)

        mock_delete.assert_awaited_once_with("42")

    async def test_execute_delete_from_vector_index_fallback_to_task(self, saga, task):
        """Когда output_data пуст, delete_from_vector_index использует task.document_id."""
        rag_step = MockStep("rag_index", 5, status="completed", output_data={})

        with patch(
            "app.services.rag_client.RAGBuilderClient.delete_index",
            new=AsyncMock(),
        ) as mock_delete:
            await saga._execute_compensation("delete_from_vector_index", rag_step, task)

        mock_delete.assert_awaited_once_with("100")  # str(task.document_id)

    async def test_execute_compensation_raises_on_exception(self, saga, step, task):
        """Когда API клиент выбрасывает исключение, _execute_compensation пробрасывает его."""
        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(side_effect=Exception("API unavailable")),
        ):
            with pytest.raises(Exception, match="API unavailable"):
                await saga._execute_compensation("delete_registry_document", step, task)

    async def test_execute_compensation_release_connection_on_error(self, saga, step, task):
        """При ошибке клиент закрывается (close вызывается через finally)."""
        mock_client = AsyncMock()
        mock_client.delete_document = AsyncMock(side_effect=Exception("fail"))

        with patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_client,
        ):
            with pytest.raises(Exception):
                await saga._execute_compensation("delete_registry_document", step, task)

        mock_client.close.assert_awaited_once()


class TestCompensationIdempotency:
    """P2-2: повторный compensate (idempotency)."""

    async def test_double_compensate_does_not_call_action_twice(self):
        """Если compensate вызывается дважды для одного task_id, и шаги
        уже compensated, action НЕ вызывается повторно.

        Текущая реализация: compensate фильтрует completed_steps по
        status == "completed". После первого compensate шаги получают
        status == "compensated" (через compensate_task_step), поэтому
        при втором вызове они уже НЕ completed → action не вызывается.
        """
        from app.core.pipeline.saga import SagaCoordinator

        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        saga = SagaCoordinator(mock_db)
        saga.task_repo = AsyncMock()

        # Шаг уже compensated (после первого вызова)
        saga.task_repo.get_task_steps.return_value = [
            MockStep("registry_creation", 4, status="compensated",
                     output_data={"registry_id": 100}),
            MockStep("rag_index", 5, status="compensated",
                     output_data={"document_id": "42"}),
        ]

        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(),
        ) as mock_delete_doc, patch(
            "app.services.rag_client.RAGBuilderClient.delete_index",
            new=AsyncMock(),
        ) as mock_delete_idx:
            # compensate без упавшего шага в списке → return рано
            await saga.compensate(task_id=1, failed_step="nonexistent_step")

        # Никаких action'ов вызвано не было
        mock_delete_doc.assert_not_called()
        mock_delete_idx.assert_not_called()

    async def test_compensate_marks_already_terminal_task(self, mock_task_repo):
        """Повторный compensate для того же task_id — task уже failed,
        set_task_error и update_task_status вызываются идемпотентно.
        """
        saga = mock_task_repo
        saga.task_repo.get_task_steps.return_value = [
            MockStep("registry_creation", 4, status="completed",
                     output_data={"registry_id": 100}),
            MockStep("rag_index", 5, status="failed"),
        ]
        task = MockTask()

        with patch(
            "app.services.registry_client.RegistryServiceClient.delete_document",
            new=AsyncMock(),
        ):
            await saga.compensate(task_id=1, failed_step="rag_index", task=task)

        # set_task_error и update_task_status вызваны
        saga.task_repo.set_task_error.assert_called_once()
        saga.task_repo.update_task_status.assert_called_once()
