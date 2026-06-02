"""
Глобальные обработчики исключений для API версии 1.
Форматируют все ошибки в соответствии с контрактом: {"error": {"code": ..., "message": ...}}
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import ParserServiceError
from app.api.v1.schemas import ErrorResponse, ErrorDetail

async def parser_service_error_handler(request: Request, exc: ParserServiceError):
    """
    Обработчик кастомных исключений ParserServiceError.
    Они уже содержат status_code и детали в формате {"error": {...}}.
    """
    # exc.detail – это словарь, который мы передавали в конструкторе ParserServiceError
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
    Обработчик ошибок валидации Pydantic (неправильный JSON, неверные типы, нарушение ограничений).
    Возвращаем HTTP 422 (Unprocessable Entity) с кодом VALIDATION_ERROR.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid request data",
                details={"errors": exc.errors()}   # exc.errors() содержит список проблемных полей
            )
        ).model_dump()
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Ловит все необработанные исключения (внутренние ошибки сервера).
    Логируем реальную ошибку для отладки, но пользователю отдаём общий код.
    В реальном проекте здесь нужно добавить logging.
    """
    # TODO: добавить логирование с exc_info=True
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred. Please contact support."
            )
        ).model_dump()
    )