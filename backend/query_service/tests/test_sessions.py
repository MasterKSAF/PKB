import pytest


@pytest.mark.asyncio
async def test_create_session(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Тест Arc4"})
    assert r.status_code == 201
    data = r.json()
    assert "session_id" in data
    assert data["title"] == "Тест Arc4"
    assert "message_count" not in data
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
    if data["sessions"]:
        item = data["sessions"][0]
        assert "message_count" not in item
        assert "last_message_preview" in item


@pytest.mark.asyncio
async def test_get_session_messages(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Сессия с сообщениями"})
    sid = r.json()["session_id"]
    r = await client.get(f"/api/v1/chat/sessions/{sid}")
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == sid
    assert "messages" in data
    assert "project_id" in data


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
    assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_export_session_returns_export_response(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Экспорт тест"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/export", json={"format": "json"})
    assert r.status_code == 200
    data = r.json()
    assert "export_id" in data
    assert data["session_id"] == sid
    assert data["format"] == "json"
    assert data["status"] == "completed"
    assert "url" in data


@pytest.mark.asyncio
async def test_export_session_not_found(client):
    r = await client.post("/api/v1/chat/sessions/999999/export", json={"format": "json"})
    assert r.status_code == 404
