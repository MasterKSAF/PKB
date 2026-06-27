from fastapi import APIRouter, Depends, FastAPI, HTTPException

from rag_search.core.config import settings
from rag_search.models.search import SearchRequest, SearchResponse
from rag_search.repositories.postgres_search_repository import PostgresSearchRepository
from rag_search.services.search_service import SearchService


router = APIRouter()


def get_search_service() -> SearchService:
    return SearchService()


@router.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
    }


@router.get("/api/v1/ready")
@router.get("/ready")
async def ready() -> dict[str, str]:
    repository = PostgresSearchRepository()

    try:
        repository.assert_read_model_ready()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    return {
        "status": "ready",
        "service": settings.SERVICE_NAME,
    }


@router.post("/search", response_model=SearchResponse)
async def search_legacy(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    try:
        return await service.search(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.post("/api/v1/rag/search", response_model=SearchResponse)
@router.post("/rag/search", response_model=SearchResponse)
async def search_compatible(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    try:
        return await service.search(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Search SPD",
        version="0.1.0",
        description="SPD RAG Search service for retrieval over indexed chunks.",
    )
    app.include_router(router)
    return app


app = create_app()
