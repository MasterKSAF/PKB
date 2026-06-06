"""Агрегация всех роутеров."""

from fastapi import APIRouter

from app.api.v1 import health, search

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(search.router, tags=["search"])