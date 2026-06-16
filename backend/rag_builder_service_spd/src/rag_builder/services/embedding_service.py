# src/rag_builder/services/embedding_service.py

from dataclasses import dataclass
from rag_builder.embeddings.base import EmbeddingProvider
from rag_builder.embeddings.factory import build_embedding_provider
from rag_builder.models.domain import Chunk, EmbeddedChunk, EmbeddingResult

@dataclass(frozen=True)
class EmbeddedChunksResult:
    chunks: list[EmbeddedChunk]
    token_count: int
    cost_usd: float

class EmbeddingService:
    """
    Сервис генерации эмбеддингов.
    """
    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self.provider = provider or build_embedding_provider()

    def create_embedding(self, text: str) -> list[float]:
        """
        Создает эмбеддинг текста.
        """

        return self.create_embedding_with_usage(text).embedding

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        return self.provider.create_embedding_with_usage(text)

    def enrich_chunk(self, chunk: Chunk) -> EmbeddedChunk:
        """
        Добавляет эмбеддинг к чанку.
        """

        return EmbeddedChunk(
            chunk=chunk,
            embedding=self.create_embedding(chunk.content),
        )

    def enrich_chunks(
            self,
            chunks: list[Chunk],
    ) -> EmbeddedChunksResult:
        texts = [
            chunk.content
            for chunk in chunks
        ]

        results = self.provider.create_embeddings_with_usage(
            texts
        )

        embedded_chunks = [
            EmbeddedChunk(
                chunk=chunk,
                embedding=result.embedding,
            )
            for chunk, result in zip(chunks, results)
        ]

        total_tokens = sum(
            result.token_count
            for result in results
        )

        total_cost = sum(
            result.cost_usd
            for result in results
        )

        return EmbeddedChunksResult(
            chunks=embedded_chunks,
            token_count=total_tokens,
            cost_usd=total_cost,
        )