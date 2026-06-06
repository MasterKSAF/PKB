from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ChatFeedback


async def save_feedback(
    db: AsyncSession,
    user_id: str,
    message_id: str | None,
    answer_id: str | None,
    rating: str | None,
    useful: bool | None,
    comment: str | None,
    aspects: list | None,
    opened_citation_ids: list | None,
) -> ChatFeedback:
    fb = ChatFeedback(
        user_id=user_id,
        message_id=message_id,
        answer_id=answer_id,
        rating=rating,
        useful=useful,
        comment=comment,
        aspects=aspects,
        opened_citation_ids=opened_citation_ids,
    )
    db.add(fb)
    await db.flush()
    await db.refresh(fb)
    return fb
