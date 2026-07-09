"""Sparse Search: полнотекстовый поиск через ts_rank."""

from __future__ import annotations

import asyncpg

from app.core.logging import get_logger

logger = get_logger("search.sparse")


async def sparse_search(
    conn: asyncpg.Connection,
    query: str,
    top_k: int,
    fetch_multiplier: int = 2,
) -> list[int]:
    """
    Выполнить полнотекстовый поиск по tsvector с ранжированием через ts_rank.

    Args:
        conn: Подключение к БД
        query: Текстовый запрос
        top_k: Количество результатов для возврата
        fetch_multiplier: Множитель для получения кандидатов с запасом (по умолчанию 2)

    Returns:
        Список ID чанков, отсортированный по убыванию ts_rank

    Raises:
        Exception: При ошибке БД (обрабатывается на уровне hybrid_search)
    """
    limit = top_k * fetch_multiplier

    logger.debug("Sparse search: query=%r, top_k=%d, limit=%d", query[:50], top_k, limit)

    # plainto_tsquery with AND fails for Russian queries because:
    #   1. It keeps some lexemes (e.g. "чем" from "чему") that exist in the
    #      query tsvector but NOT in any chunk tsvector (different stemming)
    #   2. AND requires ALL lexemes to match, so stemming differences (e.g.
    #      "применя" vs "примен") cause zero results
    # Fix: build a tsquery from the query's own tsvector with OR logic,
    #       so any single lexeme match returns a candidate. ts_rank then
    #       naturally ranks documents with more matching terms higher.
    rows = await conn.fetch(
        """
        WITH lexemes AS (
            SELECT unnest(to_tsvector('russian', $1)) AS lex
        ),
        or_query AS (
            SELECT to_tsquery('russian',
                       string_agg((lex).lexeme, ' | ' ORDER BY (lex).positions::text)
                   ) AS q
            FROM lexemes
        )
        SELECT c.id
        FROM rag.document_chunks c, or_query
        WHERE c.tsv @@ or_query.q
        ORDER BY ts_rank(c.tsv, or_query.q) DESC
        LIMIT $2
        """,
        query,
        limit,
    )

    chunk_ids = [row["id"] for row in rows]

    logger.debug("Sparse search returned %d candidates", len(chunk_ids))

    return chunk_ids