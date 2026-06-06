"""
API v1 router configuration with auth dependency.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.endpoints import documents, health, monitor, search, validate

api_router = APIRouter(
    dependencies=[Depends(get_current_user)],
)

# Documents endpoints
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
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
