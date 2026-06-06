import pytest


@pytest.mark.asyncio
async def test_text_search(client):
    r = await client.post("/api/v1/text/search", json={"text": "толщина обшивки Arc4"})
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert "analysis" in data
    assert data["analysis"]["normalized_query"]
    assert len(data["results"]) > 0
    result = data["results"][0]
    assert "document_id" in result
    assert "page" in result
    assert "content" in result
    assert "score" in result
    assert "section_id" in result


@pytest.mark.asyncio
async def test_text_ask(client):
    r = await client.post("/api/v1/text/ask", json={"text": "Какая сталь нужна для кницы по ГОСТ?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "sources" in data
    assert "disclaimer" in data
    assert len(data["sources"]) > 0
    src = data["sources"][0]
    assert "document_id" in src
    assert "page_number" in src


@pytest.mark.asyncio
async def test_error_format(client):
    r = await client.get("/api/v1/chat/sessions/999999")
    assert r.status_code == 404
    body = r.json()
    # Должен быть либо detail.error либо error напрямую
    assert "detail" in body or "error" in body


@pytest.mark.asyncio
async def test_db_tables_exist(client):
    from app.db import engine
    from sqlalchemy import inspect, text
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = {row[0] for row in result.fetchall()}
    expected = {"chat_sessions", "chat_messages", "chat_sources", "chat_feedback", "chat_exports"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"
