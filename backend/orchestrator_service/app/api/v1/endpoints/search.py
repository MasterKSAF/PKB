"""
Search API endpoints — stub implementation without external services.
"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultFragment,
)

router = APIRouter()


MOCK_RESULTS = [
    SearchResultFragment(
        fragment_id="frg-mock-001",
        document_id="doc-norm-001",
        document_title="Правила РС, часть I",
        document_type="normative",
        page=42,
        fragment="Результат поиска для запроса (фрагмент 1)",
        score=0.94,
    ),
    SearchResultFragment(
        fragment_id="frg-mock-002",
        document_id="doc-norm-002",
        document_title="СНиП 2.01.07-85",
        document_type="normative",
        page=15,
        fragment="Результат поиска для запроса (фрагмент 2)",
        score=0.87,
    ),
    SearchResultFragment(
        fragment_id="frg-mock-003",
        document_id="doc-proj-001",
        document_title="Проект А, раздел 3",
        document_type="project",
        page=8,
        fragment="Результат поиска для запроса (фрагмент 3)",
        score=0.72,
    ),
]


@router.post("/documents/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Semantic search for fragments."""
    start = time.monotonic()

    try:
        fragments = MOCK_RESULTS[: min(request.top_k, len(MOCK_RESULTS))]

        return SearchResponse(
            query=request.query,
            items=fragments,
            total_found=len(fragments),
            processing_time_ms=int((time.monotonic() - start) * 1000),
            enrichment_skipped=False,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SEARCH_ERROR", "message": str(e), "details": {}}
            },
        )


@router.get("/documents/search", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., description="Поисковый запрос"),
    document_id: Optional[str] = Query(None, description="ID документа"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """Quick GET variant of search."""
    request = SearchRequest(
        query=q, document_ids=[document_id] if document_id else None, top_k=limit
    )
    return await search(request)
