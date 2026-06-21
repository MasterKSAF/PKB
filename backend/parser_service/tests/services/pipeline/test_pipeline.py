"""
Тесты для оркестратора Pipeline (pipeline.py)
Проверяют:
- последовательное выполнение шагов
- обновление прогресса в task_store
- обработку ошибок и установку статуса FAILED
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.pipeline.pipeline import Pipeline
from app.services.pipeline.steps import PipelineStep
from app.services.pipeline.context import ProcessingContext
from app.core.task_models import TaskStatus


class DummyStep(PipelineStep):
    def __init__(self, raise_error=False, delay=0):
        self.raise_error = raise_error
        self.delay = delay

    async def execute(self, ctx):
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.raise_error:
            raise ValueError("test error")
        ctx.counter = getattr(ctx, "counter", 0) + 1
        return ctx


@pytest.mark.asyncio
async def test_pipeline_create_full():
    pipeline = Pipeline.create(mode="full", track_progress=True)
    step_names = [s.__class__.__name__ for s in pipeline.steps]
    expected = ["DownloadStep", "ValidateStep", "PagesTotalStep", "ParseStep",
                "UploadImagesStep", "NormalizeStep", "StandardizeStep",
                "SaveJsonToFileStep", "StoreResultStep"]
    assert step_names == expected


@pytest.mark.asyncio
async def test_pipeline_create_preview():
    pipeline = Pipeline.create(mode="preview", track_progress=False)
    step_names = [s.__class__.__name__ for s in pipeline.steps]
    expected = ["DownloadStep", "ValidateStep", "PagesTotalStep", "TruncatePdfStep",
                "ParseStep", "NormalizeStep", "StandardizeStep", "StoreResultStep"]
    assert step_names == expected


@pytest.mark.asyncio
async def test_pipeline_run_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf")
    step1 = DummyStep()
    step2 = DummyStep()
    pipeline = Pipeline([step1, step2])

    mock_task_store = AsyncMock()
    with patch("app.services.pipeline.pipeline.task_store", mock_task_store):
        new_ctx = await pipeline.run(ctx)

    assert new_ctx.counter == 2
    assert mock_task_store.update_task.call_count >= 3


@pytest.mark.asyncio
async def test_pipeline_run_error():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf")
    step1 = DummyStep()
    step2 = DummyStep(raise_error=True)
    pipeline = Pipeline([step1, step2])

    mock_task_store = AsyncMock()
    with patch("app.services.pipeline.pipeline.task_store", mock_task_store):
        with pytest.raises(ValueError):
            await pipeline.run(ctx)

    failed_call = mock_task_store.update_task.call_args_list[-1]
    _, kwargs = failed_call
    assert kwargs["status"] == TaskStatus.FAILED
    assert kwargs["error"]["code"] == "PARSER_FAILED"


@pytest.mark.asyncio
async def test_pipeline_cancelled_by_shutdown():
    ctx = ProcessingContext(
        task_id=1, draft_id=1, version_id="v1", file_key="test.pdf",
        shutdown_event=MagicMock()
    )
    ctx.shutdown_event.is_set = MagicMock(return_value=True)
    step = DummyStep(delay=0.1)
    pipeline = Pipeline([step])

    mock_task_store = AsyncMock()
    with patch("app.services.pipeline.pipeline.task_store", mock_task_store):
        with pytest.raises(asyncio.CancelledError):
            await pipeline.run(ctx)

    call_args = mock_task_store.update_task.call_args
    assert call_args is not None
    args, kwargs = call_args
    assert kwargs["status"] == TaskStatus.FAILED
    assert kwargs["error"]["code"] == "CANCELLED"
    assert "completed_at" in kwargs