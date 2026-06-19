import pytest


@pytest.mark.asyncio
async def test_feedback_session_format(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Feedback test"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "вопрос"})
    msg_id = r.json()["message_id"]
    r = await client.post("/api/v1/chat/feedback", json={
        "session_id": sid,
        "message_id": msg_id,
        "rating": 5,
        "rating_status": "positive",
        "comment": "Отлично!",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["saved"] is True
    assert "feedback_id" in data
    assert data["rating_status"] == "positive"


@pytest.mark.asyncio
async def test_feedback_ui_format(client):
    r = await client.post("/api/v1/chat", json={"question": "Вопрос для feedback"})
    answer_id = r.json()["answer_id"]
    r = await client.post("/api/v1/chat/feedback", json={
        "answer_id": answer_id,
        "useful": True,
        "comment": "Хороший ответ",
        "opened_citation_ids": ["cit-001"],
    })
    assert r.status_code == 200
    assert r.json()["saved"] is True


@pytest.mark.asyncio
async def test_feedback_rating_from_int(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Rating int test"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "вопрос"})
    msg_id = r.json()["message_id"]
    r = await client.post("/api/v1/chat/feedback", json={
        "session_id": sid,
        "message_id": msg_id,
        "rating": 2,
    })
    assert r.status_code == 200
    assert r.json()["rating_status"] == "negative"


@pytest.mark.asyncio
async def test_feedback_ambiguous_format(client):
    r = await client.post("/api/v1/chat/feedback", json={
        "session_id": 1,
        "answer_id": 1,
        "rating": 5,
    })
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["error"]["code"] == "AMBIGUOUS_FEEDBACK_FORMAT"


@pytest.mark.asyncio
async def test_feedback_invalid_rating(client):
    r = await client.post("/api/v1/chat/feedback", json={
        "session_id": 1,
        "rating": 10,
    })
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["error"]["code"] == "INVALID_RATING"


@pytest.mark.asyncio
async def test_feedback_invalid_rating_status(client):
    r = await client.post("/api/v1/chat/feedback", json={
        "session_id": 1,
        "rating": 4,
        "rating_status": "excellent",
    })
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["error"]["code"] == "INVALID_RATING"
