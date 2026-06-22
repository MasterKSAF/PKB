"""
RAG Search mock — обработчик /rag/search.

Все пути относительные, монтируются с префиксом /api/v1/rag в gateway.py.
Реализация возвращает мок-результаты в формате, соответствующем спецификации.
"""

import logging
import random
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mocks.common import error_response

logger = logging.getLogger("rag_search_service")

router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RagSearchFilters(BaseModel):
    document_type: Optional[List[str]] = None
    category_ids: Optional[List[int]] = None
    document_ids: Optional[List[int]] = None


class RagSearchRequest(BaseModel):
    query: str
    valid_at: str
    filters: Optional[RagSearchFilters] = None


# ---------------------------------------------------------------------------
# Mock data (small set of chunks for reproducible responses)
# ---------------------------------------------------------------------------

_MOCK_CHUNKS = [
    {
        "document_id": 1,
        "section_id": 5,
        "clause": "3.1",
        "path": "3/3.1",
        "page": 2,
        "bbox": None,
        "section_title": "Допуски соосности",
        "content": "Допуск соосности для ледового класса Arc4 — не более 0.5 мм на 1 м длины.",
        "content_hash": "sha256-abc111",
    },
    {
        "document_id": 1,
        "section_id": 8,
        "clause": "6.1",
        "path": "6/6.1",
        "page": 2,
        "bbox": None,
        "section_title": "Допуск соосности при степени точности",
        "content": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм.",
        "content_hash": "sha256-abc222",
    },
    {
        "document_id": 2,
        "section_id": 12,
        "clause": "4.2",
        "path": "4/4.2",
        "page": 5,
        "bbox": [0.1, 0.2, 0.8, 0.4],
        "section_title": "Материалы корпуса",
        "content": "Сталь марки 09Г2С допускается к применению в судостроении при температуре до -40°C.",
        "content_hash": "sha256-abc333",
    },
    {
        "document_id": 3,
        "section_id": 3,
        "clause": "1.5",
        "path": "1/1.5",
        "page": 10,
        "bbox": None,
        "section_title": "Сварные соединения",
        "content": "Катет сварного шва принимается по ГОСТ 5264 не менее 6 мм.",
        "content_hash": "sha256-abc444",
    },
]

_MOCK_ID = 0


def _next_chunk_id() -> int:
    global _MOCK_ID
    _MOCK_ID += 1
    return _MOCK_ID + 100


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/search")
async def rag_search(req: RagSearchRequest):
    """Поиск релевантных чанков (без генерации LLM)."""
    query = req.query.strip()
    if not query:
        raise HTTPException(
            status_code=400,
            detail=error_response("EMPTY_QUERY", "Пустой поисковый запрос"),
        )

    # Фильтрация по document_ids, если указаны
    candidates = _MOCK_CHUNKS
    if req.filters and req.filters.document_ids:
        candidates = [
            c for c in candidates
            if c["document_id"] in req.filters.document_ids
        ]
    if req.filters and req.filters.document_type:
        pass
    if req.filters and req.filters.category_ids:
        pass

    # Эмуляция поиска: чем длиннее query, тем больше «релевантных» результатов
    match_count = min(len(candidates), max(1, len(query) // 5))
    results = candidates[:match_count]

    # Контекст (context expansion) — соседние чанки
    context_pool = [
        {"chunk_id": _next_chunk_id(), "content": "Предшествующий контекст...", "score": 0.45, "page": 2},
        {"chunk_id": _next_chunk_id(), "content": "Последующий контекст...", "score": 0.44, "page": 2},
    ]

    response_results = []
    for chunk in results:
        chunk_id = _next_chunk_id()
        response_results.append({
            "source": {
                "document_id": chunk["document_id"],
                "section_id": chunk["section_id"],
                "clause": chunk["clause"],
                "path": chunk["path"],
                "page": chunk["page"],
                "bbox": chunk["bbox"],
                "section_title": chunk["section_title"],
                "content": chunk["content"],
                "content_hash": chunk["content_hash"],
            },
            "retrieval": {
                "chunk_id": chunk_id,
                "score": round(random.uniform(0.7, 0.95), 2),
                "mode": "dense_rerank",
            },
            "context": context_pool,
        })

    return {
        "query": query,
        "results": response_results,
        "processing_time_ms": random.randint(50, 200),
        "total_found": len(candidates),
    }
