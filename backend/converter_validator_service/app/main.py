from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.v1.exception_handlers import (
    converter_error_handler,
    generic_exception_handler,
    validation_error_handler,
)
from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.exceptions import ConverterValidatorError


app = FastAPI(
    title="Converter-Validator Service",
    description="Конвертация raw JSON (Parser/OCR) в validated_v3",
    version="1.0.0",
)

app.include_router(v1_router, prefix=settings.api_prefix)

app.add_exception_handler(ConverterValidatorError, converter_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
