"""
Эндпоинт POST /api/v1/parser/process.

Поддерживает два режима:
- full: асинхронная полная обработка (фоновый пайплайн).
- preview: синхронный предпросмотр (возвращает результат сразу).
"""
from fastapi import APIRouter, status, Depends, HTTPException
from datetime import datetime, timedelta, timezone
import logging
import asyncio

from app.api.v1.schemas import ProcessRequest, ProcessResponse, ProcessingMode
from app.dependencies import get_task_service, get_pipeline_service
from app.services.task_service import TaskService
from app.services.pipeline_service import PipelineService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/process", status_code=status.HTTP_202_ACCEPTED)
async def start_processing(
    request: ProcessRequest,
    task_service: TaskService = Depends(get_task_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """
    Запускает обработку документа в зависимости от режима.

    - Режим preview: выполняется синхронно, возвращается ResultResponse.
    - Режим full: задача ставится в очередь, возвращается 202 Accepted.
    """
    # Логируем начало обработки запроса (только для отладки)
    logger.debug(
        "Processing request: task_id=%d, draft_id=%d, file_key=%s, mode=%s, max_pages=%s",
        request.task_id,
        request.draft_id,
        request.file_key,
        request.mode.value,
        request.max_pages,
    )

    # Режим preview (синхронный)
    if request.mode == ProcessingMode.PREVIEW:
        logger.debug("Preview mode selected, delegating to task_service.start_processing")
        return await task_service.start_processing(request)

    # Проверяем, не запущена ли уже задача
    existing_response = await task_service.get_existing_task_response(request.task_id)
    if existing_response:
        logger.info(
            "Task %d already exists with status %s, returning existing response",
            request.task_id,
            existing_response.status,
        )
        return existing_response

    # Проверяем, можно ли поставить задачу в очередь
    if not await pipeline_service.can_run_full_pipeline():
        logger.warning(
            "Full pipeline queue is full, task %d rejected with 429",
            request.task_id,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Full task queue is full, please try later",
        )

    # Создаём задачу в хранилище
    await task_service.create_task(
        request.task_id,
        request.draft_id,
        request.file_key,
        request.options or {},
    )
    logger.debug("Task %d created in storage", request.task_id)

    # Ставим задачу в очередь
    try:
        await pipeline_service.submit_full_task(
            task_id=request.task_id,
            draft_id=request.draft_id,
            file_key=request.file_key,
            options=request.options or {},
        )
        logger.info("Task %d submitted to full pipeline queue", request.task_id)
    except asyncio.QueueFull:
        logger.warning("Queue full, task %d rejected and removed from storage", request.task_id)
        # Откатываем создание задачи (удаляем из хранилища)
        await task_service.remove_task(request.task_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many pending tasks, please try later",
        )
    except Exception:
        logger.exception("Failed to submit task %d to queue", request.task_id)
        await task_service.remove_task(request.task_id)
        raise HTTPException(status_code=500, detail="Internal server error")

    # Оцениваем время ожидания (приблизительно, исходя из очереди)
    queue_size = pipeline_service.get_queue_size()
    estimated_sec = 60 + queue_size * 60
    estimated = datetime.now(timezone.utc) + timedelta(seconds=estimated_sec)
    logger.info(
        "Task %d accepted, estimated completion at %s",
        request.task_id,
        estimated.isoformat(),
    )
    return ProcessResponse(
        task_id=request.task_id,
        status="accepted",
        mode=request.mode,
        estimated_completion=estimated,
    )