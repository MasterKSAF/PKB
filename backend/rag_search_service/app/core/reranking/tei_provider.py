"""Reranking-провайдер через TEI (Text Embeddings Inference)."""

from __future__ import annotations

import httpx

from app.config import get_settings
from app.core.logging import get_logger
from app.core.reranking.base import RerankResult, RerankerProvider, RerankingError

logger = get_logger("reranking.tei")


class TEIRerankerProvider(RerankerProvider):
    """Reranking через TEI HTTP API (POST /rerank)."""

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
                    "query": query,
                    "texts": documents,
                    "top_n": len(documents),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            items = data if isinstance(data, list) else data.get("results", [])
            return [
                RerankResult(
                    index=r["index"],
                    score=r["score"],
                    text=r.get("text", ""),
                )
                for r in items
            ]
        except httpx.HTTPStatusError as e:
            raise RerankingError(f"TEI HTTP error: {e.response.status_code}") from e
        except httpx.ConnectError as e:
            raise RerankingError(f"TEI connection refused: {e}") from e
        except httpx.TimeoutException as e:
            raise RerankingError(f"TEI timeout: {e}") from e
        except Exception as e:
            raise RerankingError(f"TEI rerank failed: {e}") from e

    def get_model_name(self) -> str:
        return self._model

    async def close(self) -> None:
        await self._client.aclose()
