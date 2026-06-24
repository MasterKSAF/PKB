"""
Главный роутер для API.

Объединяет все эндпоинты под префиксом /parser.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import process, result, status, processes

router = APIRouter(prefix="/parser", tags=["parser"])

router.include_router(process.router)
router.include_router(result.router)
router.include_router(status.router)
router.include_router(processes.router)