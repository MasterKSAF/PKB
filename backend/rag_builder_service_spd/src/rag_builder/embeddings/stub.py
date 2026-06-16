# src/rag_builder/embeddings/stub.py

from rag_builder.core.config import settings
from rag_builder.models.domain import EmbeddingResult


class StubEmbeddingProvider:
    """
    Тестовый провайдер эмбеддингов.

    Возвращает вектор из нулей нужной размерности.
    """

    def create_embedding(self, text: str) -> list[float]:
        return self.create_embedding_with_usage(text).embedding

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        return EmbeddingResult(
            embedding=[0.0] * settings.EMBEDDING_DIM,
            token_count=0,
            cost_usd=0.0,
       )

    def create_embeddings_with_usage(
            self,
            texts: list[str],
    ) -> list[EmbeddingResult]:
        return [
            EmbeddingResult(
                embedding=[0.0] * settings.EMBEDDING_DIM,
                token_count=0,
                cost_usd=0.0,
            )
            for _ in texts
        ]