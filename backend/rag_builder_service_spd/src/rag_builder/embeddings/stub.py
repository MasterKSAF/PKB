# src/rag_builder/embeddings/stub.py

from rag_builder.core.config import settings


class StubEmbeddingProvider:
    """
    Тестовый провайдер эмбеддингов.

    Возвращает вектор из нулей нужной размерности.
    """

    def create_embedding(self, text: str) -> list[float]:
        return [0.0] * settings.EMBEDDING_DIM