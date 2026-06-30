"""Reranking-провайдер через Infinity v2 API.

Формат ответа Infinity v2 (отличается от TEI):
    {
        "object": "rerank",
        "results": [{
            "relevance_score": 0.98,   // не "score"
            "index": 0,
            "document": null            // не "text"
        }],
        "model": "BAAI/bge-reranker-v2-m3",
        ...
    }
"""

from __future__ import annotations

import httpx

from app.config import get_settings
from app.core.logging import get_logger
from app.core.reranking.base import RerankResult, RerankerProvider, RerankingError

logger = get_logger("reranking.infinity")


class InfinityRerankerProvider(RerankerProvider):
    """Reranking через Infinity v2 HTTP API (POST /rerank)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=settings.reranker_base_url,
            timeout=settings.reranker_timeout,
        )
        self._model = settings.reranker_model

    _BATCH_SIZE = 4

    async def rerank(self, query: str, documents: list[str], top_n: int) -> list[RerankResult]:
        if not documents:
            return []

        all_results: list[RerankResult] = []
        for offset in range(0, len(documents), self._BATCH_SIZE):
            batch = documents[offset : offset + self._BATCH_SIZE]
            batch_results = await self._rerank_batch(query, batch)
            for r in batch_results:
                all_results.append(RerankResult(index=r.index + offset, score=r.score, text=r.text))

        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:top_n]

    async def _rerank_batch(self, query: str, documents: list[str]) -> list[RerankResult]:
        try:
            resp = await self._client.post(
                "/rerank",
                json={
                    "model": self._model,
                    "query": query,
                    "documents": documents,
                    "top_n": len(documents),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            items = data if isinstance(data, list) else data.get("results", [])

            # Infinity v2 возвращает relevance_score и document (может быть None)
            return [
                RerankResult(
                    index=r["index"],
                    score=float(r.get("relevance_score", r.get("score", 0.0))),
                    text=r.get("document") or r.get("text", "") or "",
                )
                for r in items
            ]
        except httpx.HTTPStatusError as e:
            raise RerankingError(f"Infinity HTTP error: {e.response.status_code}") from e
        except httpx.ConnectError as e:
            raise RerankingError(f"Infinity connection refused: {e}") from e
        except httpx.TimeoutException as e:
            raise RerankingError(f"Infinity timeout: {e}") from e
        except Exception as e:
            raise RerankingError(f"Infinity rerank failed: {e}") from e

    def get_model_name(self) -> str:
        return self._model

    async def close(self) -> None:
        await self._client.aclose()
