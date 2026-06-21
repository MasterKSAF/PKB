"""
Эндпоинт GET /parser/process/{task_id}/result для API.

Возвращает результат в структурированном формате ResultResponse.
Поддерживает обратную совместимость с результатами, сохранёнными от v1.
"""
from fastapi import APIRouter, HTTPException, status as http_status
from fastapi.responses import JSONResponse
from app.core.task_store import task_store, TaskStatus
from app.core.exceptions import TaskNotFoundError
from app.api.v1.schemas import ResultResponse, ResultMetadata, ParserInfo
from app.config import settings
from datetime import datetime

router = APIRouter()


@router.get("/process/{task_id}/result", response_model=ResultResponse)
async def get_task_result(task_id: int):
    """
    Получает результат выполненной задачи в формате.

    Args:
        task_id: ID задачи.

    Returns:
        ResultResponse: Объект с метаданными, документом, качеством и ошибками.

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
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=http_status.HTTP_409_CONFLICT,
            content={"error": {"code": "TASK_NOT_COMPLETED", "message": "Task not completed yet"}}
        )

    if task_info.result is None:
        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "PARSER_FAILED",
                    "message": "Result is empty"
                }
            }
        )

    result_data = task_info.result
    api_version = result_data.get("api_version", 1)

    if api_version == 1:
        # Совместимость с v1: формируем метаданные из минимальных данных
        document = result_data.get("document", {})
        quality = result_data.get("quality", {})
        errors = result_data.get("errors", [])
        result_status = result_data.get("status", "completed")
        metadata = {
            "schema": settings.parsing_schema,
            "mode": "full",
            "preview_not_supported": False,
            "created_at": datetime.now().isoformat(),
            "parser": {"name": "unknown", "version": "1.0"}
        }
    else:
        metadata = result_data.get("metadata", {})
        document = result_data.get("document", {})
        quality = result_data.get("quality", {})
        errors = result_data.get("errors", [])
        result_status = result_data.get("status", "completed")

    # Извлекаем draft_id из task_info (для совместимости со старыми задачами) 
    draft_id = getattr(task_info, 'draft_id', 0) 

    return ResultResponse(
        task_id=task_id,
        draft_id=draft_id,  
        metadata=ResultMetadata(
            schema_version=metadata.get("schema", settings.parsing_schema),
            mode=metadata.get("mode", "full"),
            preview_not_supported=metadata.get("preview_not_supported", False),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            parser=ParserInfo(**metadata.get("parser", {"name": "unknown", "version": "1.0"}))
        ),
        document=document,
        quality=quality,
        errors=errors,
        status=result_status
    )