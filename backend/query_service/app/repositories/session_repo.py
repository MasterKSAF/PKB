from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ChatSession, ChatMessage


async def create_session(
    db: AsyncSession,
    user_id: str,
    title: str | None,
    document_ids: list,
    options: dict,
    project_id: int | None = None,
) -> ChatSession:
    session = ChatSession(
        user_id=user_id,
        title=title,
        document_ids=document_ids,
        options=options,
        project_id=project_id,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: int, user_id: str) -> ChatSession | None:
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id, ChatSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    user_id: str,
    page: int,
    page_size: int,
    search: str | None,
    project_id: int | None = None,
) -> tuple[list[ChatSession], int]:
    q = select(ChatSession).where(ChatSession.user_id == user_id)
    if search:
        q = q.where(ChatSession.title.ilike(f"%{search}%"))
    if project_id is not None:
        q = q.where(ChatSession.project_id == project_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(ChatSession.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return (await db.execute(q)).scalars().all(), total


async def update_session(
    db: AsyncSession,
    session: ChatSession,
    title: str | None,
    document_ids: list | None,
    project_id: int | None = None,
) -> ChatSession:
    if title is not None:
        session.title = title
    if document_ids is not None:
        session.document_ids = document_ids
    if project_id is not None:
        session.project_id = project_id
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session: ChatSession) -> None:
    await db.delete(session)
    await db.flush()


async def message_count(db: AsyncSession, session_id: int) -> int:
    result = await db.execute(
        select(func.count()).where(ChatMessage.session_id == session_id)
    )
    return result.scalar_one()


async def last_assistant_message(db: AsyncSession, session_id: int) -> ChatMessage | None:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id, ChatMessage.role == "assistant")
        .order_by(ChatMessage.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
