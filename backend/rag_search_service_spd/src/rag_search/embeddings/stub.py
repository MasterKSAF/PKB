from rag_search.core.config import settings
from rag_search.embeddings.base import EmbeddingResult


class StubEmbeddingProvider:
    supports_dense = False

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        token_count = len(text.split())

        return EmbeddingResult(
            embedding=[0.0] * int(settings.EMBEDDING_DIM),
            token_count=token_count,
            cost_usd=0.0,
        )
