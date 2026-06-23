# tests/unit/test_embedding_factory.py

from rag_builder.core.config import settings
from rag_builder.embeddings.factory import build_embedding_provider
from rag_builder.embeddings.openai_provider import (
    OpenAICompatibleEmbeddingProvider,
    OpenAIEmbeddingProvider,
)
from rag_builder.embeddings.stub import StubEmbeddingProvider


def test_factory_builds_stub(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "stub")

    provider = build_embedding_provider()

    assert isinstance(provider, StubEmbeddingProvider)


def test_factory_builds_openai(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

    provider = build_embedding_provider()

    assert isinstance(provider, OpenAIEmbeddingProvider)


def test_factory_builds_openai_compatible(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "openai_compatible")
    monkeypatch.setattr(
        settings,
        "EMBEDDING_API_BASE_URL",
        "http://localhost:7997/v1",
    )

    provider = build_embedding_provider()

    assert isinstance(provider, OpenAICompatibleEmbeddingProvider)


def test_factory_builds_infinity(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "infinity")
    monkeypatch.setattr(
        settings,
        "EMBEDDING_API_BASE_URL",
        "http://localhost:7997/v1",
    )

    provider = build_embedding_provider()

    assert isinstance(provider, OpenAICompatibleEmbeddingProvider)


def test_factory_builds_external(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "external")
    monkeypatch.setattr(
        settings,
        "EMBEDDING_API_BASE_URL",
        "https://example.com/v1",
    )

    provider = build_embedding_provider()

    assert isinstance(provider, OpenAICompatibleEmbeddingProvider)


def test_factory_builds_openai_compatible_provider_aliases(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_API_KEY", "sk-noop")
    monkeypatch.setattr(settings, "EMBEDDING_API_BASE_URL", "http://127.0.0.1:18092/v1")
    monkeypatch.setattr(settings, "EMBEDDING_MODEL", "Vuy/rubert-tiny2-onnx")
    monkeypatch.setattr(settings, "EMBEDDING_DIM", 312)

    for provider_name in [
        "openai-compatible",
        "tei",
    ]:
        monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", provider_name)

        provider = build_embedding_provider()

        assert isinstance(provider, OpenAICompatibleEmbeddingProvider)
