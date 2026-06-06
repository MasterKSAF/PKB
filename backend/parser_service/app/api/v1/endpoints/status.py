"""
Эндпоинт GET /parser/process/{task_id}/status – longpoll до 15 секунд.
Возвращает текущий статус задачи, прогресс, количество обработанных страниц и т.д.
"""
from fastapi import APIRouter
from app.core.task_store import task_store, TaskStatus
from app.core.exceptions import TaskNotFoundError
from app.api.v1.schemas import StatusResponse

router = APIRouter()


@router.get("/process/{task_id}/status", response_model=StatusResponse)
async def get_task_status(task_id: int, timeout: int = 15):
    """
    Longpoll-метод:
    - Если задача завершена или провалена – возвращает статус немедленно.
    - Иначе ожидает изменения версии задачи (через task_store.wait_for_change) до `timeout` секунд.
    - По таймауту возвращает текущий статус (без ошибки).
    """
    task_info = task_store.get(task_id)
    if task_info is None:
        raise TaskNotFoundError(task_id)

    # Терминальные состояния возвращаем сразу
    if task_info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        return _build_status_response(task_info)

    # Ожидаем изменения
    current_version = task_info.get_version()
    try:
        await task_store.wait_for_change(task_id, current_version, timeout)
    except Exception:
        # При любой ошибке просто возвращаем текущий статус
        pass

    task_info = task_store.get(task_id)
    if task_info is None:
        raise TaskNotFoundError(task_id)

    return _build_status_response(task_info)


def _build_status_response(task_info):
    """
    Преобразует TaskInfo в объект StatusResponse.
    Если задача завершена, pages_processed приравнивается к pages_total.
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