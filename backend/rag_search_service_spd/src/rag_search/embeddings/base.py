from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmbeddingResult:
    embedding: list[float]
    token_count: int
    cost_usd: float


class EmbeddingProvider(Protocol):
    supports_dense: bool

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        raise NotImplementedError
