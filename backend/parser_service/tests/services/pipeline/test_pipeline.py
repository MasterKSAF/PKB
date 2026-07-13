"""
Тесты для оркестратора Pipeline (pipeline.py)
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.pipeline.pipeline import Pipeline
from app.services.pipeline.steps import PipelineStep
from app.services.pipeline.context import ProcessingContext


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
    mock_task_store = AsyncMock()
    mock_minio = AsyncMock()
    pipeline = Pipeline.create(
        mode="full",
        task_store=mock_task_store,
        minio_client=mock_minio,
        max_result_size_bytes=1024*1024
    )
    step_names = [s.__class__.__name__ for s in pipeline.steps]
    expected = [
        "DownloadStep", "ValidateStep", "QualityCheckStep", "PagesTotalStep",
        "ParseStep", "UpdateProgressStep", "UploadImagesStep", "TransformStep",
        "AssessQualityStep", "SaveJsonToFileStep", "StoreResultStep"
    ]
    assert step_names == expected


@pytest.mark.asyncio
async def test_pipeline_create_preview():
    mock_task_store = AsyncMock()
    mock_minio = AsyncMock()
    pipeline = Pipeline.create(
        mode="preview",
        task_store=mock_task_store,
        minio_client=mock_minio,
        max_result_size_bytes=1024*1024
    )
    step_names = [s.__class__.__name__ for s in pipeline.steps]
    expected = [
        "DownloadStep", "ValidateStep", "QualityCheckStep", "PagesTotalStep",
        "TruncatePdfStep", "ParseStep", "TransformStep", "AssessQualityStep",
        "StoreResultStep"
    ]
    assert step_names == expected


@pytest.mark.asyncio
async def test_pipeline_run_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf")
    step1 = DummyStep()
    step2 = DummyStep()
    mock_task_store = AsyncMock()
    mock_minio = AsyncMock()
    pipeline = Pipeline([step1, step2], task_store=mock_task_store, minio_client=mock_minio, max_result_size_bytes=1024)

    new_ctx = await pipeline.run(ctx)

    assert new_ctx.counter == 2
    assert mock_task_store.update_task.call_count >= 3


@pytest.mark.asyncio
async def test_pipeline_run_error():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf")
    step1 = DummyStep()
    step2 = DummyStep(raise_error=True)
    mock_task_store = AsyncMock()
    mock_minio = AsyncMock()
    pipeline = Pipeline([step1, step2], task_store=mock_task_store, minio_client=mock_minio, max_result_size_bytes=1024)

    with pytest.raises(ValueError):
        await pipeline.run(ctx)


@pytest.mark.asyncio
async def test_pipeline_cancelled_by_shutdown():
    shutdown_event = MagicMock()
    shutdown_event.is_set = MagicMock(return_value=True)
    ctx = ProcessingContext(
        task_id=1, draft_id=1, file_key="test.pdf",
        shutdown_event=shutdown_event
    )
    step = DummyStep(delay=0.1)
    mock_task_store = AsyncMock()
    mock_minio = AsyncMock()
    pipeline = Pipeline([step], task_store=mock_task_store, minio_client=mock_minio, max_result_size_bytes=1024)

    with pytest.raises(asyncio.CancelledError):
        await pipeline.run(ctx)