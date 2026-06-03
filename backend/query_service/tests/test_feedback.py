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
        "rating": "positive",
        "comment": "Отлично!",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["saved"] is True
    assert "feedback_id" in data


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
