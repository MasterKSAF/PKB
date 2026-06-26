import httpx
import pytest

from app.clients import llm_client, rag_client
from app.services import pipeline
from app.config import get_settings


async def _noop():
    return None


def _chunk(**kw):
    base = dict(
        chunk_id=1, document_id=1, document_title="ГОСТ 1", section_id=1,
        page=5, content="толщина не менее 12 мм", excerpt="12 мм", score=0.9,
        clause="4.2", section_title="Обшивка", confidence=0.8,
    )
    base.update(kw)
    return rag_client.Chunk(**base)


def test_build_messages_order_and_cache_friendly():
    history = [
        {"role": "user", "content": "первый вопрос"},
        {"role": "assistant", "content": "первый ответ"},
    ]
    chunks = [_chunk()]
    messages = pipeline._build_messages(history, chunks, "новый вопрос")

    assert messages[0]["role"] == "system"
    assert messages[1] == history[0]
    assert messages[2] == history[1]
    assert messages[-1]["role"] == "user"
    assert "новый вопрос" in messages[-1]["content"]
    assert "ГОСТ 1" in messages[-1]["content"]


@pytest.mark.asyncio
async def test_complete_sends_cache_key_and_params(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json
        captured["payload"] = json.loads(request.content)
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ответ"}}]})

    transport = httpx.MockTransport(handler)
    orig = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        kwargs["transport"] = transport
        return orig(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", fake_client)

    s = get_settings()
    monkeypatch.setattr(s, "MOCK_LLM_ENABLED", False)
    monkeypatch.setattr(s, "LLM_MODEL", "deepseek-chat")
    monkeypatch.setattr(s, "LLM_API_KEY", "test-key")

    msgs = [{"role": "user", "content": "вопрос"}]
    result = await llm_client.complete(msgs, cache_key="42")

    assert result == "ответ"
    assert captured["payload"]["user"] == "42"
    assert captured["payload"]["model"] == "deepseek-chat"
    assert captured["payload"]["messages"] == msgs
    assert captured["auth"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_complete_retries_then_fails(monkeypatch):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, json={"error": "boom"})

    transport = httpx.MockTransport(handler)
    orig = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        kwargs["transport"] = transport
        return orig(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", fake_client)
    monkeypatch.setattr(llm_client.asyncio, "sleep", lambda *a, **k: _noop())

    s = get_settings()
    monkeypatch.setattr(s, "MOCK_LLM_ENABLED", False)

    with pytest.raises(RuntimeError):
        await llm_client.complete([{"role": "user", "content": "x"}])
    assert calls["n"] == 3
