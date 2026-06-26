from __future__ import annotations

import hashlib
import time
from typing import Any

import httpx
from loguru import logger
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from rag_builder.core.config import settings


class RetryableEmbeddingError(Exception):
    pass


class EmbeddingService:
    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim if dim is not None else settings.vector_dimension

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        logger.info(
            "Embeddings start count={} dim={} provider={}",
            len(texts),
            self.dim,
            settings.embedding_provider,
        )
        if settings.embedding_provider in ("openai_compatible", "infinity", "tei"):
            vectors = await self._embed_openai_compatible(texts)
        else:
            vectors = [self._deterministic_embedding(t) for t in texts]
        logger.info("Embeddings done count={} dim={}", len(vectors), self.dim)
        return vectors

    def _deterministic_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = list(digest)
        vec = [((seed[i % len(seed)] / 255.0) * 2.0) - 1.0 for i in range(self.dim)]
        return vec

    async def _embed_openai_compatible(self, texts: list[str]) -> list[list[float]]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if settings.embedding_api_key:
            headers["Authorization"] = f"Bearer {settings.embedding_api_key}"

        batch_size = max(1, settings.embedding_batch_size)
        all_vectors: list[list[float]] = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        async with httpx.AsyncClient(timeout=settings.embedding_timeout) as client:
            for batch_idx, start in enumerate(range(0, len(texts), batch_size), start=1):
                batch = texts[start : start + batch_size]
                vectors = await self._embed_batch_with_retry(
                    client=client,
                    headers=headers,
                    batch=batch,
                    batch_idx=batch_idx,
                    total_batches=total_batches,
                )
                all_vectors.extend(vectors)
        return all_vectors

    async def _embed_batch_with_retry(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        batch: list[str],
        batch_idx: int,
        total_batches: int,
    ) -> list[list[float]]:
        attempts = settings.embedding_retries + 1
        retrying = AsyncRetrying(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, RetryableEmbeddingError)),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                attempt_no = int(attempt.retry_state.attempt_number)
                payload = {"model": settings.embedding_model, "input": batch}
                logger.info(
                    "Embedding batch request start batch={}/{} size={} attempt={} url={} model={}",
                    batch_idx,
                    total_batches,
                    len(batch),
                    attempt_no,
                    settings.embedding_api_url,
                    settings.embedding_model,
                )
                started = time.perf_counter()
                response = await client.post(settings.embedding_api_url, headers=headers, json=payload)
                took_ms = (time.perf_counter() - started) * 1000
                logger.info(
                    "Embedding batch response batch={}/{} attempt={} status={} took_ms={:.2f}",
                    batch_idx,
                    total_batches,
                    attempt_no,
                    response.status_code,
                    took_ms,
                )
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    logger.warning(
                        "Embedding transient failure batch={}/{} attempt={} status={} retrying",
                        batch_idx,
                        total_batches,
                        attempt_no,
                        response.status_code,
                    )
                    raise RetryableEmbeddingError(f"Transient status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                vectors = self._parse_openai_embeddings(data)
                if len(vectors) != len(batch):
                    raise ValueError(
                        f"Embedding batch size mismatch vectors={len(vectors)} expected={len(batch)}"
                    )
                logger.info("Embedding batch done batch={}/{} vectors={}", batch_idx, total_batches, len(vectors))
                return vectors
        raise RuntimeError("Embedding retry loop finished without result")

    def _parse_openai_embeddings(self, data: dict[str, Any]) -> list[list[float]]:
        rows = data.get("data", [])
        if not isinstance(rows, list):
            raise ValueError("Invalid embeddings payload: 'data' is not a list")
        vectors: list[list[float]] = []
        for item in rows:
            if not isinstance(item, dict):
                raise ValueError("Invalid embeddings payload item")
            embedding = item.get("embedding")
            if not isinstance(embedding, list):
                raise ValueError("Invalid embeddings payload: missing 'embedding'")
            vector = [float(x) for x in embedding]
            if len(vector) != self.dim:
                raise ValueError(f"Invalid vector dimension {len(vector)}, expected {self.dim}")
            vectors.append(vector)
        return vectors
