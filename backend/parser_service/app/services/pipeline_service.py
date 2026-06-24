"""
Сервис управления пайплайнами обработки.
"""
import asyncio
import os
import shutil
import logging
from datetime import datetime, timezone
from typing import Optional

from app.services.pipeline.pipeline import Pipeline
from app.services.pipeline.context import ProcessingContext
from app.core.task_models import TaskStatus
from app.core.exceptions import (
    StorageError,
    UnsupportedFormatError,
    FileNotFoundError,
    FileTooLargeError,
    ParserFailedError,
    FatalError,
)
from app.services.result_builder import build_result
from app.api.v1.schemas import ProcessRequest, ResultResponse
from app.core.retry import retry

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Сервис управления пайплайнами обработки документов.
    Управляет очередью full-задач, параллельностью выполнения и предпросмотром.
    """

    def __init__(self, minio_client, task_store, settings, shutdown_event=None):
        self.minio_client = minio_client
        self.task_store = task_store
        self.settings = settings
        self.shutdown_event = shutdown_event

        # Семафор для preview
        self._preview_semaphore = asyncio.Semaphore(settings.max_concurrent_preview_tasks)

        # Семафор для full-задач
        self._full_semaphore = asyncio.Semaphore(settings.max_concurrent_full_pipelines)

        # Очередь full-задач
        self._queue = asyncio.Queue(maxsize=settings.max_full_queue_size)
        self._worker_task: Optional[asyncio.Task] = None
        self._start_worker()

        logger.info(
            "PipelineService initialized: preview_limit=%d, full_limit=%d, queue_size=%d",
            settings.max_concurrent_preview_tasks,
            settings.max_concurrent_full_pipelines,
            settings.max_full_queue_size,
        )

    def _start_worker(self):
        """Запускает фоновый воркер для обработки очереди."""
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.debug("Worker task created")

    async def _worker_loop(self):
        """Основной цикл воркера: извлекает задачи из очереди и запускает."""
        logger.info("Full pipeline worker started")
        try:
            while True:
                if self.shutdown_event and self.shutdown_event.is_set():
                    logger.info("Worker stopped due to shutdown event")
                    break

                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                task_id, draft_id, file_key, options = item
                logger.info(
                    "Worker processing task %d, queue size now %d",
                    task_id,
                    self._queue.qsize(),
                )

                async with self._full_semaphore:
                    try:
                        await self._run_full_pipeline_async(task_id, draft_id, file_key, options)
                    except Exception as e:
                        logger.exception("Worker failed to process task %d", task_id)
                    finally:
                        self._queue.task_done()

        except asyncio.CancelledError:
            logger.info("Worker loop cancelled")
        except Exception as e:
            logger.exception("Unexpected error in worker loop: %s", e)
        finally:
            logger.info("Full pipeline worker stopped")

    async def submit_full_task(
        self,
        task_id: int,
        draft_id: int,
        file_key: str,
        options: dict,
    ) -> bool:
        """
        Помещает full-задачу в очередь.
        Возвращает True, если задача поставлена, иначе выбрасывает asyncio.QueueFull.
        """
        try:
            await asyncio.wait_for(
                self._queue.put((task_id, draft_id, file_key, options)),
                timeout=self.settings.queue_submit_timeout,
            )
            logger.info("Task %d submitted to queue (size %d)", task_id, self._queue.qsize())
            return True
        except asyncio.TimeoutError:
            logger.warning("Queue full, task %d rejected", task_id)
            raise asyncio.QueueFull(f"Task queue full (limit {self._queue.maxsize})")

    async def can_run_full_pipeline(self) -> bool:
        """Проверяет, не переполнена ли очередь."""
        return self._queue.qsize() < self._queue.maxsize

    def get_queue_size(self) -> int:
        """Возвращает текущий размер очереди full-задач."""
        return self._queue.qsize()

    @retry(
        exceptions=(StorageError, TimeoutError, ConnectionError),
        max_attempts=3,
        delay=1.0,
        backoff=2.0,
    )
    async def _download_with_retry(self, file_key: str) -> bytes:
        """Скачивает файл с повторными попытками при временных ошибках."""
        return await self.minio_client.download_and_validate(file_key)

    async def _execute_pipeline(
        self,
        ctx: ProcessingContext,
        mode: str,
        timeout: int,
    ) -> ProcessingContext:
        """
        Общий метод выполнения пайплайна с обработкой ошибок и очисткой.
        """
        pipeline = Pipeline.create(
            mode=mode,
            task_store=self.task_store,
            minio_client=self.minio_client,
            max_result_size_bytes=self.settings.max_result_size_bytes,
        )
        try:
            return await asyncio.wait_for(pipeline.run(ctx), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(
                "Pipeline timeout after %ds for task %d",
                timeout,
                ctx.task_id,
                exc_info=True,
            )
            await self.task_store.update_task(
                ctx.task_id,
                status=TaskStatus.FAILED,
                error={
                    "code": "PIPELINE_TIMEOUT",
                    "message": f"Pipeline timeout after {timeout}s",
                },
                completed_at=datetime.now(timezone.utc),
            )
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            raise
        except asyncio.CancelledError:
            logger.warning("Pipeline cancelled for task %d", ctx.task_id)
            await self.task_store.update_task(
                ctx.task_id,
                status=TaskStatus.FAILED,
                error={"code": "CANCELLED", "message": "Task cancelled"},
                completed_at=datetime.now(timezone.utc),
            )
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            raise
        except (StorageError, FileNotFoundError, UnsupportedFormatError, FileTooLargeError) as e:
            logger.error(
                "Pipeline failed for task %d: %s",
                ctx.task_id,
                str(e),
                exc_info=True,
            )
            await self.task_store.update_task(
                ctx.task_id,
                status=TaskStatus.FAILED,
                error={"code": e.error_code, "message": str(e)},
                completed_at=datetime.now(timezone.utc),
            )
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            raise
        except Exception as e:
            logger.exception("Unexpected error in pipeline for task %d", ctx.task_id)
            await self.task_store.update_task(
                ctx.task_id,
                status=TaskStatus.FAILED,
                error={"code": "FATAL_ERROR", "message": str(e)},
                completed_at=datetime.now(timezone.utc),
            )
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            raise FatalError(f"Unexpected pipeline error: {str(e)}", e)

    async def _run_full_pipeline_async(
        self,
        task_id: int,
        draft_id: int,
        file_key: str,
        options: dict,
    ) -> None:
        """Запускает полный пайплайн для задачи."""
        logger.info("Starting full pipeline for task %d, file %s", task_id, file_key)
        ctx = ProcessingContext(
            task_id=task_id,
            draft_id=draft_id,
            file_key=file_key,
            options=options,
            max_pages=None,
            track_progress=True,
            shutdown_event=self.shutdown_event,
            api_version=2,
        )
        await self._execute_pipeline(ctx, "full", self.settings.pipeline_timeout)
        logger.info("Full pipeline completed for task %d", task_id)

    async def run_preview(self, request: ProcessRequest) -> ResultResponse:
        """
        Выполняет предпросмотр с ограничением параллельности.
        """
        async with self._preview_semaphore:
            try:
                file_bytes = await self._download_with_retry(request.file_key)
                logger.debug(
                    "File downloaded for preview, size=%d bytes",
                    len(file_bytes),
                )

                ctx = ProcessingContext(
                    task_id=request.task_id,
                    draft_id=request.draft_id,
                    file_key=request.file_key,
                    options=request.options or {},
                    max_pages=request.max_pages,
                    file_bytes=file_bytes,
                    track_progress=False,
                    shutdown_event=self.shutdown_event,
                    api_version=2,
                )

                ctx = await self._execute_pipeline(ctx, "preview", self.settings.preview_timeout)
                logger.info("Preview pipeline completed for task %d", request.task_id)

                if ctx.final_json is None:
                    raise RuntimeError("Pipeline finished without final_json")

                result_payload = build_result(
                    task_id=request.task_id,
                    draft_id=request.draft_id,
                    final_json=ctx.final_json,
                    mode="preview",
                    preview_not_supported=getattr(ctx, "preview_not_supported", False),
                )

                return ResultResponse(**result_payload)

            except (StorageError, FileNotFoundError, UnsupportedFormatError, FileTooLargeError) as e:
                logger.error("Preview error: %s", e, exc_info=True)
                raise
            except asyncio.TimeoutError as e:
                logger.error("Preview timeout after %ds", self.settings.preview_timeout, exc_info=True)
                raise ParserFailedError(
                    TimeoutError(f"Preview timeout after {self.settings.preview_timeout}s")
                ) from e
            except Exception as e:
                logger.exception("Unexpected error in preview")
                raise ParserFailedError(e) from e

    async def shutdown_worker(self):
        """Останавливает воркер gracefully."""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Worker shut down")