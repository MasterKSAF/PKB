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

    rows = await conn.fetch(
        """
        SELECT id
        FROM rag.document_chunks
        WHERE tsv @@ plainto_tsquery('russian', $1)
        ORDER BY ts_rank(tsv, plainto_tsquery('russian', $1)) DESC
        LIMIT $2
        """,
        query,
        limit,
    )

    chunk_ids = [row["id"] for row in rows]

    logger.debug("Sparse search returned %d candidates", len(chunk_ids))

    return chunk_ids