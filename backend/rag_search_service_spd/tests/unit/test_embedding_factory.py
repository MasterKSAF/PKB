import pytest

from rag_search.embeddings.factory import build_embedding_provider
from rag_search.embeddings.openai_provider import OpenAICompatibleEmbeddingProvider
from rag_search.embeddings.stub import StubEmbeddingProvider


def test_build_stub_embedding_provider() -> None:
    provider = build_embedding_provider(provider_name="stub")

    assert isinstance(provider, StubEmbeddingProvider)
    assert provider.supports_dense is False


def test_stub_embedding_provider_returns_configured_dim() -> None:
    provider = build_embedding_provider(provider_name="stub")

    result = provider.create_embedding_with_usage("допуск соосности")

    assert len(result.embedding) > 0
    assert result.token_count == 2
    assert result.cost_usd == 0.0


def test_build_openai_compatible_embedding_provider_without_network_call() -> None:
    provider = build_embedding_provider(
        provider_name="openai-compatible",
        api_key="sk-test",
        base_url="http://127.0.0.1:9999/v1",
        model="test-model",
        embedding_dim=3,
    )

    assert isinstance(provider, OpenAICompatibleEmbeddingProvider)
    assert provider.supports_dense is True


def test_build_tei_embedding_provider_without_network_call() -> None:
    provider = build_embedding_provider(
        provider_name="tei",
        api_key="sk-noop",
        base_url="http://tei:80/v1",
        model="Vuy/rubert-tiny2-onnx",
        embedding_dim=312,
    )

    assert isinstance(provider, OpenAICompatibleEmbeddingProvider)
    assert provider.supports_dense is True


def test_unsupported_embedding_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported EMBEDDING_PROVIDER"):
        build_embedding_provider(provider_name="unknown")
