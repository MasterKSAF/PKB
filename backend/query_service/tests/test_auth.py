import pytest


@pytest.mark.asyncio
async def test_x_user_id_header_used_when_present(client):
    r = await client.post(
        "/api/v1/chat/sessions",
        json={"title": "auth test"},
        headers={"X-User-ID": "u-fad65ebbe463"},
    )
    assert r.status_code == 201
    assert r.json()["user_id"] == "u-fad65ebbe463"


@pytest.mark.asyncio
async def test_dev_user_id_fallback_without_header(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "dev fallback"})
    assert r.status_code == 201
    assert r.json()["user_id"] == "u-001"


@pytest.mark.asyncio
async def test_different_users_get_isolated_sessions(client):
    r1 = await client.post(
        "/api/v1/chat/sessions", json={"title": "user1"}, headers={"X-User-ID": "u-aaa"}
    )
    r2 = await client.post(
        "/api/v1/chat/sessions", json={"title": "user2"}, headers={"X-User-ID": "u-bbb"}
    )
    assert r1.json()["user_id"] == "u-aaa"
    assert r2.json()["user_id"] == "u-bbb"

    list_r1 = await client.get("/api/v1/chat/sessions", headers={"X-User-ID": "u-aaa"})
    session_ids = [s["session_id"] for s in list_r1.json()["sessions"]]
    assert r2.json()["session_id"] not in session_ids
