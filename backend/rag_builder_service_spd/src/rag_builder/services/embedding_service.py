# src/rag_builder/services/embedding_service.py

from rag_builder.embeddings.base import EmbeddingProvider
from rag_builder.embeddings.factory import build_embedding_provider
from rag_builder.models.domain import Chunk, EmbeddedChunk, EmbeddingResult

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