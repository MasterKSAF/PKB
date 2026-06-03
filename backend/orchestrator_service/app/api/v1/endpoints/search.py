"""
Search and RAG API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.search import (
    AskRequest,
    AskResponse,
    AskSource,
    SearchRequest,
    SearchResponse,
    SearchResultFragment,
)
from app.services.query_client import QueryServiceClient
from app.services.rag_client import RAGServiceClient

router = APIRouter()


@router.post("/documents/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Semantic search for fragments."""
    rag_client = RAGServiceClient()
    try:
        result = await rag_client.search(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters.model_dump() if request.filters else None,
            search_type="hybrid",
        )

        # Convert RAG results to orchestrator format
        fragments = []
        for item in result.get("results", []):
            fragments.append(
                SearchResultFragment(
                    fragment_id=item.get("chunk_id", ""),
                    document_id=item.get("document_id", ""),
                    document_title=item.get("metadata", {}).get("title", "Документ"),
                    document_type=item.get("metadata", {}).get(
                        "document_type", "unknown"
                    ),
                    section=item.get("metadata", {}).get("section"),
                    page=item.get("page_number", 1),
                    fragment=item.get("text", ""),
                    score=item.get("score", 0.0),
                    page_preview_url=item.get("page_preview_url"),
                    document_url=item.get("document_url"),
                )
            )

        return SearchResponse(
            query=request.query,
            items=fragments,
            total_found=result.get("total_found", len(fragments)),
            processing_time_ms=result.get("processing_time_ms", 0),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SEARCH_ERROR", "message": str(e), "details": {}}
            },
        )
    finally:
        await rag_client.close()


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


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """Generate answer with sources."""
    query_client = QueryServiceClient()
    try:
        result = await query_client.text_ask(
            text=request.question,
            document_ids=request.document_ids,
            options=request.options.model_dump() if request.options else None,
        )

        # Convert Query service result to orchestrator format
        sources = []
        for src in result.get("sources", []):
            sources.append(
                AskSource(
                    document_id=src.get("document_id", ""),
                    document_title=src.get("document_title", ""),
                    page_number=src.get("page_number", 1),
                    fragment_id=src.get("fragment_id", ""),
                    text=src.get("text", ""),
                    score=src.get("score", 0.0),
                )
            )

        return AskResponse(
            question=request.question,
            answer=result.get("answer", ""),
            sources=sources,
            processing_time_ms=result.get("processing_time_ms", 0),
            model_used=result.get("model_used", "unknown"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "ASK_ERROR", "message": str(e), "details": {}}},
        )
    finally:
        await query_client.close()
