"""Оркестратор гибридного поиска: dense + sparse + RRF + retry/fallback."""

from __future__ import annotations

import asyncio
from typing import Literal

import asyncpg

from app.config import get_settings
from app.core.embeddings import get_embedding_provider
from app.core.logging import get_logger
from app.core.search.dense import dense_search
from app.core.search.rrf import reciprocal_rank_fusion
from app.core.search.sparse import sparse_search

logger = get_logger("search.hybrid")

# Политика retry согласно pipeline3-search.md:
# RAG Search: 2 retry, exponential backoff 500ms → 1s
_MAX_RETRIES = 2
_RETRY_BACKOFF = [0.5, 1.0]  # секунды


async def _run_with_retry(
    search_fn,
    conn: asyncpg.Connection,
    *args,
    **kwargs,
) -> list[int]:
    """
    Запустить поисковую функцию с retry (2 попытки, exponential backoff).

    Args:
        search_fn: Асинхронная функция поиска (dense_search или sparse_search)
        conn: Подключение к БД
        *args, **kwargs: Аргументы для search_fn

    Returns:
        Список ID чанков

    Raises:
        Exception: Если все retry исчерпаны
    """
    last_exc = None
    for attempt in range(1 + _MAX_RETRIES):
        try:
            return await search_fn(conn, *args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF[attempt]
                logger.warning(
                    "%s attempt %d failed, retrying in %.1fs: %s",
                    search_fn.__name__, attempt + 1, wait, e,
                )
                await asyncio.sleep(wait)
            else:
                logger.error(
                    "%s all %d attempts failed: %s",
                    search_fn.__name__, _MAX_RETRIES + 1, e,
                )
    raise last_exc  # type: ignore[misc]


async def hybrid_search(
    conn: asyncpg.Connection,
    query: str,
    top_k: int = 10,
    search_type: Literal["hybrid", "dense", "sparse"] = "hybrid",
    rerank: bool = True,
) -> tuple[dict[int, float], int]:
    """
    Выполнить гибридный поиск чанков с опциональным RRF-реранжированием.

    Реализует политику retry/fallback согласно pipeline3-search.md:
    - RAG Search: 2 retry, exponential backoff 500ms → 1s
    - При ошибке dense: fallback на sparse (если sparse тоже упал — ошибка)
    - При ошибке sparse: fallback на dense (если dense тоже упал — ошибка)

    Args:
        conn: Подключение к БД
        query: Текстовый запрос
        top_k: Количество результатов для возврата
        search_type: Тип поиска (hybrid, dense, sparse)
        rerank: Применять RRF-реранжирование (только для hybrid)

    Returns:
        Кортеж (results, total_found):
            results: Словарь {chunk_id: score}, отсортированный по убыванию скора.
                Для dense/sparse score = 1.0 (порядок определяется БД).
                Для hybrid score = RRF score.
            total_found: Общее количество найденных кандидатов (до top_k).

    Raises:
        ValueError: Если query пустой или search_type невалидный
        Exception: При критической ошибке поиска (все retry исчерпаны)
    """
    if not query.strip():
        raise ValueError("Query cannot be empty")

    settings = get_settings()
    results: dict[int, float] = {}
    total_found: int = 0

    if search_type == "dense":
        logger.info("Executing dense-only search for query=%r", query[:50])
        embedding_provider = get_embedding_provider()
        query_embedding = await embedding_provider.encode(query)
        chunk_ids = await _run_with_retry(
            dense_search, conn, query_embedding, top_k, settings.search_fetch_multiplier
        )
        total_found = len(chunk_ids)
        results = {chunk_id: 1.0 for chunk_id in chunk_ids[:top_k]}

    elif search_type == "sparse":
        logger.info("Executing sparse-only search for query=%r", query[:50])
        chunk_ids = await _run_with_retry(
            sparse_search, conn, query, top_k, settings.search_fetch_multiplier
        )
        total_found = len(chunk_ids)
        results = {chunk_id: 1.0 for chunk_id in chunk_ids[:top_k]}

    elif search_type == "hybrid":
        logger.info("Executing hybrid search for query=%r", query[:50])

        # Получаем эмбеддинг запроса
        embedding_provider = get_embedding_provider()
        query_embedding = await embedding_provider.encode(query)

        # Выполняем оба поиска с retry и fallback
        dense_ids: list[int] = []
        sparse_ids: list[int] = []

        # Dense с retry; при ошибке — fallback на sparse
        try:
            dense_ids = await _run_with_retry(
                dense_search, conn, query_embedding, top_k, settings.search_fetch_multiplier
            )
        except Exception as e:
            logger.error("Dense search failed after retries, falling back to sparse-only: %s", e)

        # Sparse с retry; при ошибке — fallback на dense
        try:
            sparse_ids = await _run_with_retry(
                sparse_search, conn, query, top_k, settings.search_fetch_multiplier
            )
        except Exception as e:
            logger.error("Sparse search failed after retries: %s", e)
            if not dense_ids:
                raise  # Если оба упали — пробрасываем ошибку

        # Объединяем результаты через RRF
        if rerank and (dense_ids or sparse_ids):
            ranked_lists = [lst for lst in [dense_ids, sparse_ids] if lst]
            rrf_scores = reciprocal_rank_fusion(ranked_lists, k=settings.search_rrf_k)
            total_found = len(rrf_scores)
            results = dict(list(rrf_scores.items())[:top_k])
        else:
            # Без RRF — возвращаем dense результаты (или sparse, если dense пустой)
            primary_ids = dense_ids if dense_ids else sparse_ids
            total_found = len(primary_ids)
            results = {chunk_id: 1.0 for chunk_id in primary_ids[:top_k]}

    else:
        raise ValueError(f"Invalid search_type: {search_type}. Must be 'hybrid', 'dense', or 'sparse'")

    logger.info(
        "Search completed: %d results (total_found=%d), search_type=%s",
        len(results), total_found, search_type,
    )

    return results, total_found