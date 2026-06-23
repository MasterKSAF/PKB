from fastapi import APIRouter, FastAPI

from rag_search.core.config import settings
from rag_search.models.search import SearchRequest, SearchResponse
from rag_search.services.search_service import SearchService


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
    }


@router.post("/search", response_model=SearchResponse)
async def search_legacy(request: SearchRequest) -> SearchResponse:
    return await SearchService().search(request)


@router.post("/rag/search", response_model=SearchResponse)
async def search_compatible(request: SearchRequest) -> SearchResponse:
    return await SearchService().search(request)


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Search SPD",
        version="0.1.0",
        description="SPD RAG Search service for retrieval over indexed chunks.",
    )
    app.include_router(router)
    return app


app = create_app()
