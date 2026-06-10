# app/core/exception_handlers.py
"""
Глобальные обработчики исключений для API.

Перехватывают кастомные ParserServiceError, валидационные ошибки FastAPI
и любые необработанные исключения, возвращая единообразный JSON-ответ.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import ParserServiceError
from app.api.v1.schemas import ErrorResponse, ErrorDetail
import logging

logger = logging.getLogger(__name__)


async def parser_service_error_handler(request: Request, exc: ParserServiceError):
    """
    Обработчик для всех исключений, наследующих ParserServiceError.

    Args:
        request: HTTP-запрос.
        exc: Исключение сервиса.

    Returns:
        JSONResponse с кодом ошибки из исключения и структурой ErrorResponse.
    """
    logger.error(f"ParserServiceError: {exc.error_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.detail["error"]["message"],
                details=exc.details
            )
        ).model_dump()
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Обработчик ошибок валидации Pydantic (422).

    Args:
        request: HTTP-запрос.
        exc: Исключение валидации FastAPI.

    Returns:
        JSONResponse с 422 и деталями ошибок.
    """
    logger.warning(f"Validation error: {exc.errors()}")
    # Преобразуем исключения ValueError в читаемый JSON
    errors = []
    for err in exc.errors():
        if isinstance(err.get("ctx"), dict) and "error" in err["ctx"]:
            error_obj = err["ctx"]["error"]
            if isinstance(error_obj, ValueError):
                errors.append({
                    "loc": err["loc"],
                    "msg": str(error_obj),
                    "type": err["type"]
                })
            else:
                errors.append(err)
        else:
            errors.append(err)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid request data",
                details={"errors": errors}
            )
        ).model_dump()
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Обработчик любых непредвиденных исключений (500).

    Args:
        request: HTTP-запрос.
        exc: Необработанное исключение.

    Returns:
        JSONResponse с 500 и общим сообщением.
    """
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred. Please contact support."
            )
        ).model_dump()
    )