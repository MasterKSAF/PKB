"""
Тесты для оркестратора Pipeline (pipeline.py)
Проверяют:
- последовательное выполнение шагов
- обновление прогресса в task_store
- обработку ошибок и установку статуса FAILED
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.pipeline.pipeline import Pipeline
from app.services.pipeline.steps import PipelineStep
from app.services.pipeline.context import ProcessingContext
from app.core.task_models import TaskStatus


class DummyStep(PipelineStep):
    """Тестовый шаг, который может либо успешно выполниться, либо выбросить ошибку."""
    def __init__(self, raise_error: bool = False):
        self.raise_error = raise_error

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if self.raise_error:
            raise ValueError("test error")
        ctx.step_executed = True   # добавляем маркер в контекст
        return ctx


@pytest.mark.asyncio
async def test_pipeline_runs_steps():
    """Проверка, что Pipeline последовательно выполняет все шаги и обновляет прогресс."""
    ctx = ProcessingContext(task_id=1, version_id="v", file_key="test.pdf")
    step1 = DummyStep()
    step2 = DummyStep()
    pipeline = Pipeline([step1, step2])

    mock_task_store = AsyncMock()
    with patch("app.services.pipeline.pipeline.task_store", mock_task_store):
        new_ctx = await pipeline.run(ctx)

    # Шаг установил маркер в контексте
    assert new_ctx.step_executed is True

    # Количество вызовов update_task: начальный (0%) + для каждого шага + финальный (100%)
    assert mock_task_store.update_task.call_count >= 3

    # Финальный вызов должен иметь progress_percent=100 и step="completed"
    final_call = mock_task_store.update_task.call_args_list[-1]
    _, kwargs = final_call
    assert kwargs.get("progress_percent") == 100
    assert kwargs.get("step") == "completed"


@pytest.mark.asyncio
async def test_pipeline_handles_error():
    """Проверка, что при ошибке в шаге задача помечается как FAILED и ошибка пробрасывается."""
    ctx = ProcessingContext(task_id=1, version_id="v", file_key="test.pdf")
    step1 = DummyStep()
    step2 = DummyStep(raise_error=True)   # второй шаг упадёт
    pipeline = Pipeline([step1, step2])

    mock_task_store = AsyncMock()
    with patch("app.services.pipeline.pipeline.task_store", mock_task_store):
        with pytest.raises(ValueError):
            await pipeline.run(ctx)

    # Проверяем, что был вызван update_task со статусом FAILED
    failed_call = mock_task_store.update_task.call_args_list[-1]
    _, kwargs = failed_call
    assert kwargs.get("status") == TaskStatus.FAILED
    assert kwargs.get("error")["code"] == "PARSER_FAILED"
    assert "test error" in kwargs.get("error")["message"]