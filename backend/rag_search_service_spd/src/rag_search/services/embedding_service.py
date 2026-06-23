from dataclasses import dataclass

from rag_search.core.config import settings


@dataclass(frozen=True)
class EmbeddingResult:
    embedding: list[float]
    token_count: int
    cost_usd: float


class StubEmbeddingProvider:
    supports_dense = False

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        token_count = len(text.split())

        return EmbeddingResult(
            embedding=[0.0] * int(settings.EMBEDDING_DIM),
            token_count=token_count,
            cost_usd=0.0,
        )


def build_embedding_provider():
    return StubEmbeddingProvider()
