"""
Эндпоинт GET /parser/processes – список активных процессов.
Возвращает задачи, которые ещё не завершены (status = accepted или processing).
"""
from fastapi import APIRouter
from app.core.task_store import task_store

router = APIRouter()


@router.get("/processes")
async def list_active_processes():
    """
    Формирует список активных задач.
    Для каждой задачи возвращает:
    - task_id, version_id, status, progress_percent,
    - pages_processed, pages_total, started_at.
    """
    active = task_store.get_active_tasks()
    result = []
    for task in active:
        result.append({
            "task_id": task.task_id,
            "version_id": task.version_id,
            "status": task.status,
            "progress_percent": task.progress_percent,
            "pages_processed": task.pages_processed,
            "pages_total": task.pages_total,
            "started_at": task.started_at.isoformat() + "Z"
        })
    return {"processes": result}