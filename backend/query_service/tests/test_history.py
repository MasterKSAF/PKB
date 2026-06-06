import pytest


@pytest.mark.asyncio
async def test_get_history(client):
    await client.post("/api/v1/chat", json={"question": "Вопрос для истории"})
    r = await client.get("/api/v1/chat/history")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["total"] >= 1
    item = data["items"][0]
    assert "history_id" in item
    assert "session_id" in item
    assert "status" in item
    assert "user_id" in item


@pytest.mark.asyncio
async def test_history_export(client):
    r = await client.get("/api/v1/chat/history/export")
    assert r.status_code == 200
    data = r.json()
    assert "export_id" in data
    assert data["format"] == "xlsx"
    assert "url" in data
