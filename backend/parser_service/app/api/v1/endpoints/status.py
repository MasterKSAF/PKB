"""
Эндпоинт GET /parser/process/{task_id}/status – получение статуса задачи.
"""
from fastapi import APIRouter, Depends
from app.core.task_store import TaskStatus
from app.core.exceptions import TaskNotFoundError
from app.api.v1.schemas import StatusResponse
from app.dependencies import get_task_service
from app.services.task_service import TaskService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/process/{task_id}/status", response_model=StatusResponse)
async def get_task_status(
    task_id: int,
    timeout: int = 15,
    task_service: TaskService = Depends(get_task_service),
):
    """
    Возвращает текущий статус задачи с поддержкой long polling (опционально).
    """
    logger.debug("Status request for task %d, timeout=%d", task_id, timeout)

    task_info = await task_service.get_task(task_id)
    if task_info is None:
        logger.warning("Task %d not found", task_id)
        raise TaskNotFoundError(task_id)

    # Если задача уже завершена — сразу возвращаем статус
    if task_info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        logger.info("Task %d is terminal, returning status %s", task_id, task_info.status.value)
        return _build_status_response(task_info)

    # Ожидание изменения (long polling)
    current_version = task_info.get_version()
    try:
        logger.debug("Waiting for change of task %d, version=%d", task_id, current_version)
        changed = await task_service.wait_for_change(task_id, current_version, timeout)
        if not changed:
            logger.debug("Timeout waiting for task %d, returning current status", task_id)
    except Exception:
        # В случае ошибки ожидания просто продолжаем
        logger.exception("Error while waiting for task %d change", task_id)

    # Повторно получаем задачу после ожидания
    task_info = await task_service.get_task(task_id)
    if task_info is None:
        logger.warning("Task %d disappeared during wait", task_id)
        raise TaskNotFoundError(task_id)

    logger.info("Returning status for task %d: %s", task_id, task_info.status.value)
    return _build_status_response(task_info)


def _build_status_response(task_info):
    """
    Формирует объект StatusResponse на основе данных задачи.
    """
    pages_processed = task_info.pages_processed
    if task_info.status == TaskStatus.COMPLETED:
        pages_processed = task_info.pages_total

    return StatusResponse(
        task_id=task_info.task_id,
        status=task_info.status.value,
        progress_percent=task_info.progress_percent,
        pages_processed=pages_processed,
        pages_total=task_info.pages_total,
        avg_confidence=getattr(task_info, "avg_confidence", 0.0),
        step=task_info.step,
        step_detail=task_info.step_detail,
        started_at=task_info.started_at,
        completed_at=task_info.completed_at,
    )