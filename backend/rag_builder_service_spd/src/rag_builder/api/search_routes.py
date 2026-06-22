# rag_builder_service_spd/src/rag_builder/api/search_routes.py

from fastapi import APIRouter, HTTPException

from rag_builder.models.search import SearchRequest, SearchResponse
from rag_builder.services.search_service import SearchService

router = APIRouter()


@router.post(
    "/rag/search",
    response_model=SearchResponse,
)
@router.post(
    "/search",
    response_model=SearchResponse,
)

def search_chunks(request: SearchRequest) -> SearchResponse:
    """
    Search relevant chunks.

    MVP supports dense vector search only.
    """
    service = SearchService()

    try:
        return service.search(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
