# src/rag_builder/embeddings/base.py

from typing import Protocol
from rag_builder.models.domain import EmbeddingResult


class EmbeddingProvider(Protocol):
    """
    Интерфейс любого провайдера эмбеддингов.

    Реализации:
    - stub
    - openai
    - local
    """
    def create_embedding(self, text: str) -> list[float]:
        ...

    def create_embedding_with_usage(
            self,
            text: str,
    ) -> EmbeddingResult:
        ...

    def create_embeddings_with_usage(
            self,
            texts: list[str],
    ) -> list[EmbeddingResult]:
        ...