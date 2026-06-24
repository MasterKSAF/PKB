"""
Эндпоинт GET /api/v1/parser/processes – список активных процессов.
"""
from fastapi import APIRouter, Depends
from app.dependencies import get_task_service
from app.services.task_service import TaskService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/processes")
async def list_active_processes(
    task_service: TaskService = Depends(get_task_service),
):
    """
    Возвращает список активных (не завершённых) задач обработки.
    """
    logger.debug("Listing active processes")
    active = await task_service.get_active_tasks()
    result = []
    for task in active:
        result.append(
            {
                "task_id": task.task_id,
                "status": task.status,
                "progress_percent": task.progress_percent,
                "pages_processed": task.pages_processed,
                "pages_total": task.pages_total,
                "started_at": task.started_at.isoformat() + "Z",
            }
        )
    logger.info("Returned %d active processes", len(result))
    return {"processes": result}