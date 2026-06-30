"""Оркестратор поиска: стратегии S1-S7 (rag_experiments_methodology.md).

S1  — dense:         только dense (векторный поиск)
S2  — dense_rerank:  dense + cross-encoder rerank (продакшн)
S3  — sparse:        только sparse (BM25)
S4  — hybrid:        dense + sparse, простое слияние (среднее)
S5  — hybrid_rerank: S4 + cross-encoder rerank
S6  — hybrid_rrf:    dense + sparse, RRF (k=60)
S7  — hybrid_rrf_rerank: S6 + cross-encoder rerank
"""

from __future__ import annotations

import asyncio

import asyncpg

from app.config import get_settings
from app.core.embeddings import get_embedding_provider
from app.core.logging import get_logger
from app.core.reranking import RerankingError, get_reranker
from app.core.search.chunks import fetch_chunk_contents
from app.core.search.dense import dense_search
from app.core.search.rrf import reciprocal_rank_fusion
from app.core.search.sparse import sparse_search

logger = get_logger("search.hybrid")

_MAX_RETRIES = 2
_RETRY_BACKOFF = [0.5, 1.0]

# Все поддерживаемые стратегии
VALID_STRATEGIES = frozenset({
    "dense",           # S1
    "dense_rerank",    # S2 (продакшн)
    "sparse",          # S3
    "hybrid",          # S4
    "hybrid_rerank",   # S5
    "hybrid_rrf",      # S6
    "hybrid_rrf_rerank",  # S7
})


async def _run_with_retry(
    search_fn,
    conn: asyncpg.Connection,
    *args,
    **kwargs,
) -> list[int]:
    """Запустить поисковую функцию с retry."""
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
                    search_fn.__name__,
                    attempt + 1,
                    wait,
                    e,
                )
                await asyncio.sleep(wait)
            else:
                logger.error(
                    "%s all %d attempts failed: %s",
                    search_fn.__name__,
                    _MAX_RETRIES + 1,
                    e,
                )
    raise last_exc  # type: ignore[misc]


async def _try_rerank(
    conn: asyncpg.Connection,
    query: str,
    candidate_ids: list[int],
    top_k: int,
) -> dict[int, float] | None:
    """Попытка reranking через TEI. Возвращает {chunk_id: score} или None при ошибке."""
    if not candidate_ids:
        return None
    try:
        chunk_contents = await fetch_chunk_contents(conn, candidate_ids)
        if not chunk_contents:
            return None
        id_list = [cid for cid in candidate_ids if cid in chunk_contents]
        documents = [chunk_contents[cid] for cid in id_list]

        reranker = get_reranker()
        tei_results = await reranker.rerank(query, documents, top_n=top_k)

        if not tei_results:
            return None
        return {id_list[r.index]: r.score for r in tei_results if r.index < len(id_list)}
    except RerankingError:
        logger.warning("TEI reranker unavailable, will use fallback")
        return None
    except Exception as e:
        logger.warning("TEI reranker error: %s", e)
        return None


def _merge_simple(
    dense_ids: list[int],
    sparse_ids: list[int],
    top_k: int,
) -> tuple[dict[int, float], int]:
    """Простое слияние (S4/S5): усредняем скоры dense и sparse."""
    scores: dict[int, float] = {}
    counts: dict[int, int] = {}

    for cid in dense_ids:
        scores[cid] = scores.get(cid, 0.0) + 1.0
        counts[cid] = counts.get(cid, 0) + 1

    for cid in sparse_ids:
        scores[cid] = scores.get(cid, 0.0) + 1.0
        counts[cid] = counts.get(cid, 0) + 1

    for cid in scores:
        scores[cid] /= counts[cid]

    sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
    return dict(list(sorted_scores.items())[:top_k]), len(sorted_scores)


def _merge_rrf(
    dense_ids: list[int],
    sparse_ids: list[int],
    top_k: int,
    rrf_k: int,
) -> tuple[dict[int, float], int]:
    """RRF слияние (S6/S7)."""
    ranked_lists = [lst for lst in [dense_ids, sparse_ids] if lst]
    rrf_scores = reciprocal_rank_fusion(ranked_lists, k=rrf_k)
    return dict(list(rrf_scores.items())[:top_k]), len(rrf_scores)


def _raw_scores(candidate_ids: list[int], top_k: int) -> tuple[dict[int, float], int]:
    """Score=1.0 для всех кандидатов."""
    return {cid: 1.0 for cid in candidate_ids[:top_k]}, len(candidate_ids)


async def _run_dense(
    conn: asyncpg.Connection,
    query_embedding: list[float],
    top_k: int,
    fetch_k: int,
) -> list[int]:
    """Dense-поиск с retry."""
    return await _run_with_retry(dense_search, conn, query_embedding, top_k, fetch_k)


async def _run_sparse(
    conn: asyncpg.Connection,
    query: str,
    top_k: int,
    fetch_k: int,
) -> list[int]:
    """Sparse-поиск с retry."""
    return await _run_with_retry(sparse_search, conn, query, top_k, fetch_k)


async def _get_embedding(query: str) -> list[float]:
    """Получить эмбеддинг запроса."""
    provider = get_embedding_provider()
    return await provider.encode(query)


async def hybrid_search(
    conn: asyncpg.Connection,
    query: str,
    top_k: int = 10,
    search_type: str = "dense_rerank",
    rerank: bool = True,
) -> tuple[dict[int, float], int]:
    """
    Выполнить поиск чанков по выбранной стратегии.

    Стратегии:
        S1: dense          — только dense
        S2: dense_rerank   — dense + TEI rerank (продакшн)
        S3: sparse         — только sparse (BM25)
        S4: hybrid         — dense + sparse, простое слияние
        S5: hybrid_rerank  — S4 + TEI rerank
        S6: hybrid_rrf     — dense + sparse, RRF
        S7: hybrid_rrf_rerank — S6 + TEI rerank

    Returns:
        Кортеж (results, total_found)
    """
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if search_type not in VALID_STRATEGIES:
        raise ValueError(
            f"Invalid search_type: {search_type}. "
            f"Must be one of: {', '.join(sorted(VALID_STRATEGIES))}"
        )

    settings = get_settings()
    # Множитель для dense/sparse запроса: сколько кандидатов на каждый top_k.
    # reranker_fetch_multiplier — при rerank, search_fetch_multiplier — без rerank.
    fetch_k = settings.reranker_fetch_multiplier if rerank else settings.search_fetch_multiplier

    results: dict[int, float] = {}
    total_found: int = 0

    # --- S1: dense ---
    if search_type == "dense":
        logger.info("S1 dense: query=%r", query[:50])
        emb = await _get_embedding(query)
        dense_ids = await _run_dense(conn, emb, top_k, fetch_k)
        total_found = len(dense_ids)
        results = _raw_scores(dense_ids, top_k)[0]

    # --- S2: dense_rerank (продакшн) ---
    elif search_type == "dense_rerank":
        logger.info("S2 dense_rerank: query=%r", query[:50])
        emb = await _get_embedding(query)
        dense_ids = await _run_dense(conn, emb, top_k, fetch_k)
        total_found = len(dense_ids)

        if dense_ids:
            tei = await _try_rerank(conn, query, dense_ids, top_k)
            if tei is not None:
                results = tei
                logger.info("S2 dense_rerank: TEI rerank succeeded")
                return results, total_found
        results = _raw_scores(dense_ids, top_k)[0]

    # --- S3: sparse ---
    elif search_type == "sparse":
        logger.info("S3 sparse: query=%r", query[:50])
        sparse_ids = await _run_sparse(conn, query, top_k, fetch_k)
        total_found = len(sparse_ids)
        results = _raw_scores(sparse_ids, top_k)[0]

    # --- S4: hybrid (простое слияние) ---
    elif search_type == "hybrid":
        logger.info("S4 hybrid: query=%r", query[:50])
        emb = await _get_embedding(query)

        dense_ids, sparse_ids = await _run_dense_sparse(conn, emb, query, top_k, fetch_k)
        all_ids = list(dict.fromkeys(dense_ids + sparse_ids))
        total_found = len(all_ids)
        results, _ = _merge_simple(dense_ids, sparse_ids, top_k)

    # --- S5: hybrid_rerank ---
    elif search_type == "hybrid_rerank":
        logger.info("S5 hybrid_rerank: query=%r", query[:50])
        emb = await _get_embedding(query)

        dense_ids, sparse_ids = await _run_dense_sparse(conn, emb, query, top_k, fetch_k)
        all_ids = list(dict.fromkeys(dense_ids + sparse_ids))
        total_found = len(all_ids)

        if all_ids:
            tei = await _try_rerank(conn, query, all_ids, top_k)
            if tei is not None:
                results = tei
                logger.info("S5 hybrid_rerank: TEI rerank succeeded")
                return results, total_found
        results, _ = _merge_simple(dense_ids, sparse_ids, top_k)

    # --- S6: hybrid_rrf ---
    elif search_type == "hybrid_rrf":
        logger.info("S6 hybrid_rrf: query=%r", query[:50])
        emb = await _get_embedding(query)

        dense_ids, sparse_ids = await _run_dense_sparse(conn, emb, query, top_k, fetch_k)
        all_ids = list(dict.fromkeys(dense_ids + sparse_ids))
        total_found = len(all_ids)
        results, _ = _merge_rrf(dense_ids, sparse_ids, top_k, settings.search_rrf_k)

    # --- S7: hybrid_rrf_rerank ---
    elif search_type == "hybrid_rrf_rerank":
        logger.info("S7 hybrid_rrf_rerank: query=%r", query[:50])
        emb = await _get_embedding(query)

        dense_ids, sparse_ids = await _run_dense_sparse(conn, emb, query, top_k, fetch_k)
        all_ids = list(dict.fromkeys(dense_ids + sparse_ids))
        total_found = len(all_ids)

        if all_ids:
            tei = await _try_rerank(conn, query, all_ids, top_k)
            if tei is not None:
                results = tei
                logger.info("S7 hybrid_rrf_rerank: TEI rerank succeeded")
                return results, total_found
        results, _ = _merge_rrf(dense_ids, sparse_ids, top_k, settings.search_rrf_k)

    logger.info(
        "Search completed: %d results (total_found=%d), strategy=%s",
        len(results),
        total_found,
        search_type,
    )

    return results, total_found


async def _run_dense_sparse(
    conn: asyncpg.Connection,
    query_embedding: list[float],
    query: str,
    top_k: int,
    fetch_k: int,
) -> tuple[list[int], list[int]]:
    """Запустить dense и sparse параллельно (для S4-S7)."""
    dense_ids: list[int] = []
    sparse_ids: list[int] = []

    try:
        dense_ids = await _run_dense(conn, query_embedding, top_k, fetch_k)
    except Exception as e:
        logger.error("Dense search failed: %s", e)

    try:
        sparse_ids = await _run_sparse(conn, query, top_k, fetch_k)
    except Exception as e:
        logger.error("Sparse search failed: %s", e)
        if not dense_ids:
            raise

    return dense_ids, sparse_ids
