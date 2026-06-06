import pytest


@pytest.mark.asyncio
async def test_create_session(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Тест Arc4"})
    assert r.status_code == 201
    data = r.json()
    assert "session_id" in data
    assert data["title"] == "Тест Arc4"
    assert data["message_count"] == 0
    return data["session_id"]


@pytest.mark.asyncio
async def test_list_sessions(client):
    await client.post("/api/v1/chat/sessions", json={"title": "Сессия для списка"})
    r = await client.get("/api/v1/chat/sessions")
    assert r.status_code == 200
    data = r.json()
    assert "sessions" in data
    assert "meta" in data
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_get_session_messages(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Сессия с сообщениями"})
    sid = r.json()["session_id"]
    r = await client.get(f"/api/v1/chat/sessions/{sid}")
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == sid
    assert "messages" in data


@pytest.mark.asyncio
async def test_update_session(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Старое название"})
    sid = r.json()["session_id"]
    r = await client.put(f"/api/v1/chat/sessions/{sid}", json={"title": "Новое название"})
    assert r.status_code == 200
    assert r.json()["title"] == "Новое название"


@pytest.mark.asyncio
async def test_delete_session(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "На удаление"})
    sid = r.json()["session_id"]
    r = await client.delete(f"/api/v1/chat/sessions/{sid}")
    assert r.status_code == 200
    assert r.json()["session_id"] == sid
    r = await client.get(f"/api/v1/chat/sessions/{sid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_session_not_found(client):
    r = await client.get("/api/v1/chat/sessions/999999")
    assert r.status_code == 404
    data = r.json()
    assert "error" in data or "detail" in data
