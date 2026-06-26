# tests/unit/test_openai_compatible_provider.py

import pytest

from rag_builder.core.config import settings
from rag_builder.embeddings.openai_provider import (
    OpenAICompatibleEmbeddingProvider,
)


class FakeUsage:
    total_tokens = 12


class FakeEmbeddingItem:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding


class FakeEmbeddingResponse:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.data = [
            FakeEmbeddingItem(embedding)
            for embedding in embeddings
        ]
        self.usage = FakeUsage()


class FakeEmbeddingsClient:
    def __init__(self, embedding_dim: int) -> None:
        self.embedding_dim = embedding_dim
        self.calls = []

    def create(
        self,
        model: str,
        input,
        dimensions: int | None = None,
    ):
        self.calls.append(
            {
                "model": model,
                "input": input,
                "dimensions": dimensions,
            }
        )

        inputs = input if isinstance(input, list) else [input]

        return FakeEmbeddingResponse(
            embeddings=[
                [0.1] * self.embedding_dim
                for _ in inputs
            ]
        )


class FakeOpenAIClient:
    def __init__(self, embedding_dim: int) -> None:
        self.embeddings = FakeEmbeddingsClient(embedding_dim)


def test_openai_compatible_single_embedding():
    client = FakeOpenAIClient(settings.EMBEDDING_DIM)

    provider = OpenAICompatibleEmbeddingProvider(client=client)

    result = provider.create_embedding_with_usage("ГОСТ 20868-81")

    assert len(result.embedding) == settings.EMBEDDING_DIM
    assert result.token_count == 12
    assert result.cost_usd == pytest.approx(
        (12 / 1_000_000) * settings.EMBEDDING_PRICE_PER_1M_TOKENS_USD
    )

    assert client.embeddings.calls[0]["model"] == settings.EMBEDDING_MODEL
    assert client.embeddings.calls[0]["dimensions"] == settings.EMBEDDING_DIM
    assert client.embeddings.calls[0]["input"] == "ГОСТ 20868-81"


def test_openai_compatible_batch_embeddings():
    client = FakeOpenAIClient(settings.EMBEDDING_DIM)

    provider = OpenAICompatibleEmbeddingProvider(client=client)

    results = provider.create_embeddings_with_usage(
        [
            "первый текст",
            "второй текст",
        ]
    )

    assert len(results) == 2
    assert all(
        len(result.embedding) == settings.EMBEDDING_DIM
        for result in results
    )
    assert all(result.token_count == 6 for result in results)


def test_openai_compatible_dimension_mismatch():
    client = FakeOpenAIClient(settings.EMBEDDING_DIM - 1)

    provider = OpenAICompatibleEmbeddingProvider(client=client)

    with pytest.raises(ValueError, match="Embedding dimension mismatch"):
        provider.create_embedding_with_usage("bad dim")


def test_openai_compatible_empty_batch():
    client = FakeOpenAIClient(settings.EMBEDDING_DIM)

    provider = OpenAICompatibleEmbeddingProvider(client=client)

    assert provider.create_embeddings_with_usage([]) == []


def test_openai_compatible_requires_base_url_without_client(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_API_BASE_URL", None)
    monkeypatch.setattr(settings, "EMBEDDING_BASE_URL", None)
    monkeypatch.setattr(settings, "EMBEDDING_API_URL", None)

    with pytest.raises(ValueError, match="EMBEDDING_API_BASE_URL"):
        OpenAICompatibleEmbeddingProvider()
