"""
Эндпоинт GET /parser/process/{task_id}/result.
"""
from fastapi import APIRouter, HTTPException, status as http_status, Depends
from fastapi.responses import JSONResponse
from app.core.task_store import TaskStatus
from app.core.exceptions import TaskNotFoundError
from app.api.v1.schemas import ResultResponse, ResultMetadata, ParserInfo, ProcessingMode
from app.config import settings
from datetime import datetime
from app.dependencies import get_task_service
from app.services.task_service import TaskService
from typing import NamedTuple, Dict, Any, List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ResultData(NamedTuple):
    """Структурированный набор данных, извлечённых из результата задачи."""
    mode: ProcessingMode
    metadata: Dict[str, Any]
    document: Dict[str, Any]
    quality: Dict[str, Any]
    errors: List[Any]
    status: str


def _extract_result_data(result_data: Dict[str, Any]) -> ResultData:
    """
    Извлекает из result_data mode, metadata, document, quality, errors, status.
    Возвращает именованный кортеж ResultData.
    """
    api_version = result_data.get("api_version", 1)

    # Извлекаем mode
    mode_str = result_data.get("mode") or result_data.get("metadata", {}).get("mode", "full")
    try:
        mode = ProcessingMode(mode_str)
    except ValueError:
        mode = ProcessingMode.FULL

    if api_version == 1:
        document = result_data.get("document", {})
        quality = result_data.get("quality", {})
        errors = result_data.get("errors", [])
        status = result_data.get("status", "completed")
        metadata = {
            "schema": settings.parsing_schema,
            "mode": mode.value,
            "preview_not_supported": False,
            "created_at": datetime.now().isoformat(),
            "parser": {"name": "unknown", "version": "1.0"},
        }
    else:
        metadata = result_data.get("metadata", {})
        document = result_data.get("document", {})
        quality = result_data.get("quality", {})
        errors = result_data.get("errors", [])
        status = result_data.get("status", "completed")

    return ResultData(mode, metadata, document, quality, errors, status)


@router.get("/process/{task_id}/result", response_model=ResultResponse)
async def get_task_result(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
):
    """
    Возвращает результат обработки для завершённой задачи.
    """
    logger.debug("Fetching result for task %d", task_id)

    task_info = await task_service.get_task(task_id)
    if task_info is None:
        logger.warning("Task %d not found", task_id)
        raise TaskNotFoundError(task_id)

    if task_info.status == TaskStatus.FAILED:
        error = task_info.error or {"code": "PARSER_FAILED", "message": "Unknown error"}
        logger.error(
            "Task %d failed with error: %s",
            task_id,
            error.get("code", "UNKNOWN"),
        )
        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": error.get("code", "PARSER_FAILED"),
                    "message": error.get("message", "Unknown error"),
                    "details": error.get("details"),
                }
            },
        )

    if task_info.status != TaskStatus.COMPLETED:
        logger.info("Task %d not completed yet, returning 409", task_id)
        return JSONResponse(
            status_code=http_status.HTTP_409_CONFLICT,
            content={"error": {"code": "TASK_NOT_COMPLETED", "message": "Task not completed yet"}},
        )

    if task_info.result is None:
        logger.error("Task %d completed but result is empty", task_id)
        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "PARSER_FAILED",
                    "message": "Result is empty",
                }
            },
        )

    result_data = task_info.result
    extracted = _extract_result_data(result_data)

    draft_id = getattr(task_info, "draft_id", 0)

    metadata_obj = ResultMetadata(
        schema_version=extracted.metadata.get("schema", settings.parsing_schema),
        task_id=task_id,
        draft_id=draft_id,
        mode=extracted.metadata.get("mode", extracted.mode.value),
        preview_not_supported=extracted.metadata.get("preview_not_supported", False),
        created_at=datetime.fromisoformat(
            extracted.metadata.get("created_at", datetime.now().isoformat())
        ),
        parser=ParserInfo(**extracted.metadata.get("parser", {"name": "unknown", "version": "1.0"})),
    )

    logger.info("Result for task %d returned successfully", task_id)
    return ResultResponse(
        metadata=metadata_obj,
        document=extracted.document,
        quality=extracted.quality,
        errors=extracted.errors,
        status=extracted.status,
    )