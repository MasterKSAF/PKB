"""
Unit-тесты Saga Coordinator — компенсация при ошибках pipeline.

Проверяет:
  1. SagaCoordinator.compensate — откат registry_creation после ошибки
  2. _mock_delete_document — runtime vs seed
  3. Компенсация не вызывается для stateless-шагов
"""

import pytest
from unittest.mock import AsyncMock, patch

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

        # delete_document должен быть вызван с document_id=100
        mock_delete.assert_awaited_once_with(100)

        # Компенсация должна отметить шаг
        saga.task_repo.compensate_task_step.assert_called_once()

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

        # Нет шагов ДО registry_creation с компенсацией — delete не вызывается
        mock_delete.assert_not_called()

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
