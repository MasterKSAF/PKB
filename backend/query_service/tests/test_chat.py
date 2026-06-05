import asyncio
import pytest
from app.mocks import rag_responses


@pytest.mark.asyncio
async def test_send_message_to_session(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Чат тест"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "Какая толщина обшивки Arc4?"})
    assert r.status_code == 202
    data = r.json()
    assert data["session_id"] == sid
    assert data["status"] == "pending"
    assert "message_id" in data


@pytest.mark.asyncio
async def test_post_chat_auto_creates_session(client):
    r = await client.post("/api/v1/chat", json={"question": "Какой минимальный размер?", "session_id": None})
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert "answer_id" in data
    assert data["status"] in ("answered", "needs_clarification", "source_conflict", "pending")


@pytest.mark.asyncio
async def test_post_chat_reuses_session(client):
    r = await client.post("/api/v1/chat", json={"question": "Первый вопрос"})
    sid = r.json()["session_id"]
    r = await client.post("/api/v1/chat", json={"question": "Второй вопрос", "session_id": sid})
    assert r.status_code == 200
    assert r.json()["session_id"] == sid


@pytest.mark.asyncio
async def test_answered_response_has_sources(client):
    # Сбрасываем цикл к answered, отправив несколько запросов
    for _ in range(6):  # цикл: answered, answered, needs_clarification, answered, source_conflict, answered
        r = await client.post("/api/v1/chat", json={"question": "Тест источников"})
        data = r.json()
        if data["status"] == "answered":
            assert len(data["answer_items"]) > 0
            assert len(data["answer_items"][0]["citations"]) > 0
            cite = data["answer_items"][0]["citations"][0]
            assert "document_id" in cite
            assert "page" in cite
            break


@pytest.mark.asyncio
async def test_needs_clarification_response(client):
    for _ in range(6):
        r = await client.post("/api/v1/chat", json={"question": "Тест уточнений"})
        data = r.json()
        if data["status"] == "needs_clarification":
            assert data["message"] is not None
            assert isinstance(data.get("missing_fields"), list)
            break


@pytest.mark.asyncio
async def test_source_conflict_response(client):
    for _ in range(6):
        r = await client.post("/api/v1/chat", json={"question": "Тест конфликта"})
        data = r.json()
        if data["status"] == "source_conflict":
            assert data["message"] is not None
            assert isinstance(data.get("conflicts"), list)
            assert len(data["conflicts"]) >= 2
            break


@pytest.mark.asyncio
async def test_send_message_returns_202_with_role_and_content(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Тест 202"})
    sid = r.json()["session_id"]
    content = "Проверь толщину обшивки Arc4"
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": content})
    assert r.status_code == 202
    data = r.json()
    assert data["role"] == "user"
    assert data["content"] == content
    assert data["status"] == "pending"
    assert data["session_id"] == sid
    assert "message_id" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_message_transitions_to_answered(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Тест pipeline"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "Arc4 толщина?"})
    mid = r.json()["message_id"]

    await asyncio.sleep(2.0)

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/{mid}")
    assert r.status_code == 200
    msg = r.json()["message"]
    assert msg["status"] in ("answered", "not_found", "failed")
    if msg["status"] == "answered":
        assert msg["content"] is not None
        assert len(msg["content"]) > 0


@pytest.mark.asyncio
async def test_longpoll_returns_final_status(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Longpoll тест"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "Arc4?"})
    mid = r.json()["message_id"]

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/{mid}?longpoll=10")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert data["message"]["status"] in ("answered", "not_found", "failed")


@pytest.mark.asyncio
async def test_get_message_by_id_no_longpoll(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Get message"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "вопрос"})
    mid = r.json()["message_id"]

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/{mid}")
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == sid
    assert data["message"]["message_id"] == mid


@pytest.mark.asyncio
async def test_get_message_not_found(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "s"})
    sid = r.json()["session_id"]
    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/999999")
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "MESSAGE_NOT_FOUND"
