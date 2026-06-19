import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models import ChatMessage

logger = logging.getLogger("query_service")

# сообщение считается зависшим если не менялось более 30с
_STATE_TIMEOUT = timedelta(seconds=30)
# абсолютный TTL — 48ч
_ABSOLUTE_TIMEOUT = timedelta(hours=48)
_PENDING_STATUSES = ("pending", "enriching", "searching", "generating", "enriching_citations")


async def _mark_stuck(session_factory: async_sessionmaker) -> None:
    cutoff_state = datetime.now(timezone.utc) - _STATE_TIMEOUT
    cutoff_abs = datetime.now(timezone.utc) - _ABSOLUTE_TIMEOUT

    async with session_factory() as db:
        async with db.begin():
            await db.execute(
                update(ChatMessage)
                .where(
                    ChatMessage.status.in_(_PENDING_STATUSES),
                    ChatMessage.timestamp < cutoff_state,
                )
                .values(status="failed", content="Обработка запроса прервана: превышено время ожидания.")
            )
            await db.execute(
                update(ChatMessage)
                .where(ChatMessage.timestamp < cutoff_abs)
                .values(status="failed", content="Сессия истекла.")
            )


async def run_watchdog(session_factory: async_sessionmaker) -> None:
    while True:
        try:
            await _mark_stuck(session_factory)
        except Exception as exc:
            logger.warning(f"pending_watchdog error: {exc}")
        await asyncio.sleep(15)
