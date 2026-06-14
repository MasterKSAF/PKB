# src/rag_builder/embeddings/base.py

from typing import Protocol


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