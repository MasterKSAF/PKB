"""Dense Search: векторный поиск через pgvector cosine distance."""

from __future__ import annotations

import asyncpg

from app.core.logging import get_logger

logger = get_logger("search.dense")


async def dense_search(
    conn: asyncpg.Connection,
    query_embedding: list[float],
    top_k: int,
    fetch_multiplier: int = 2,
) -> list[int]:
    """
    Выполнить векторный поиск по cosine distance.

    Args:
        conn: Подключение к БД
        query_embedding: Вектор запроса
        top_k: Количество результатов для возврата
        fetch_multiplier: Множитель для получения кандидатов с запасом (по умолчанию 2)

    Returns:
        Список ID чанков, отсортированный по убыванию сходства (ближайшие первыми)

    Raises:
        Exception: При ошибке БД (обрабатывается на уровне hybrid_search)
    """
    limit = top_k * fetch_multiplier

    logger.debug("Dense search: embedding_dim=%d, top_k=%d, limit=%d", len(query_embedding), top_k, limit)

    rows = await conn.fetch(
        """
        SELECT id
        FROM rag.document_chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector
        LIMIT $2
        """,
        query_embedding,
        limit,
    )

    chunk_ids = [row["id"] for row in rows]

    logger.debug("Dense search returned %d candidates", len(chunk_ids))

    return chunk_ids