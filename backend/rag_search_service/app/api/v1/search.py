"""POST /rag/search — поиск чанков (dense + rerank) с context expansion."""

from __future__ import annotations

import time

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.database import get_connection
from app.core.logging import get_logger
from app.core.search.context import expand_context_batch
from app.core.search.hybrid import hybrid_search
from app.models.request import SearchRequest
from app.models.response import ContextChunk, RetrievalMeta, SearchResponse, SearchResult, SourceLocator

logger = get_logger("search.api")
router = APIRouter()


@router.post(
    "/rag/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Chunk search (dense + rerank)",
    description=(
        "Поиск релевантных чанков. Возвращает source-локаторы и retrieval-метаданные. "
        "Без генерации LLM."
    ),
)
async def search_chunks(request: SearchRequest):
    """Поиск чанков: dense → rerank → context expansion → ответ."""
    start = time.monotonic()

    if not request.query.strip():
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "EMPTY_QUERY",
                    "message": "Поисковый запрос не может быть пустым",
                    "details": {},
                }
            },
        )

    settings = _get_settings()
    logger.info(
        "Search request: query=%r, valid_at=%s",
        request.query[:50],
        request.valid_at,
    )

    try:
        async with get_connection() as conn:
            # 1. Поиск (dense + rerank)
            search_results, total_found = await hybrid_search(
                conn=conn,
                query=request.query,
                top_k=settings.search_top_k,
                search_type=settings.search_strategy,
                rerank=True,
            )

            if not search_results:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                return SearchResponse(
                    query=request.query,
                    results=[],
                    processing_time_ms=elapsed_ms,
                    total_found=total_found,
                )

            # 2. Подтягивание контента и метаданных (JOIN) с фильтрацией
            chunk_ids = list(search_results.keys())

            base_query = """
                SELECT
                    c.id            AS chunk_id,
                    c.document_id   AS document_id,
                    c.section_id    AS section_id,
                    c.chunk_index   AS chunk_index,
                    s.clause        AS clause,
                    s.path          AS section_path,
                    s.bbox          AS section_bbox,
                    s.title         AS section_title,
                    c.page          AS page,
                    c.content       AS content
                FROM rag.document_chunks c
                JOIN registry.documents d ON d.id = c.document_id
                LEFT JOIN registry.document_sections s ON s.id = c.section_id
                WHERE c.id = ANY($1::bigint[])
                  AND d.valid_from <= $2::date
                  AND d.valid_until >= $2::date
            """

            params: list = [chunk_ids, request.valid_at]
            filter_clauses: list[str] = []
            param_idx = 3

            if request.filters:
                if request.filters.document_type:
                    placeholders = ",".join(
                        f"${param_idx + i}::text"
                        for i in range(len(request.filters.document_type))
                    )
                    filter_clauses.append(f"d.document_type IN ({placeholders})")
                    params.extend(request.filters.document_type)
                    param_idx += len(request.filters.document_type)

                if request.filters.document_ids:
                    placeholders = ",".join(
                        f"${param_idx + i}::bigint"
                        for i in range(len(request.filters.document_ids))
                    )
                    filter_clauses.append(f"d.id IN ({placeholders})")
                    params.extend(request.filters.document_ids)
                    param_idx += len(request.filters.document_ids)

                if request.filters.category_ids:
                    placeholders = ",".join(
                        f"${param_idx + i}::bigint"
                        for i in range(len(request.filters.category_ids))
                    )
                    filter_clauses.append(
                        f"d.id IN (SELECT document_id FROM registry.document_categories "
                        f"WHERE category_id IN ({placeholders}))"
                    )
                    params.extend(request.filters.category_ids)
                    param_idx += len(request.filters.category_ids)

            if filter_clauses:
                base_query += " AND " + " AND ".join(filter_clauses)

            rows = await conn.fetch(base_query, *params)
            rows_map = {row["chunk_id"]: dict(row) for row in rows}

            # 3. Context expansion
            expansion_targets = []
            for chunk_id, score in search_results.items():
                row = rows_map.get(chunk_id)
                if row:
                    expansion_targets.append({
                        "chunk_id": chunk_id,
                        "section_id": row.get("section_id"),
                        "chunk_index": row.get("chunk_index"),
                    })

            context_map = await expand_context_batch(
                conn, expansion_targets, expansion=settings.context_expansion
            )

            # 4. Формирование ответа
            results = []
            for chunk_id, score in search_results.items():
                row = rows_map.get(chunk_id)
                if not row:
                    continue

                # Source locator
                source = SourceLocator(
                    document_id=row["document_id"],
                    section_id=row.get("section_id"),
                    clause=row.get("clause"),
                    path=str(row["section_path"]) if row.get("section_path") else None,
                    page=row.get("page"),
                    bbox=row.get("section_bbox"),
                    section_title=row.get("section_title"),
                    content=row["content"],
                )

                # Retrieval metadata
                retrieval = RetrievalMeta(
                    chunk_id=chunk_id,
                    score=score,
                    mode=settings.search_strategy,
                )

                # Context chunks
                raw_context = context_map.get(chunk_id, [])
                context = [
                    ContextChunk(
                        chunk_id=c["chunk_id"],
                        content=c["content"],
                        page=c.get("page"),
                    )
                    for c in raw_context
                ]

                results.append(SearchResult(
                    source=source,
                    retrieval=retrieval,
                    context=context,
                ))

            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "Search completed: %d results, %d ms, strategy=%s",
                len(results),
                elapsed_ms,
                settings.search_strategy,
            )

            return SearchResponse(
                query=request.query,
                results=results,
                processing_time_ms=elapsed_ms,
                total_found=total_found,
            )

    except Exception as e:
        logger.exception("Search failed: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "SEARCH_FAILED",
                    "message": f"Search failed: {e}",
                    "details": {},
                }
            },
        )


def _get_settings():
    from app.config import get_settings
    return get_settings()
