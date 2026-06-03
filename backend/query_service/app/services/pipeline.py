import asyncio
import re
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..clients import registry_client, rag_client
from ..config import get_settings
from ..models import ChatMessage, ChatSource


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

    try:
        await _set_status(session_factory, message_id, "enriching")
        try:
            enriched_query, _synonyms = await asyncio.wait_for(
                registry_client.enrich_query(user_query), timeout=15.0
            )
        except Exception:
            enriched_query = user_query

        await _set_status(session_factory, message_id, "searching")
        try:
            chunks = await asyncio.wait_for(
                rag_client.search(enriched_query, top_k=10),
                timeout=60.0,
            )
        except Exception:
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
        llm_text: str | None = None
        for attempt in range(3):
            try:
                if settings.MOCK_LLM_ENABLED:
                    await asyncio.sleep(0.3)
                    llm_text = _build_llm_mock(enriched_query, chunks)
                    break
                # TODO: LLM call
                llm_text = _build_llm_mock(enriched_query, chunks)
                break
            except Exception:
                if attempt < 2:
                    context_chunks = chunks[: max(1, len(chunks) - attempt)]
                    chunks = context_chunks
                    await asyncio.sleep(2 ** attempt * 2)

        if llm_text is None:
            await _set_status(session_factory, message_id, "failed")
            return

        await _set_status(session_factory, message_id, "enriching_citations")
        try:
            final_text = await asyncio.wait_for(
                asyncio.to_thread(_enrich_citations, llm_text, chunks),
                timeout=10.0,
            )
        except Exception:
            final_text = llm_text

        async with session_factory() as db:
            async with db.begin():
                await db.execute(
                    update(ChatMessage)
                    .where(ChatMessage.message_id == message_id)
                    .values(
                        content=final_text,
                        status="answered",
                        processing_time_ms=0,
                    )
                )
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

    except Exception:
        await _set_status(session_factory, message_id, "failed")
