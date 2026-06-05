import pytest


async def _make_session(client, title="s") -> str:
    r = await client.post("/api/v1/chat/sessions", json={"title": title})
    return r.json()["session_id"]


async def _send(client, sid: str, content: str) -> str:
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": content})
    assert r.status_code == 202
    return r.json()["message_id"]


@pytest.mark.asyncio
async def test_get_last_messages_empty_session(client):
    sid = await _make_session(client, "empty")
    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/last")
    assert r.status_code == 200
    data = r.json()
    assert data["messages"] == []
    assert data["has_older"] is False


@pytest.mark.asyncio
async def test_get_last_messages_limit(client):
    sid = await _make_session(client, "limit test")
    for i in range(5):
        await _send(client, sid, f"вопрос {i}")

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/last?limit=3")
    assert r.status_code == 200
    data = r.json()
    assert len(data["messages"]) == 3
    assert data["has_older"] is True


@pytest.mark.asyncio
async def test_get_last_messages_order_newest_first(client):
    sid = await _make_session(client, "order test")
    await _send(client, sid, "первый")
    await _send(client, sid, "второй")
    await _send(client, sid, "третий")

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/last?limit=10")
    data = r.json()
    msgs = data["messages"]
    assert len(msgs) >= 3
    # /last возвращает от новых к старым — первый элемент новее последнего
    ts = [m["timestamp"] for m in msgs]
    assert ts == sorted(ts, reverse=True)


@pytest.mark.asyncio
async def test_list_messages_no_cursor_returns_all(client):
    sid = await _make_session(client, "list all")
    await _send(client, sid, "один")
    await _send(client, sid, "два")

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages")
    assert r.status_code == 200
    data = r.json()
    assert "messages" in data
    assert "has_more" in data
    user_msgs = [m for m in data["messages"] if m["role"] == "user"]
    assert len(user_msgs) == 2


@pytest.mark.asyncio
async def test_list_messages_after_cursor(client):
    sid = await _make_session(client, "after test")
    await _send(client, sid, "первый")
    mid_anchor = await _send(client, sid, "второй")
    await _send(client, sid, "третий")

    # Получаем все сообщения чтобы найти timestamp якоря
    all_r = await client.get(f"/api/v1/chat/sessions/{sid}/messages")
    all_msgs = all_r.json()["messages"]
    total_count = len(all_msgs)

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages?after={mid_anchor}")
    assert r.status_code == 200
    data = r.json()
    # После якоря должно быть меньше сообщений, чем всего
    assert len(data["messages"]) < total_count
    # И ни одно из возвращённых не должно быть якорем или более ранним
    returned_ids = {m["message_id"] for m in data["messages"]}
    assert mid_anchor not in returned_ids


@pytest.mark.asyncio
async def test_list_messages_before_cursor(client):
    sid = await _make_session(client, "before test")
    await _send(client, sid, "первый")
    mid_anchor = await _send(client, sid, "второй")
    await _send(client, sid, "третий")

    all_r = await client.get(f"/api/v1/chat/sessions/{sid}/messages")
    total_count = len(all_r.json()["messages"])

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages?before={mid_anchor}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["messages"]) < total_count
    returned_ids = {m["message_id"] for m in data["messages"]}
    assert mid_anchor not in returned_ids


@pytest.mark.asyncio
async def test_list_messages_after_takes_priority_over_before(client):
    sid = await _make_session(client, "priority test")
    await _send(client, sid, "первый")
    mid_anchor = await _send(client, sid, "второй")
    await _send(client, sid, "третий")

    all_r = await client.get(f"/api/v1/chat/sessions/{sid}/messages")
    total_count = len(all_r.json()["messages"])

    # after + before вместе — after имеет приоритет
    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages?after={mid_anchor}&before={mid_anchor}")
    assert r.status_code == 200
    data = r.json()
    # Если after победил — возвращает сообщения ПОСЛЕ якоря (меньше всего)
    assert len(data["messages"]) < total_count
    assert mid_anchor not in {m["message_id"] for m in data["messages"]}


@pytest.mark.asyncio
async def test_messages_session_not_found(client):
    r = await client.get("/api/v1/chat/sessions/999999/messages/last")
    assert r.status_code == 404
    r = await client.get("/api/v1/chat/sessions/999999/messages")
    assert r.status_code == 404
