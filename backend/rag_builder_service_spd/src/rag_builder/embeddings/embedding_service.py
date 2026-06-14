# src/rag_builder/services/embedding_service.py

from rag_builder.embeddings.base import EmbeddingProvider
from rag_builder.embeddings.factory import build_embedding_provider
from rag_builder.models.domain import Chunk, EmbeddedChunk


class EmbeddingService:
    """
    Сервис генерации эмбеддингов.

    Не знает, какая именно модель используется.
    Работает через EmbeddingProvider.
    """

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self.provider = provider or build_embedding_provider()

    def create_embedding(self, text: str) -> list[float]:
        return self.provider.create_embedding(text)

    def enrich_chunk(self, chunk: Chunk) -> EmbeddedChunk:
        return EmbeddedChunk(
            chunk=chunk,
            embedding=self.create_embedding(chunk.content),
        )

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
