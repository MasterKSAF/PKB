"""
Эндпоинт GET /parser/process/{task_id}/status – получение статуса задачи.

Поддерживает long polling через параметр timeout.
Отличается от v1 только отсутствием поля version_id в ответе.
"""
from fastapi import APIRouter
from app.core.task_store import task_store, TaskStatus
from app.core.exceptions import TaskNotFoundError
from app.api.v1.schemas import StatusResponse
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/process/{task_id}/status", response_model=StatusResponse)
async def get_task_status(task_id: int, timeout: int = 15):
    """
    Возвращает текущий статус задачи с поддержкой long polling.

    Если задача завершена или провалена – возвращает сразу.
    Иначе ожидает изменения статуса до timeout секунд.

    Args:
        task_id: ID задачи.
        timeout: Максимальное время ожидания в секундах (по умолчанию 15).

    Returns:
        StatusResponse: Объект со статусом, прогрессом и деталями.

    Raises:
        TaskNotFoundError: Если задача не найдена.
    """
    logger.debug(f"Status request for task {task_id}, timeout={timeout}")
    task_info = task_store.get(task_id)
    if task_info is None:
        logger.warning(f"Task {task_id} not found")
        raise TaskNotFoundError(task_id)

    if task_info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        logger.debug(f"Task {task_id} already terminal")
        return _build_status_response(task_info)

    current_version = task_info.get_version()
    try:
        logger.debug(f"Waiting for change of task {task_id}, version={current_version}")
        await task_store.wait_for_change(task_id, current_version, timeout)
    except Exception:
        pass

    task_info = task_store.get(task_id)
    if task_info is None:
        logger.warning(f"Task {task_id} disappeared during wait")
        raise TaskNotFoundError(task_id)
    logger.info(f"Returning status for task {task_id}: {task_info.status}")
    return _build_status_response(task_info)


def _build_status_response(task_info):
    """
    Формирует объект StatusResponse из TaskInfo.

    Args:
        task_info: Объект TaskInfo.

    Returns:
        StatusResponse: Структурированный ответ со статусом и прогрессом.
    """
    pages_processed = task_info.pages_processed
    if task_info.status == TaskStatus.COMPLETED:
        pages_processed = task_info.pages_total
    return StatusResponse(
        task_id=task_info.task_id,
        status=task_info.status,
        progress_percent=task_info.progress_percent,
        pages_processed=pages_processed,
        pages_total=task_info.pages_total,
        avg_confidence=getattr(task_info, 'avg_confidence', 0.0),
        step=task_info.step,
        step_detail=task_info.step_detail,
        started_at=task_info.started_at,
        completed_at=task_info.completed_at
    )