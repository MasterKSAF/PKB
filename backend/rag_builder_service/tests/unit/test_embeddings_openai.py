from __future__ import annotations

import pytest

from rag_builder.core import config as config_module
from rag_builder.embeddings.service import EmbeddingService


class _OkResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}


class _BadResponse:
    def raise_for_status(self) -> None:
        raise RuntimeError("http error")

    def json(self) -> dict[str, object]:
        return {}


class _ClientOk:
    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "_ClientOk":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        return None

    async def post(self, url: str, headers: dict[str, str], json: dict[str, object]) -> _OkResponse:
        assert url
        assert "model" in json
        return _OkResponse()


class _ClientBad:
    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "_ClientBad":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        return None

    async def post(self, url: str, headers: dict[str, str], json: dict[str, object]) -> _BadResponse:
        return _BadResponse()


@pytest.mark.asyncio
async def test_openai_compatible_embeddings_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "embedding_provider", "openai_compatible")
    monkeypatch.setattr(config_module.settings, "embedding_retries", 0)
    monkeypatch.setattr("rag_builder.embeddings.service.httpx.AsyncClient", _ClientOk)
    svc = EmbeddingService(dim=3)
    vectors = await svc.embed_many(["hello"])
    assert vectors == [[0.1, 0.2, 0.3]]


@pytest.mark.asyncio
async def test_openai_compatible_embeddings_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "embedding_provider", "openai_compatible")
    monkeypatch.setattr(config_module.settings, "embedding_retries", 0)
    monkeypatch.setattr("rag_builder.embeddings.service.httpx.AsyncClient", _ClientBad)
    svc = EmbeddingService(dim=3)
    with pytest.raises(RuntimeError):
        await svc.embed_many(["hello"])


def test_parse_embeddings_dimension_error() -> None:
    svc = EmbeddingService(dim=3)
    with pytest.raises(ValueError):
        svc._parse_openai_embeddings({"data": [{"embedding": [1.0, 2.0]}]})
