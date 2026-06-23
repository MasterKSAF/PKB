"""
API v1 router configuration with auth dependency.

Единая точка входа — POST /drafts (draft-first).
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.endpoints import documents, drafts, health, tasks

api_router = APIRouter(
    dependencies=[Depends(get_current_user)],
)

# Drafts endpoints — единая точка входа для загрузки
api_router.include_router(
    drafts.router,
    prefix="/drafts",
    tags=["drafts"],
)


# Documents endpoints — только pipeline-операция reprocess
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
)


# Tasks endpoints — админка пайплайнов
api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"],
)


# Health check
api_router.include_router(
    health.router,
    prefix="",
    tags=["health"],
)
