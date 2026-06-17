"""
Эндпоинт POST /api/v1/parser/process.

Поддерживает два режима:
- full: асинхронная полная обработка (фоновый пайплайн).
- preview: синхронный предпросмотр (возвращает результат сразу).
"""

from datetime import datetime, timedelta, timezone
import asyncio
import os
import shutil
from fastapi import APIRouter, BackgroundTasks, status
from pydantic import ValidationError as PydanticValidationError

from app.api.v1.schemas import (
    ProcessRequest, ProcessResponse, ProcessingMode, ResultResponse
)
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus
from app.services.pipeline.context import ProcessingContext
from app.services.pipeline.pipeline import Pipeline
from app.services.result_builder import ResultBuilder
from app.config import settings
from app.core.exceptions import (
    StorageError, UnsupportedFormatError, ParserFailedError,
    FileNotFoundError, FileTooLargeError
)
from app.services.file_loader import fetch_and_validate

import logging

router = APIRouter()
logger = logging.getLogger(__name__)

_shutdown_event = None


def set_shutdown_event(event: asyncio.Event) -> None:
    """
    Устанавливает глобальное событие завершения работы для graceful shutdown.

    Args:
        event: asyncio.Event, который будет установлен при сигнале завершения.
    """
    global _shutdown_event
    _shutdown_event = event


async def _run_full_pipeline(
    task_id: int,
    file_key: str,
    options: dict,
    shutdown_event: asyncio.Event = None
) -> None:
    """
    Фоновая задача для выполнения полного пайплайна обработки.

    Args:
        task_id: ID задачи.
        file_key: Ключ файла в MinIO.
        options: Опции парсинга.
        shutdown_event: Событие для отслеживания сигнала завершения.
    """
    logger.info("Starting full pipeline for task %d, file %s", task_id, file_key)
    ctx = ProcessingContext(
        task_id=task_id,
        version_id="",
        file_key=file_key,
        options=options,
        max_pages=None,
        track_progress=True,
        shutdown_event=shutdown_event,
        api_version=2
    )
    pipeline = Pipeline.create(mode="full", track_progress=True)
    try:
        await asyncio.wait_for(pipeline.run(ctx), timeout=settings.pipeline_timeout)
        logger.info("Full pipeline completed for task %d", task_id)
    except asyncio.TimeoutError:
        logger.error("Full pipeline timeout after %ds for task %d", settings.pipeline_timeout, task_id)
        await task_store.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error={"code": "PIPELINE_TIMEOUT", "message": f"Pipeline timeout after {settings.pipeline_timeout}s"},
            completed_at=datetime.now(timezone.utc)
        )
        if ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
    except asyncio.CancelledError:
        logger.warning("Full pipeline cancelled for task %d (shutdown)", task_id)
        await task_store.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error={"code": "CANCELLED", "message": "Task cancelled due to shutdown"},
            completed_at=datetime.now(timezone.utc)
        )
        if ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
    except Exception as e:
        logger.exception("Unexpected error in pipeline for task %d", task_id)


@router.post("/process", status_code=status.HTTP_202_ACCEPTED)
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Запускает обработку документа в зависимости от режима.

    - Режим preview: выполняется синхронно, возвращается ResultResponse (202).
    - Режим full: задача ставится в очередь, возвращается 202 Accepted.

    Args:
        request: Объект запроса с параметрами.
        background_tasks: FastAPI BackgroundTasks для выполнения фоновой работы.

    Returns:
        ResultResponse для preview, ProcessResponse для full.
    """
    # Режим preview (синхронный)
    if request.mode == ProcessingMode.PREVIEW:
        try:
            result = await _sync_preview(request)
            return result
        except (StorageError, UnsupportedFormatError, FileNotFoundError, FileTooLargeError):
            raise
        except Exception as e:
            logger.exception("Preview failed for task %d", request.task_id)
            raise ParserFailedError(e) from e

    # Режим full (асинхронный)
    existing = task_store.get(request.task_id)
    if existing and existing.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        return ProcessResponse(
            task_id=request.task_id,
            status=existing.status.value,
            estimated_completion=datetime.now(timezone.utc) + timedelta(seconds=30)
        )

    task_info = TaskInfo(
        task_id=request.task_id,
        version_id="",
        file_key=request.file_key,
        options=request.options or {}
    )
    task_store.add(task_info)

    background_tasks.add_task(
        _run_full_pipeline,
        request.task_id,
        request.file_key,
        request.options or {},
        _shutdown_event
    )

    estimated = datetime.now(timezone.utc) + timedelta(seconds=60)
    return ProcessResponse(
        task_id=request.task_id,
        status="accepted",
        mode=request.mode,
        estimated_completion=estimated
    )


async def _sync_preview(request: ProcessRequest) -> ResultResponse:
    """
    Синхронное выполнение предпросмотра документа.

    Скачивает файл, валидирует, запускает пайплайн preview и возвращает результат.

    Args:
        request: ProcessRequest с mode=PREVIEW.

    Returns:
        ResultResponse: Результат предпросмотра.

    Raises:
        StorageError, UnsupportedFormatError, FileNotFoundError, FileTooLargeError,
        ParserFailedError: При ошибках обработки.
    """
    ctx = None
    try:
        file_bytes = await fetch_and_validate(request.file_key)
        logger.debug("File downloaded for preview, size=%d bytes", len(file_bytes))

        ctx = ProcessingContext(
            task_id=request.task_id,
            version_id="",
            file_key=request.file_key,
            options=request.options or {},
            max_pages=request.max_pages,
            file_bytes=file_bytes,
            track_progress=False,
            api_version=2
        )

        pipeline = Pipeline.create(mode="preview", track_progress=False)
        ctx = await asyncio.wait_for(pipeline.run(ctx), timeout=settings.preview_timeout)
        logger.info("Preview pipeline completed for task %d", request.task_id)

        if ctx.final_json is None:
            raise RuntimeError("Pipeline finished without final_json")

        result_payload = ResultBuilder.build(
            task_id=request.task_id,
            final_json=ctx.final_json,
            mode="preview",
            preview_not_supported=getattr(ctx, 'preview_not_supported', False)
        )

        try:
            response = ResultResponse(**result_payload)
        except PydanticValidationError as e:
            logger.error("Response validation failed: %s", e.errors())
            raise RuntimeError(f"Invalid response structure: {e}")

        return response

    except (StorageError, UnsupportedFormatError, FileNotFoundError, FileTooLargeError) as e:
        logger.error("Preview error: %s", e)
        raise
    except asyncio.TimeoutError as e:
        logger.error("Preview timeout after %ds", settings.preview_timeout)
        raise ParserFailedError(TimeoutError(f"Preview timeout after {settings.preview_timeout}s")) from e
    except Exception as e:
        logger.exception("Unexpected error in preview")
        raise ParserFailedError(e) from e
    # Примечание: временная директория удаляется внутри парсера, не здесь