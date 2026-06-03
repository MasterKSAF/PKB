from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import ChatMessage, ChatSource


async def save_user_message(db: AsyncSession, session_id: str, content: str) -> ChatMessage:
    msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


async def save_assistant_message(
    db: AsyncSession,
    session_id: str,
    answer_id: str,
    status: str,
    content: str | None,
    message: str | None,
    missing_fields: list | None,
    conflicts: list | None,
    answer_items: list,
    processing_time_ms: int,
    sources: list[dict],
) -> tuple["ChatMessage", list[ChatSource]]:
    msg = ChatMessage(
        session_id=session_id,
        answer_id=answer_id,
        role="assistant",
        status=status,
        content=content,
        message=message,
        missing_fields=missing_fields,
        conflicts=conflicts,
        answer_items=answer_items,
        model_used="mock-rag-v1",
        processing_time_ms=processing_time_ms,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)

    saved_sources: list[ChatSource] = []
    for s in sources:
        src = ChatSource(
            message_id=msg.message_id,
            fragment_id=s.get("fragment_id"),
            document_id=s.get("document_id", ""),
            document_title=s.get("document_title"),
            page_number=s.get("page_number") or s.get("page"),
            text=s.get("text") or s.get("fragment"),
            score=s.get("score"),
            page_preview_url=s.get("page_preview_url"),
            document_url=s.get("document_url"),
        )
        db.add(src)
        saved_sources.append(src)
    await db.flush()
    return msg, saved_sources


async def get_session_messages(db: AsyncSession, session_id: str, limit: int, before: str | None) -> tuple[list[ChatMessage], bool]:
    q = select(ChatMessage).options(selectinload(ChatMessage.sources)).where(ChatMessage.session_id == session_id)
    if before:
        anchor = await db.execute(select(ChatMessage.timestamp).where(ChatMessage.message_id == before))
        ts = anchor.scalar_one_or_none()
        if ts:
            q = q.where(ChatMessage.timestamp < ts)
    q = q.order_by(ChatMessage.timestamp.asc())
    result = await db.execute(q)
    all_msgs = result.scalars().all()
    if len(all_msgs) > limit:
        return all_msgs[-limit:], True
    return all_msgs, False
