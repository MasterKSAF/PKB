from __future__ import annotations

from collections import deque
from typing import Any

import pytest

from rag_builder.core import config as config_module
from rag_builder.embeddings.service import EmbeddingService


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http error {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeClient:
    responses: deque[_FakeResponse] = deque()
    requests: list[dict[str, Any]] = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        return None

    async def post(self, url: str, headers: dict[str, str], json: dict[str, object]) -> _FakeResponse:
        self.requests.append({"url": url, "headers": headers, "json": json})
        if not self.responses:
            raise RuntimeError("No fake responses left")
        return self.responses.popleft()


@pytest.mark.asyncio
async def test_openai_compatible_embeddings_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "embedding_provider", "openai_compatible")
    monkeypatch.setattr(config_module.settings, "embedding_retries", 0)
    monkeypatch.setattr(config_module.settings, "embedding_batch_size", 16)
    _FakeClient.requests = []
    _FakeClient.responses = deque(
        [_FakeResponse(200, {"data": [{"embedding": [0.1, 0.2, 0.3]}]})]
    )
    monkeypatch.setattr("rag_builder.embeddings.service.httpx.AsyncClient", _FakeClient)
    svc = EmbeddingService(dim=3)
    vectors = await svc.embed_many(["hello"])
    assert vectors == [[0.1, 0.2, 0.3]]
    assert len(_FakeClient.requests) == 1


@pytest.mark.asyncio
async def test_openai_compatible_embeddings_retry_and_batching(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "embedding_provider", "openai_compatible")
    monkeypatch.setattr(config_module.settings, "embedding_retries", 1)
    monkeypatch.setattr(config_module.settings, "embedding_batch_size", 2)
    _FakeClient.requests = []
    _FakeClient.responses = deque(
        [
            _FakeResponse(429, {"error": "rate_limited"}),
            _FakeResponse(
                200,
                {"data": [{"embedding": [1.0, 1.0, 1.0]}, {"embedding": [2.0, 2.0, 2.0]}]},
            ),
            _FakeResponse(200, {"data": [{"embedding": [3.0, 3.0, 3.0]}]}),
        ]
    )
    monkeypatch.setattr("rag_builder.embeddings.service.httpx.AsyncClient", _FakeClient)
    svc = EmbeddingService(dim=3)
    vectors = await svc.embed_many(["a", "b", "c"])
    assert vectors == [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]
    # 1-я пачка: retry (2 запроса), 2-я пачка: 1 запрос
    assert len(_FakeClient.requests) == 3


@pytest.mark.asyncio
async def test_openai_compatible_embeddings_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "embedding_provider", "openai_compatible")
    monkeypatch.setattr(config_module.settings, "embedding_retries", 0)
    monkeypatch.setattr(config_module.settings, "embedding_batch_size", 8)
    _FakeClient.requests = []
    _FakeClient.responses = deque([_FakeResponse(500, {"error": "boom"})])
    monkeypatch.setattr("rag_builder.embeddings.service.httpx.AsyncClient", _FakeClient)
    svc = EmbeddingService(dim=3)
    with pytest.raises(Exception):
        await svc.embed_many(["hello"])


def test_parse_embeddings_dimension_error() -> None:
    svc = EmbeddingService(dim=3)
    with pytest.raises(ValueError):
        svc._parse_openai_embeddings({"data": [{"embedding": [1.0, 2.0]}]})
