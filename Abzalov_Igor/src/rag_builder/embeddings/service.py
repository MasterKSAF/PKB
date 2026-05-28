from __future__ import annotations

import hashlib
from loguru import logger

from rag_builder.core.config import settings


class EmbeddingService:
    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim if dim is not None else settings.embedding_dim

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        logger.info("Embeddings start count={} dim={}", len(texts), self.dim)
        vectors = [self._deterministic_embedding(t) for t in texts]
        logger.info("Embeddings done count={} dim={}", len(vectors), self.dim)
        return vectors

    def _deterministic_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = list(digest)
        vec = [((seed[i % len(seed)] / 255.0) * 2.0) - 1.0 for i in range(self.dim)]
        return vec
