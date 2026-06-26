import pytest

from app.services import pipeline
from app.config import get_settings
from app.models import ChatSession, ChatMessage


async def _seed_session(factory, n_pairs: int) -> int:
    async with factory() as db:
        async with db.begin():
            s = ChatSession(user_id="u-001", document_ids=[], options={})
            db.add(s)
            await db.flush()
            sid = s.session_id
            for i in range(n_pairs):
                db.add(ChatMessage(
                    session_id=sid, role="user", status="pending",
                    content=f"вопрос номер {i} " + "x" * 80,
                ))
                db.add(ChatMessage(
                    session_id=sid, role="assistant", status="answered",
                    content=f"ответ номер {i} " + "y" * 80,
                ))
    return sid


@pytest.mark.asyncio
async def test_summarization_triggers_on_overflow(app, monkeypatch):
    from app.db import get_session_factory
    factory = get_session_factory()
    sid = await _seed_session(factory, 8)

    s = get_settings()
    monkeypatch.setattr(s, "MOCK_LLM_ENABLED", True)
    monkeypatch.setattr(s, "LLM_CONTEXT_TOKEN_BUDGET", 200)
    monkeypatch.setattr(s, "LLM_RECENT_KEEP_MESSAGES", 4)

    summary, history = await pipeline._prepare_context(factory, sid, "0", s)

    assert summary is not None
    assert len(history) == 4

    async with factory() as db:
        row = await db.get(ChatSession, sid)
        assert row.summary is not None
        assert row.summarized_until_message_id is not None


@pytest.mark.asyncio
async def test_append_only_no_resummarize_within_budget(app, monkeypatch):
    from app.db import get_session_factory
    factory = get_session_factory()
    sid = await _seed_session(factory, 8)

    s = get_settings()
    monkeypatch.setattr(s, "MOCK_LLM_ENABLED", True)
    monkeypatch.setattr(s, "LLM_CONTEXT_TOKEN_BUDGET", 200)
    monkeypatch.setattr(s, "LLM_RECENT_KEEP_MESSAGES", 4)

    await pipeline._prepare_context(factory, sid, "0", s)
    async with factory() as db:
        until_1 = (await db.get(ChatSession, sid)).summarized_until_message_id

    monkeypatch.setattr(s, "LLM_CONTEXT_TOKEN_BUDGET", 100000)
    summary, history = await pipeline._prepare_context(factory, sid, "0", s)

    async with factory() as db:
        until_2 = (await db.get(ChatSession, sid)).summarized_until_message_id

    assert until_2 == until_1
    assert summary is not None
    assert len(history) == 4
