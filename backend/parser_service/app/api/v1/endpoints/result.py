"""
Эндпоинт GET /parser/process/{task_id}/result – получение готового JSON-контейнера.
Вызывается оркестратором только после получения статуса completed.
"""
from fastapi import APIRouter, HTTPException, status
from app.core.task_store import task_store, TaskStatus
from app.core.exceptions import TaskNotFoundError

router = APIRouter()


@router.get("/process/{task_id}/result")
async def get_task_result(task_id: int):
    """
    Возвращает результат парсинга (JSON-контейнер).
    - Если задача не найдена – 404.
    - Если задача завершилась с ошибкой – 500 с кодом PARSER_FAILED.
    - Если задача ещё не завершена – 409 Conflict.
    - Если результат пуст – 500.
    """
    task_info = task_store.get(task_id)
    if task_info is None:
        raise TaskNotFoundError(task_id)

    if task_info.status == TaskStatus.FAILED:
        error = task_info.error or {"code": "PARSER_FAILED", "message": "Unknown error"}
        raise HTTPException(status_code=500, detail=error)

    if task_info.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task not completed yet"
        )

    if task_info.result is None:
        raise HTTPException(status_code=500, detail="Result is empty")

    return task_info.result