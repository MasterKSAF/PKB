from rag_search.embeddings.base import EmbeddingProvider, EmbeddingResult
from rag_search.embeddings.factory import build_embedding_provider


class EmbeddingService:
    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self.provider = provider or build_embedding_provider()

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        return self.provider.create_embedding_with_usage(text)

    def create_embedding(self, text: str) -> list[float]:
        return self.create_embedding_with_usage(text).embedding


__all__ = [
    "EmbeddingProvider",
    "EmbeddingResult",
    "EmbeddingService",
    "build_embedding_provider",
]
