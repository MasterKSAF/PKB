"""
API v1 router configuration.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import documents, health, search, validate

api_router = APIRouter()

# Documents endpoints
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

# Search and RAG endpoints
api_router.include_router(
    search.router,
    prefix="",
    tags=["search"]
)

# Validation endpoints
api_router.include_router(
    validate.router,
    prefix="/validate",
    tags=["validation"]
)

# Health check
api_router.include_router(
    health.router,
    prefix="",
    tags=["health"]
)
