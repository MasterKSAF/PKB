from datetime import datetime, timedelta, timezone

import pytest

from app.services.pending_watchdog import _mark_stuck
from app.models import ChatSession, ChatMessage


def _old() -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=5)


@pytest.mark.asyncio
async def test_watchdog_does_not_touch_user_or_answered(app):
    from app.db import get_session_factory
    factory = get_session_factory()

    async with factory() as db:
        async with db.begin():
            s = ChatSession(user_id="u-001", document_ids=[], options={})
            db.add(s)
            await db.flush()
            sid = s.session_id
            user_msg = ChatMessage(session_id=sid, role="user", status="pending",
                                   content="вопрос пользователя", timestamp=_old())
            answered = ChatMessage(session_id=sid, role="assistant", status="answered",
                                   content="готовый ответ", timestamp=_old())
            stuck = ChatMessage(session_id=sid, role="assistant", status="searching",
                               content=None, timestamp=_old())
            db.add_all([user_msg, answered, stuck])
            await db.flush()
            uid, aid, stid = user_msg.message_id, answered.message_id, stuck.message_id

    await _mark_stuck(factory)

    async with factory() as db:
        u = await db.get(ChatMessage, uid)
        a = await db.get(ChatMessage, aid)
        st = await db.get(ChatMessage, stid)

    assert u.status == "pending"
    assert u.content == "вопрос пользователя"
    assert a.status == "answered"
    assert a.content == "готовый ответ"
    assert st.status == "failed"
