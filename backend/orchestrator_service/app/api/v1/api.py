"""
API v1 router configuration with auth dependency.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.endpoints import documents, drafts, health, monitor, search, tasks, validate

api_router = APIRouter(
    dependencies=[Depends(get_current_user)],
)

# Drafts endpoints
api_router.include_router(
    drafts.router,
    prefix="/drafts",
    tags=["drafts"],
)

# Documents endpoints (existing, will be deprecated)
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
)

# Tasks endpoints
api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"],
)

# Search and RAG endpoints
api_router.include_router(
    search.router,
    prefix="",
    tags=["search"],
)

# Validation endpoints
api_router.include_router(
    validate.router,
    prefix="/validate",
    tags=["validation"],
)

# Health check
api_router.include_router(
    health.router,
    prefix="",
    tags=["health"],
)

# Monitor / metrics
api_router.include_router(
    monitor.router,
    prefix="/monitor",
    tags=["monitor"],
)
