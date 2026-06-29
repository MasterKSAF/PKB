import time
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import (
    TextSearchRequest, TextSearchResponse, TextSearchAnalysis, TextSearchResult,
)
from ..clients import rag_client
from ..services.auth import get_current_user

router = APIRouter(prefix="/text", tags=["text"])


@router.post("/search", response_model=TextSearchResponse)
async def text_search(
    body: TextSearchRequest,
    user_id: str = Depends(get_current_user),
):
    filters = dict(body.filters)
    if body.document_ids:
        filters["document_ids"] = body.document_ids
    if body.category_ids:
        filters["category_ids"] = body.category_ids

    t0 = time.monotonic()
    try:
        chunks = await rag_client.search(
            query=body.text,
            top_k=body.top_k,
            filters=filters,
            valid_at=body.valid_at,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="RAG search unavailable")

    elapsed = int((time.monotonic() - t0) * 1000)
    results = [
        TextSearchResult(
            section_id=c.section_id,
            document_id=c.document_id,
            document_title=c.document_title,
            page=c.page,
            content=c.content,
            score=c.score,
            document_type="",
            matched_subquery=body.text[:40],
        )
        for c in chunks
    ]
    return TextSearchResponse(
        original_text=body.text,
        analysis=TextSearchAnalysis(
            normalized_query=body.text,
            entities=[],
            subqueries=[body.text],
        ),
        results=results,
        total_found=len(results),
        processing_time_ms=elapsed,
    )
