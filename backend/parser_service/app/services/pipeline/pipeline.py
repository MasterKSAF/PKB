"""
Пайплайн обработки документа: последовательное выполнение шагов.
"""
import logging
from typing import List
import asyncio
import os
import shutil
from app.services.pipeline.steps import PipelineStep
from app.services.pipeline.context import ProcessingContext
from app.core.task_store import task_store
from app.core.task_models import TaskStatus
from app.core.exceptions import StorageError
from app.services.pipeline.steps import (
    DownloadStep, ValidateStep, PagesTotalStep, ParseStep,
    UploadImagesStep, NormalizeStep, StandardizeStep,
    SaveJsonToFileStep, StoreResultStep, TruncatePdfStep
)
from app.services.normalizer import Normalizer
from app.services.standardizer import JsonStandardizer

logger = logging.getLogger(__name__)


class Pipeline:
    """Управляет последовательностью шагов обработки документа."""

    def __init__(self, steps: List[PipelineStep]):
        """
        Инициализирует пайплайн с заданным списком шагов.

        Args:
            steps: Список объектов PipelineStep для последовательного выполнения.
        """
        self.steps = steps

    @staticmethod
    def create(mode: str, track_progress: bool = True) -> 'Pipeline':
        """
        Создаёт пайплайн в зависимости от режима.

        Args:
            mode: "full" или "preview"
            track_progress: Обновлять ли статус в task_store

        Returns:
            Настроенный экземпляр Pipeline
        """
        normalizer = Normalizer()
        standardizer = JsonStandardizer()

        if mode == "full":
            steps = [
                DownloadStep(),
                ValidateStep(),
                PagesTotalStep(),
                ParseStep(),
                UploadImagesStep(),
                NormalizeStep(normalizer),
                StandardizeStep(standardizer),
                SaveJsonToFileStep(),
                StoreResultStep()
            ]
        else:  # preview
            steps = [
                DownloadStep(),
                ValidateStep(),
                PagesTotalStep(),
                TruncatePdfStep(),
                ParseStep(),
                NormalizeStep(normalizer),
                StandardizeStep(standardizer),
                StoreResultStep()
            ]
        logger.debug("Created pipeline with %d steps, mode=%s", len(steps), mode)
        return Pipeline(steps)

    async def run(self, ctx: ProcessingContext) -> ProcessingContext:
        """
        Запускает выполнение пайплайна.

        Args:
            ctx: Контекст обработки.

        Returns:
            Обновлённый контекст.

        Raises:
            CancelledError: при отмене (shutdown)
            StorageError: при ошибках хранилища
            Exception: любые другие ошибки (помечают задачу как FAILED)
        """
        total_steps = len(self.steps)
        try:
            for i, step in enumerate(self.steps):
                # Проверка на graceful shutdown
                if ctx.shutdown_event and ctx.shutdown_event.is_set():
                    logger.warning(
                        "Pipeline cancelled for task %d due to shutdown",
                        ctx.task_id
                    )
                    raise asyncio.CancelledError("Pipeline cancelled due to shutdown")

                step_name = step.__class__.__name__
                progress = int((i / total_steps) * 100)

                if ctx.track_progress:
                    await task_store.update_task(
                        ctx.task_id,
                        step=step_name,
                        step_detail=f"Шаг {i+1}/{total_steps}: {step_name}",
                        progress_percent=progress
                    )
                    logger.debug(
                        "Executing step %d/%d: %s",
                        i + 1, total_steps, step_name
                    )

                ctx = await step.execute(ctx)

            if ctx.track_progress:
                await task_store.update_task(
                    ctx.task_id,
                    progress_percent=100,
                    step="completed",
                    step_detail="Все шаги пайплайна выполнены"
                )
            logger.info("Pipeline completed successfully for task %d", ctx.task_id)
            return ctx

        except asyncio.CancelledError:
            logger.warning("Pipeline cancelled for task %d", ctx.task_id)
            if ctx.track_progress:
                await task_store.update_task(
                    ctx.task_id,
                    status=TaskStatus.FAILED,
                    error={"code": "CANCELLED", "message": "Task cancelled due to shutdown"}
                )
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            raise
        except StorageError as e:
            logger.error(
                "Storage error in pipeline for task %d: %s",
                ctx.task_id, str(e), exc_info=True
            )
            if ctx.track_progress:
                await task_store.update_task(
                    ctx.task_id,
                    status=TaskStatus.FAILED,
                    error={"code": "STORAGE_ERROR", "message": str(e)}
                )
            raise
        except Exception as e:
            logger.exception("Pipeline failed for task %d", ctx.task_id)
            if ctx.track_progress:
                await task_store.update_task(
                    ctx.task_id,
                    status=TaskStatus.FAILED,
                    error={"code": "PARSER_FAILED", "message": str(e)}
                )
            raise