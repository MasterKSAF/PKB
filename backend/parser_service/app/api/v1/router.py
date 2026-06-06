"""
Главный роутер для API версии 1.
Объединяет все эндпоинты префиксом /parser.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import process, preview, status, result, processes

router = APIRouter(prefix="/parser", tags=["parser"])

# Подключаем каждый эндпоинт
router.include_router(process.router)
router.include_router(preview.router)
router.include_router(status.router)
router.include_router(result.router)
router.include_router(processes.router)
