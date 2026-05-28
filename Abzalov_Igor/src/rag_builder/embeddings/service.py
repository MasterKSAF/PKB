from __future__ import annotations

import hashlib
import asyncio
from typing import Any

import httpx
from loguru import logger

from rag_builder.core.config import settings


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
        if settings.embedding_provider == "openai_compatible":
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

        payload = {"model": settings.embedding_model, "input": texts}
        attempts = settings.embedding_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                logger.info(
                    "Embedding API request attempt={} url={} model={}",
                    attempt,
                    settings.embedding_api_url,
                    settings.embedding_model,
                )
                async with httpx.AsyncClient(timeout=settings.embedding_timeout) as client:
                    response = await client.post(settings.embedding_api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                vectors = self._parse_openai_embeddings(data)
                logger.info("Embedding API response ok vectors={}", len(vectors))
                return vectors
            except Exception as exc:
                last_error = exc
                logger.exception("Embedding API call failed attempt={}", attempt)
                if attempt < attempts:
                    await asyncio.sleep(2 ** (attempt - 1))

        if last_error is not None:
            raise last_error
        raise RuntimeError("Embedding API failed without explicit error")

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
