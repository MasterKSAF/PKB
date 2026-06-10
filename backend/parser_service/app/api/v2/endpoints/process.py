"""
Эндпоинт POST /parser/process для API версии 2.

Поддерживает два режима:
- full: асинхронная полная обработка (фоновый пайплайн).
- preview: синхронный предпросмотр (возвращает результат сразу).
"""
from datetime import datetime, timedelta, timezone
import asyncio
import os
import shutil
from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse
from app.api.v2.schemas import (
    ProcessRequest, ProcessResponse, PreviewResponse, ProcessingMode
)
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus
from app.services.pipeline.context import ProcessingContext
from app.services.pipeline.pipeline import Pipeline
from app.config import settings
from app.core.exceptions import (
    StorageError, UnsupportedFormatError, ParserFailedError,
    FileNotFoundError, FileTooLargeError
)
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

_shutdown_event = None


def set_shutdown_event(event):
    """
    Устанавливает глобальное событие завершения работы для graceful shutdown.

    Args:
        event: asyncio.Event, который будет установлен при сигнале завершения.
    """
    global _shutdown_event
    _shutdown_event = event


async def _run_full_pipeline(task_id: int, file_key: str, options: dict, shutdown_event: asyncio.Event = None):
    """
    Фоновая задача для выполнения полного пайплайна обработки (v2).

    Args:
        task_id: ID задачи.
        file_key: Ключ файла в MinIO.
        options: Опции парсинга.
        shutdown_event: Событие для отслеживания сигнала завершения.
    """
    logger.info(f"Starting full pipeline for task {task_id}, file {file_key}")
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
        logger.info(f"Full pipeline completed for task {task_id}")
    except asyncio.TimeoutError:
        logger.error(f"Full pipeline timeout after {settings.pipeline_timeout}s for task {task_id}")
        await task_store.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error={"code": "PIPELINE_TIMEOUT", "message": f"Pipeline timeout after {settings.pipeline_timeout}s"}
        )
        if ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
    except asyncio.CancelledError:
        logger.warning(f"Full pipeline cancelled for task {task_id} (shutdown)")
        await task_store.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error={"code": "CANCELLED", "message": "Task cancelled due to shutdown"}
        )
        if ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
    except Exception as e:
        logger.exception(f"Unexpected error in pipeline for task {task_id}")


@router.post("/process", status_code=status.HTTP_202_ACCEPTED)
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Запускает обработку документа в зависимости от режима.

    - Режим preview: выполняется синхронно, результат возвращается немедленно.
    - Режим full: задача ставится в очередь, возвращается 202 Accepted.

    Args:
        request: ProcessRequest с task_id, file_key, mode, max_pages, options.
        background_tasks: FastAPI BackgroundTasks для выполнения фоновой работы.

    Returns:
        JSONResponse: PreviewResponse (для preview) или ProcessResponse (для full).
    """
    if request.mode == ProcessingMode.PREVIEW:
        result = await _sync_preview(request)
        return JSONResponse(content=result.model_dump(), status_code=status.HTTP_200_OK)

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
        estimated_completion=estimated
    )


async def _sync_preview(request: ProcessRequest):
    """
    Синхронное выполнение предпросмотра документа (v2).

    Скачивает файл, валидирует, запускает пайплайн preview и возвращает результат.

    Args:
        request: ProcessRequest с mode=PREVIEW.

    Returns:
        PreviewResponse: Результат предпросмотра.

    Raises:
        StorageError, UnsupportedFormatError, FileNotFoundError, FileTooLargeError,
        ParserFailedError: При ошибках обработки.
    """
    from app.services.file_loader import fetch_and_validate
    import shutil

    ctx = None
    try:
        file_bytes = await fetch_and_validate(request.file_key)
        logger.debug(f"File downloaded for preview, size={len(file_bytes)} bytes")

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
        logger.info(f"Preview pipeline completed for task {request.task_id}")

        document = ctx.final_json.get("content", {}).get("document", {}) if ctx.final_json else {}

        def remove_temp_paths(obj):
            """Рекурсивно удаляет временные пути из объекта JSON."""
            if isinstance(obj, dict):
                if "_temp_path" in obj:
                    del obj["_temp_path"]
                for key in ("image_key", "source", "file_path", "path"):
                    if key in obj and isinstance(obj[key], str) and ("tmp" in obj[key] or "_temp" in obj[key]):
                        del obj[key]
                for v in obj.values():
                    remove_temp_paths(v)
            elif isinstance(obj, list):
                for item in obj:
                    remove_temp_paths(item)

        remove_temp_paths(document)

        return PreviewResponse(
            task_id=request.task_id,
            version_id="",
            preview=True,
            max_pages=request.max_pages,
            metadata={
                "schema": settings.parsing_schema,
                "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            },
            document=document
        )
    except (StorageError, UnsupportedFormatError, FileNotFoundError, FileTooLargeError) as e:
        logger.error(f"Preview error: {e}")
        raise
    except asyncio.TimeoutError as e:
        logger.error(f"Preview timeout after {settings.preview_timeout}s")
        raise ParserFailedError(TimeoutError(f"Preview timeout after {settings.preview_timeout}s")) from e
    except Exception as e:
        logger.exception("Unexpected error in preview")
        if ctx is not None and hasattr(ctx, 'temp_dir') and ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
        raise ParserFailedError(e) from e