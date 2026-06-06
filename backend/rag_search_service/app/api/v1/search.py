"""POST /rag/search — гибридный поиск чанков."""

from __future__ import annotations

import time

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.database import get_connection
from app.core.logging import get_logger
from app.core.search.hybrid import hybrid_search
from app.models.request import SearchRequest
from app.models.response import ChunkResult, SearchResponse

logger = get_logger("search.api")
router = APIRouter()


@router.post(
    "/rag/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Hybrid chunk search",
    description=(
        "Гибридный поиск релевантных чанков. Возвращает сырые чанки с полным содержимым "
        "и метаданными. Без генерации LLM."
    ),
)
async def search_chunks(request: SearchRequest):
    """
    Полный цикл поиска:
      1. Генерация эмбеддинга запроса
      2. Dense + Sparse поиск
      3. RRF-реранжирование
      4. JOIN с метаданными документа и секции
    """
    start = time.monotonic()
    logger.info(
        "Search request: query=%r, top_k=%d, search_type=%s, rerank=%s",
        request.query[:50],
        request.top_k,
        request.search_type,
        request.rerank,
    )

    if request.filters:
        logger.info("Filters received: %s", request.filters.model_dump())

    try:
        async with get_connection() as conn:
            # 1. Гибридный поиск (Dense + Sparse + RRF)
            search_results, total_found = await hybrid_search(
                conn=conn,
                query=request.query,
                top_k=request.top_k,
                search_type=request.search_type,
                rerank=request.rerank,
            )

            if not search_results:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                return SearchResponse(
                    query=request.query,
                    results=[],
                    search_type_used=request.search_type,
                    processing_time_ms=elapsed_ms,
                    total_found=total_found,
                )

            # 2. Подтягивание контента и метаданных (JOIN) с фильтрацией
            chunk_ids = list(search_results.keys())

            # Динамически строим WHERE с фильтрами
            base_query = """
                SELECT
                    c.id            AS chunk_id,
                    c.document_id   AS document_id,
                    d.title         AS document_title,
                    d.doc_code      AS doc_code,
                    c.section_id    AS section_id,
                    s.title         AS section_title,
                    s.clause        AS clause,
                    c.page          AS page,
                    c.content       AS content,
                    c.confidence    AS confidence
                FROM rag.document_chunks c
                JOIN registry.documents d ON d.id = c.document_id
                LEFT JOIN registry.document_sections s ON s.id = c.section_id
                WHERE c.id = ANY($1::bigint[])
            """

            params: list = [chunk_ids]
            filter_clauses: list[str] = []
            param_idx = 2  # следующий индекс после $1

            if request.filters:
                if request.filters.document_type:
                    placeholders = ",".join(f"${param_idx + i}::text" for i in range(len(request.filters.document_type)))
                    filter_clauses.append(f"d.document_type IN ({placeholders})")
                    params.extend(request.filters.document_type)
                    param_idx += len(request.filters.document_type)

                if request.filters.date_from:
                    filter_clauses.append(f"d.adoption_date >= ${param_idx}::date")
                    params.append(request.filters.date_from)
                    param_idx += 1

                if request.filters.date_to:
                    filter_clauses.append(f"d.adoption_date <= ${param_idx}::date")
                    params.append(request.filters.date_to)
                    param_idx += 1

            if filter_clauses:
                base_query += " AND " + " AND ".join(filter_clauses)

            rows = await conn.fetch(base_query, *params)

            # 3. Формирование ответа с сохранением порядка из RRF
            rows_map = {row["chunk_id"]: dict(row) for row in rows}
            results = []
            for chunk_id, score in search_results.items():
                row = rows_map.get(chunk_id)
                if not row:
                    # Чанк мог быть удален между поиском и JOIN (маловероятно, но защищаемся)
                    continue
                
                results.append(
                    ChunkResult(
                        chunk_id=row["chunk_id"],
                        document_id=row["document_id"],
                        document_title=row["document_title"] or "",
                        doc_code=row.get("doc_code"),
                        section_id=row["section_id"],
                        section_title=row.get("section_title"),
                        page=row.get("page"),
                        content=row["content"],
                        score=score,
                        clause=row.get("clause"),
                        confidence=row.get("confidence"),
                    )
                )

            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "Search completed: %d results, %d ms, search_type=%s",
                len(results), elapsed_ms, request.search_type
            )

            return SearchResponse(
                query=request.query,
                results=results,
                search_type_used=request.search_type,
                processing_time_ms=elapsed_ms,
                total_found=total_found,
            )

    except Exception as e:
        logger.exception("Search failed: %s", e)
        # Формат ошибки строго согласно rag_search_service_api.md и common_api.md
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