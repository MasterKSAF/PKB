import asyncio
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..clients import registry_client, rag_client, llm_client
from ..config import get_settings
from ..models import ChatMessage, ChatSource

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Ты — ассистент по инженерным нормативно-техническим документам ПКБ. "
    "Отвечай строго на основе предоставленных фрагментов документов. "
    "Если во фрагментах нет ответа — прямо сообщи об этом, не домысливай. "
    "Указывай источник (наименование документа, пункт, страницу) для каждого утверждения."
)


async def _load_history(
    session_factory: async_sessionmaker,
    session_id: str,
    exclude_message_id: str,
    limit: int,
) -> list[dict]:
    async with session_factory() as db:
        rows = (await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.message_id != exclude_message_id,
                ChatMessage.content.is_not(None),
                ChatMessage.role.in_(("user", "assistant")),
            )
            .order_by(ChatMessage.timestamp.desc())
            .limit(limit)
        )).scalars().all()

    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


def _build_messages(
    history: list[dict],
    chunks: list[rag_client.Chunk],
    user_query: str,
) -> list[dict]:
    context_parts = [
        f"[{i}] «{c.document_title}», {c.clause}, стр. {c.page}:\n{c.content}"
        for i, c in enumerate(chunks, 1)
    ]
    context_block = "\n\n".join(context_parts)

    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"Фрагменты документов:\n{context_block}\n\nВопрос: {user_query}",
    })
    return messages


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _set_status(
    session_factory: async_sessionmaker,
    message_id: str,
    status: str,
) -> None:
    async with session_factory() as db:
        async with db.begin():
            await db.execute(
                update(ChatMessage)
                .where(ChatMessage.message_id == message_id)
                .values(status=status)
            )


def _build_llm_mock(query: str, chunks: list[rag_client.Chunk]) -> str:
    if not chunks:
        return "По данному запросу релевантные фрагменты в базе знаний не найдены."

    parts = []
    for i, chunk in enumerate(chunks[:3], 1):
        ref = f"(источник: «{chunk.document_title}», {chunk.clause}, стр. {chunk.page})"
        parts.append(f"{i}. {chunk.excerpt} {ref}")
    return "\n".join(parts)


def _enrich_citations(text: str, chunks: list[rag_client.Chunk]) -> str:
    for chunk in chunks:
        pattern = re.escape(chunk.document_title)
        replacement = (
            f"{chunk.document_title} %[document_id:{chunk.document_id}]%"
            f" %[section_id:{chunk.section_id}]%"
        )
        text = re.sub(pattern, replacement, text, count=1)
    return text


async def run_pipeline(
    session_factory: async_sessionmaker,
    message_id: str,
    session_id: str,
    user_query: str,
) -> None:
    settings = get_settings()
    logger.info("pipeline started", extra={"message_id": message_id, "session_id": session_id})

    try:
        await _set_status(session_factory, message_id, "enriching")
        enrichment_skipped = False
        try:
            enriched_query, _synonyms = await asyncio.wait_for(
                registry_client.enrich_query(user_query), timeout=30.0
            )
        except Exception:
            enriched_query = user_query
            enrichment_skipped = True
            logger.warning("query enrichment skipped", extra={"message_id": message_id})

        await _set_status(session_factory, message_id, "searching")
        try:
            chunks = await asyncio.wait_for(
                rag_client.search(enriched_query, top_k=10, valid_at=_utcnow().strftime("%Y-%m-%d")),
                timeout=60.0,
            )
        except Exception:
            logger.error("rag search failed", extra={"message_id": message_id}, exc_info=True)
            await _set_status(session_factory, message_id, "failed")
            async with session_factory() as db:
                async with db.begin():
                    await db.execute(
                        update(ChatMessage)
                        .where(ChatMessage.message_id == message_id)
                        .values(
                            content="Поиск временно недоступен. Попробуйте повторить запрос.",
                            status="failed",
                            processing_time_ms=0,
                        )
                    )
            return

        if not chunks:
            logger.info("no chunks found", extra={"message_id": message_id})
            await _set_status(session_factory, message_id, "answered")
            async with session_factory() as db:
                async with db.begin():
                    await db.execute(
                        update(ChatMessage)
                        .where(ChatMessage.message_id == message_id)
                        .values(
                            content="В базе знаний не найдено подтверждённых фрагментов по данному запросу.",
                            status="not_found",
                            processing_time_ms=0,
                        )
                    )
            return

        await _set_status(session_factory, message_id, "generating")
        history = await _load_history(
            session_factory, session_id, message_id, settings.LLM_HISTORY_LIMIT
        )
        llm_text: str | None = None
        for attempt in range(3):
            try:
                if settings.MOCK_LLM_ENABLED:
                    await asyncio.sleep(0.3)
                    llm_text = _build_llm_mock(enriched_query, chunks)
                    break
                messages = _build_messages(history, chunks, enriched_query)
                llm_text = await llm_client.complete(messages, cache_key=str(session_id))
                break
            except Exception:
                if attempt < 2:
                    chunks = chunks[: max(1, len(chunks) - attempt - 1)]
                    await asyncio.sleep(2 ** attempt * 2)

        if llm_text is None:
            logger.error("llm generation failed after retries", extra={"message_id": message_id})
            await _set_status(session_factory, message_id, "failed")
            return

        await _set_status(session_factory, message_id, "enriching_citations")
        try:
            final_text = await asyncio.wait_for(
                asyncio.to_thread(_enrich_citations, llm_text, chunks),
                timeout=30.0,
            )
        except Exception:
            final_text = llm_text

        async with session_factory() as db:
            async with db.begin():
                result = await db.execute(
                    update(ChatMessage)
                    .where(ChatMessage.message_id == message_id)
                    .values(
                        content=final_text,
                        status="answered",
                        processing_time_ms=0,
                        enrichment_skipped=enrichment_skipped,
                    )
                )
                if result.rowcount == 0:
                    logger.warning("pipeline: message deleted before finish, skipping sources", extra={"message_id": message_id})
                    return
                for chunk in chunks:
                    db.add(ChatSource(
                        message_id=message_id,
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        document_title=chunk.document_title,
                        section_id=chunk.section_id,
                        page_number=chunk.page,
                        clause=chunk.clause,
                        section_title=chunk.section_title,
                        excerpt=chunk.excerpt,
                        text=chunk.content,
                        score=chunk.score,
                        confidence=chunk.confidence,
                    ))

        logger.info("pipeline finished", extra={"message_id": message_id, "chunks": len(chunks)})

    except Exception:
        logger.error("pipeline error", extra={"message_id": message_id}, exc_info=True)
        await _set_status(session_factory, message_id, "failed")
