"""
Пайплайн обработки документа: последовательное выполнение шагов.
"""
import logging
from typing import List
import asyncio

from app.services.pipeline.steps import (
    DownloadStep,
    ValidateStep,
    QualityCheckStep,
    PagesTotalStep,
    ParseStep,
    UpdateProgressStep,
    UploadImagesStep,
    TransformStep,
    AssessQualityStep,
    SaveJsonToFileStep,
    StoreResultStep,
    TruncatePdfStep,
)
from app.services.pipeline.context import ProcessingContext
from app.services.normalizer import Normalizer
from app.core.task_store import task_store
from app.core.minio_client import minio_client

logger = logging.getLogger(__name__)


class Pipeline:
    """Управляет последовательностью шагов обработки документа."""

    def __init__(self, steps: List, task_store, minio_client, max_result_size_bytes):
        self.steps = steps
        self.task_store = task_store
        self.minio_client = minio_client
        self.max_result_size_bytes = max_result_size_bytes

    @staticmethod
    def create(mode: str, task_store, minio_client, max_result_size_bytes: int) -> "Pipeline":
        """
        Создаёт пайплайн в зависимости от режима (full/preview).
        Передаёт зависимости в шаги через конструктор.
        """
        normalizer = Normalizer()

        if mode == "full":
            steps = [
                DownloadStep(minio_client),
                ValidateStep(),
                QualityCheckStep(),
                PagesTotalStep(task_store),
                ParseStep(),
                UpdateProgressStep(task_store),
                UploadImagesStep(minio_client),
                TransformStep(normalizer),
                AssessQualityStep(),
                SaveJsonToFileStep(),
                StoreResultStep(task_store, max_result_size_bytes),
            ]
        else:  # preview
            steps = [
                DownloadStep(minio_client),
                ValidateStep(),
                QualityCheckStep(),
                PagesTotalStep(task_store),
                TruncatePdfStep(),
                ParseStep(),
                TransformStep(normalizer),
                AssessQualityStep(),
                StoreResultStep(task_store, max_result_size_bytes),
            ]
        logger.debug("Created pipeline with %d steps, mode=%s", len(steps), mode)
        return Pipeline(steps, task_store, minio_client, max_result_size_bytes)

    async def run(self, ctx: ProcessingContext) -> ProcessingContext:
        """Запускает выполнение пайплайна."""
        import time as _time
        total_steps = len(self.steps)
        _step_times = []
        for i, step in enumerate(self.steps):
            t_s = _time.time()
            if ctx.shutdown_event and ctx.shutdown_event.is_set():
                logger.warning("Pipeline cancelled for task %d due to shutdown", ctx.task_id)
                raise asyncio.CancelledError("Pipeline cancelled due to shutdown")

            step_name = step.__class__.__name__
            progress = int((i / total_steps) * 100)

            if ctx.track_progress:
                await self.task_store.update_task(
                    ctx.task_id,
                    step=step_name,
                    step_detail=f"Шаг {i+1}/{total_steps}: {step_name}",
                    progress_percent=progress,
                )
                logger.debug("Executing step %d/%d: %s", i + 1, total_steps, step_name)

            ctx = await step.execute(ctx)
            t_e = _time.time()
            _step_times.append((step_name, t_e - t_s))
            logger.info("TIMING Pipeline step %s: %.3fs (task %d)", step_name, t_e - t_s, ctx.task_id)

        if ctx.track_progress:
            await self.task_store.update_task(
                ctx.task_id,
                progress_percent=100,
                step="completed",
                step_detail="Все шаги пайплайна выполнены",
            )
        _total = sum(t for _, t in _step_times)
        _steps_summary = ", ".join(f"{n}={t:.1f}s" for n, t in _step_times)
        logger.info("TIMING Pipeline total=%.1fs task=%d [%s]", _total, ctx.task_id, _steps_summary)
        return ctx