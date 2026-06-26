from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.schemas import ErrorDetail, ErrorResponse
from app.core.exceptions import ConverterValidatorError


async def converter_error_handler(
    request: Request, exc: ConverterValidatorError
):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.detail["error"]["message"],
                details=exc.details or None,
            )
        ).model_dump(),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid request data",
                details={"errors": exc.errors()},
            )
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="CONVERSION_FAILED",
                message="An unexpected error occurred.",
            )
        ).model_dump(),
    )
