"""
Эндпоинт POST /parser/process – асинхронный запуск полной обработки документа (v1).

Принимает задачу, добавляет её в хранилище и запускает фоновый пайплайн.
Возвращает 202 Accepted с предполагаемым временем завершения.
"""
from datetime import datetime, timedelta, timezone
import asyncio
import os
import shutil
from fastapi import APIRouter, BackgroundTasks, status
from app.api.v1.schemas import ProcessRequest, ProcessResponse
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus
from app.services.pipeline.context import ProcessingContext
from app.services.pipeline.pipeline import Pipeline
from app.config import settings
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


async def _run_pipeline(task_id: int, version_id: str, file_key: str, options: dict, shutdown_event: asyncio.Event = None):
    """
    Фоновая задача для выполнения полного пайплайна обработки.

    Args:
        task_id: ID задачи.
        version_id: Версия документа.
        file_key: Ключ файла в MinIO.
        options: Опции парсинга.
        shutdown_event: Событие для отслеживания сигнала завершения.
    """
    logger.info(f"Starting full pipeline for task {task_id}, file {file_key}")
    ctx = ProcessingContext(
        task_id=task_id,
        version_id=version_id,
        file_key=file_key,
        options=options,
        track_progress=True,
        shutdown_event=shutdown_event,
        api_version=1
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


@router.post("/process", status_code=status.HTTP_202_ACCEPTED, response_model=ProcessResponse)
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Запускает асинхронную обработку документа.

    Если задача с таким task_id уже существует и не завершена, возвращает
    существующий статус. Иначе создаёт новую задачу и запускает пайплайн в фоне.

    Args:
        request: ProcessRequest с task_id, version_id, file_key, options.
        background_tasks: FastAPI BackgroundTasks для выполнения фоновой работы.

    Returns:
        ProcessResponse: Статус принятия задачи и предполагаемое время завершения.
    """
    logger.info(f"Process request received: task_id={request.task_id}, file_key={request.file_key}")
    existing = task_store.get(request.task_id)
    if existing and existing.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        logger.debug(f"Task {request.task_id} already exists with status {existing.status}, returning existing")
        return ProcessResponse(
            task_id=request.task_id,
            status=existing.status.value,
            version_id=request.version_id,
            estimated_completion=datetime.now(timezone.utc) + timedelta(seconds=30)
        )

    task_info = TaskInfo(
        task_id=request.task_id,
        version_id=request.version_id,
        file_key=request.file_key,
        options=request.options or {}
    )
    task_store.add(task_info)
    logger.debug(f"Task {request.task_id} added to store")

    background_tasks.add_task(
        _run_pipeline,
        request.task_id,
        request.version_id,
        request.file_key,
        request.options or {},
        _shutdown_event
    )
    estimated = datetime.now(timezone.utc) + timedelta(seconds=60)
    return ProcessResponse(
        task_id=request.task_id,
        status="accepted",
        version_id=request.version_id,
        estimated_completion=estimated
    )