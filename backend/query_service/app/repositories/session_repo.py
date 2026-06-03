from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ChatSession, ChatMessage


async def create_session(db: AsyncSession, user_id: str, title: str | None, document_ids: list, options: dict) -> ChatSession:
    session = ChatSession(user_id=user_id, title=title, document_ids=document_ids, options=options)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: str, user_id: str) -> ChatSession | None:
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id, ChatSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_sessions(db: AsyncSession, user_id: str, page: int, page_size: int, search: str | None) -> tuple[list[ChatSession], int]:
    q = select(ChatSession).where(ChatSession.user_id == user_id)
    if search:
        q = q.where(ChatSession.title.ilike(f"%{search}%"))
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    q = q.order_by(ChatSession.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return result.scalars().all(), total


async def update_session(db: AsyncSession, session: ChatSession, title: str | None, document_ids: list | None) -> ChatSession:
    if title is not None:
        session.title = title
    if document_ids is not None:
        session.document_ids = document_ids
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session: ChatSession) -> None:
    await db.delete(session)
    await db.flush()


async def message_count(db: AsyncSession, session_id: str) -> int:
    result = await db.execute(
        select(func.count()).where(ChatMessage.session_id == session_id)
    )
    return result.scalar_one()


async def last_assistant_message(db: AsyncSession, session_id: str) -> ChatMessage | None:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id, ChatMessage.role == "assistant")
        .order_by(ChatMessage.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
