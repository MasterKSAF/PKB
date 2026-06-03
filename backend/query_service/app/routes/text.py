from fastapi import APIRouter, Depends
from ..schemas import (
    TextSearchRequest, TextSearchResponse, TextSearchAnalysis, TextSearchResult,
    TextAskRequest, TextAskResponse, TextAskSource,
)
from ..services.auth import get_current_user
from ..mocks.rag_responses import SEARCH_RESULTS, ASK_RESPONSE

router = APIRouter(prefix="/text", tags=["text"])


@router.post("/search", response_model=TextSearchResponse)
async def text_search(
    body: TextSearchRequest,
    user_id: str = Depends(get_current_user),
):
    top_k = min(body.top_k, len(SEARCH_RESULTS))
    results = [
        TextSearchResult(**{**r, "matched_subquery": body.text[:40]})
        for r in SEARCH_RESULTS[:top_k]
    ]
    return TextSearchResponse(
        original_text=body.text,
        analysis=TextSearchAnalysis(
            normalized_query=body.text[:80],
            entities=[{"type": "query", "value": body.text[:40]}],
            subqueries=[body.text[:60]],
        ),
        results=results,
        total_found=len(SEARCH_RESULTS),
        processing_time_ms=850,
    )


@router.post("/ask", response_model=TextAskResponse)
async def text_ask(
    body: TextAskRequest,
    user_id: str = Depends(get_current_user),
):
    r = ASK_RESPONSE
    return TextAskResponse(
        original_text=body.text,
        normalized_question=r["normalized_question"],
        answer=r["answer"],
        sources=[TextAskSource(**s) for s in r["sources"]],
        disclaimer=r["disclaimer"],
        processing_time_ms=r["processing_time_ms"],
        model_used=r["model_used"],
    )
