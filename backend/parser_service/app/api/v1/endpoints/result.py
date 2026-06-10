"""
Эндпоинт GET /parser/process/{task_id}/result (v1).

Возвращает результат выполнения задачи в формате JSON.
Если задача не завершена – возвращает 409 Conflict.
При ошибке парсинга – 500 с кодом PARSER_FAILED.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from app.core.task_store import task_store, TaskStatus
from app.core.exceptions import TaskNotFoundError

router = APIRouter()


@router.get("/process/{task_id}/result")
async def get_task_result(task_id: int):
    """
    Получает результат выполненной задачи.

    Args:
        task_id: ID задачи.

    Returns:
        JSONResponse: Содержимое результата задачи (task_info.result).

    Raises:
        TaskNotFoundError: Если задача не найдена.
        HTTPException: 409, если задача ещё не завершена.
        HTTPException: 500, если задача завершилась с ошибкой или результат пуст.
    """
    task_info = task_store.get(task_id)
    if task_info is None:
        raise TaskNotFoundError(task_id)

    if task_info.status == TaskStatus.FAILED:
        error = task_info.error or {"code": "PARSER_FAILED", "message": "Unknown error"}
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": error.get("code", "PARSER_FAILED"),
                    "message": error.get("message", "Unknown error"),
                    "details": error.get("details")
                }
            }
        )

    if task_info.status != TaskStatus.COMPLETED:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": {"code": "TASK_NOT_COMPLETED", "message": "Task not completed yet"}}
        )

    if task_info.result is None:
        # Тест ожидает PARSER_FAILED для пустого результата
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "PARSER_FAILED",
                    "message": "Result is empty"
                }
            }
        )

    return task_info.result