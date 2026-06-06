# app/main.py
"""
Главный модуль FastAPI приложения.
Подключает роутеры, глобальные обработчики ошибок, lifespan менеджер.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.api.v1.router import router as v1_router
from app.api.v1.exception_handlers import (
    parser_service_error_handler,
    validation_error_handler,
    generic_exception_handler
)
from app.core.exceptions import ParserServiceError
from app.core.task_store import task_store   # это фасад TaskStore (группа A)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения:
    - запускает фоновую очистку устаревших задач в task_store
    - при завершении закрывает ресурсы (если есть)
    """
    # Запускаем фоновую очистку задач (чистка каждые 60 минут)
    # task_store.start_cleanup() – корутина, запускаем её в фоне
    cleanup_task = asyncio.create_task(task_store.start_cleanup())
    yield
    # Здесь можно отменить cleanup_task при graceful shutdown
    cleanup_task.cancel()
    # Дополнительные ресурсы (например, сессии MinIO) – пока не требуется


# Создаём экземпляр приложения FastAPI
app = FastAPI(
    title="Parser Service",
    description="Внутренний сервис парсинга документов из MinIO",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роутеры API версии 1
app.include_router(v1_router, prefix=settings.api_prefix)

# ========== Глобальные обработчики исключений ==========
# Все ошибки преобразуются в единый формат {"error": {"code": ..., "message": ...}}
app.add_exception_handler(ParserServiceError, parser_service_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Для проверки работы сервиса (опционально)
@app.get("/health")
async def health_check():
    return {"status": "ok"}