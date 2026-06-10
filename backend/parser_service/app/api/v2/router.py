"""
Главный роутер для API версии 2.

Объединяет все эндпоинты версии 2 под префиксом /parser.
Отличается от v1 отсутствием эндпоинта /preview (встроен в /process с mode=preview).
"""
from fastapi import APIRouter
from app.api.v2.endpoints import process, result, status, processes

router = APIRouter(prefix="/parser", tags=["parser"])

router.include_router(process.router)
router.include_router(result.router)
router.include_router(status.router)
router.include_router(processes.router)