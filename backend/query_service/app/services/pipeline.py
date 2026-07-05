import asyncio
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..clients import registry_client, rag_client, llm_client
from ..config import get_settings
from ..models import ChatMessage, ChatSession, ChatSource

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Ты — ассистент по инженерным нормативно-техническим документам ПКБ. "
    "Отвечай строго на основе предоставленных фрагментов документов. "
    "Если во фрагментах нет ответа — прямо сообщи об этом, не домысливай. "
    "После каждого утверждения, основанного на фрагменте, ставь ссылку в формате [source:N], "
    "где N — индекс фрагмента начиная с 0 (например: [source:0], [source:2]). "
    "Не пиши идентификаторы документов в тексте — только [source:N]."
)

_SUMMARY_PROMPT = (
    "Сожми переписку инженера с ассистентом в краткое резюме на русском: "
    "сохрани заданные вопросы, ключевые выводы, упомянутые документы и параметры. "
    "Без воды, только факты, необходимые для продолжения диалога."
)

_FINAL_ASSISTANT_STATUSES = ("answered", "not_found")
_SOURCE_REF_RE = re.compile(r"\[source:(\d+)\]")
_OLD_MARKER_RE = re.compile(r"\s*%\[[^\]]*\]%")

_ROUTER_PROMPT = (
    "Ты определяешь нужен ли поиск по инженерным документам для ответа на вопрос пользователя. "
    "Ответь одним словом: RAG — если нужен поиск по документам, CHAT — если можно ответить на основе истории диалога. "
    "Только одно слово, без объяснений."
)

_CHAT_SYSTEM_PROMPT = (
    "Ты — ассистент по инженерным нормативно-техническим документам ПКБ. "
    "Отвечай на вопрос на основе истории диалога. Будь краток и по делу."
)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _clean_content(role: str, content: str) -> str:
    if role == "assistant":
        content = _SOURCE_REF_RE.sub("", content)
        content = _OLD_MARKER_RE.sub("", content)
    return content


def _enrich_citations(
    llm_text: str, chunks: list[rag_client.Chunk]
) -> tuple[str, list[int]]:
    used_indices: list[int] = []
    seen: set[int] = set()

    def replace(m: re.Match) -> str:
        n = int(m.group(1))
        if n < 0 or n >= len(chunks):
            return ""
        chunk = chunks[n]
        if n not in seen:
            seen.add(n)
            used_indices.append(n)
        title = chunk.document_title or ""
        clause = f" §{chunk.clause}" if chunk.clause else ""
        page = f", стр. {chunk.page}" if chunk.page else ""
        return f"[document_id:{chunk.document_id}, section_id:{chunk.section_id}{clause}{page}]"

    enriched = _SOURCE_REF_RE.sub(replace, llm_text)
    return enriched, used_indices


async def _load_session_meta(
    session_factory: async_sessionmaker, session_id: str
) -> tuple[str | None, int | None]:
    async with session_factory() as db:
        session = await db.get(ChatSession, session_id)
        if session is None:
            return None, None
        return session.summary, session.summarized_until_message_id


async def _load_messages_after(
    session_factory: async_sessionmaker,
    session_id: str,
    exclude_message_id: str,
    after_id: int | None,
) -> list[dict]:
    async with session_factory() as db:
        q = select(ChatMessage).where(
            ChatMessage.session_id == session_id,
            ChatMessage.message_id != exclude_message_id,
            ChatMessage.content.is_not(None),
            ChatMessage.role.in_(("user", "assistant")),
            ChatMessage.status.in_(("pending",) + _FINAL_ASSISTANT_STATUSES),
        )
        if after_id is not None:
            q = q.where(ChatMessage.message_id > after_id)
        rows = (await db.execute(q.order_by(ChatMessage.message_id.asc()))).scalars().all()

    return [
        {"id": m.message_id, "role": m.role, "content": _clean_content(m.role, m.content)}
        for m in rows
    ]


async def _summarize(prev_summary: str | None, messages: list[dict], settings) -> str:
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    if settings.MOCK_LLM_ENABLED:
        base = f"{prev_summary} | " if prev_summary else ""
        return base + "; ".join(m["content"][:60] for m in messages)

    base = f"Текущее резюме:\n{prev_summary}\n\n" if prev_summary else ""
    prompt = [
        {"role": "system", "content": _SUMMARY_PROMPT},
        {"role": "user", "content": base + f"Добавь в резюме переписку:\n{convo}"},
    ]
    return await llm_client.complete(prompt, max_tokens=settings.LLM_SUMMARY_MAX_TOKENS)


async def _prepare_context(
    session_factory: async_sessionmaker,
    session_id: str,
    exclude_message_id: str,
    settings,
) -> tuple[str | None, list[dict]]:
    summary, until = await _load_session_meta(session_factory, session_id)
    history = await _load_messages_after(session_factory, session_id, exclude_message_id, until)

    budget = settings.LLM_CONTEXT_TOKEN_BUDGET
    keep = settings.LLM_RECENT_KEEP_MESSAGES

    def total_tokens() -> int:
        t = _estimate_tokens(summary) if summary else 0
        return t + sum(_estimate_tokens(m["content"]) for m in history)

    if total_tokens() > budget and len(history) > keep:
        to_compress = history[:-keep]
        summary = await _summarize(summary, to_compress, settings)
        last_id = to_compress[-1]["id"]
        async with session_factory() as db:
            async with db.begin():
                await db.execute(
                    update(ChatSession)
                    .where(ChatSession.session_id == session_id)
                    .values(summary=summary, summarized_until_message_id=last_id)
                )
        history = history[-keep:]

    return summary, [{"role": m["role"], "content": m["content"]} for m in history]


def _build_messages(
    summary: str | None,
    history: list[dict],
    chunks: list[rag_client.Chunk],
    user_query: str,
) -> list[dict]:
    context_parts = [
        f"[{i}] «{c.document_title}», {c.clause}, стр. {c.page}:\n{c.content}"
        for i, c in enumerate(chunks)
    ]
    context_block = "\n\n".join(context_parts)

    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if summary:
        messages.append({"role": "system", "content": f"Резюме предыдущего диалога:\n{summary}"})
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
    for i, chunk in enumerate(chunks[:3]):
        parts.append(f"{chunk.excerpt} [source:{i}]")
    return " ".join(parts)


async def _needs_rag(user_query: str, history: list[dict], settings) -> bool:
    if settings.MOCK_LLM_ENABLED:
        return True
    messages = [
        {"role": "system", "content": _ROUTER_PROMPT},
        *history[-4:],
        {"role": "user", "content": user_query},
    ]
    try:
        result = await asyncio.wait_for(
            llm_client.complete(messages, max_tokens=5),
            timeout=10.0,
        )
        return "CHAT" not in result.content.upper()
    except Exception:
        return True


async def _answer_from_chat(user_query: str, history: list[dict], summary: str | None, settings) -> llm_client.LLMResult:
    messages = [{"role": "system", "content": _CHAT_SYSTEM_PROMPT}]
    if summary:
        messages.append({"role": "system", "content": f"Резюме предыдущего диалога:\n{summary}"})
    messages.extend(history)
    messages.append({"role": "user", "content": user_query})
    return await llm_client.complete(messages)


async def run_pipeline(
    session_factory: async_sessionmaker,
    message_id: str,
    session_id: str,
    user_query: str,
) -> None:
    settings = get_settings()
    logger.info("pipeline started", extra={"message_id": message_id, "session_id": session_id})

    try:
        t_start = _utcnow()
        warnings: list[str] = []
        prompt_tokens: int = 0
        completion_tokens: int = 0
        await _set_status(session_factory, message_id, "enriching")
        enrichment_skipped = False
        try:
            enriched_query, _synonyms = await asyncio.wait_for(
                registry_client.enrich_query(user_query), timeout=30.0
            )
        except Exception as exc:
            enriched_query = user_query
            enrichment_skipped = True
            warnings.append("Обогащение терминов недоступно. Поиск выполнен без нормализации.")
            logger.warning("query enrichment skipped", extra={"message_id": message_id}, exc_info=True)

        await _set_status(session_factory, message_id, "generating")
        summary, history = await _prepare_context(
            session_factory, session_id, message_id, settings
        )

        use_rag = await _needs_rag(user_query, history, settings)
        logger.info("router decision use_rag=%s", use_rag, extra={"message_id": message_id})

        if not use_rag:
            try:
                llm_result = await asyncio.wait_for(
                    _answer_from_chat(user_query, history, summary, settings),
                    timeout=120.0,
                )
                processing_time_ms = int((_utcnow() - t_start).total_seconds() * 1000)
                async with session_factory() as db:
                    async with db.begin():
                        await db.execute(
                            update(ChatMessage)
                            .where(ChatMessage.message_id == message_id)
                            .values(
                                content=llm_result.content,
                                status="answered",
                                processing_time_ms=processing_time_ms,
                                prompt_tokens=llm_result.prompt_tokens or None,
                                completion_tokens=llm_result.completion_tokens or None,
                                model_used=settings.LLM_MODEL,
                                enrichment_skipped=enrichment_skipped,
                                warnings=warnings or None,
                            )
                        )
                logger.info("pipeline finished via chat", extra={"message_id": message_id})
                return
            except Exception:
                logger.warning("chat answer failed, falling back to RAG", extra={"message_id": message_id}, exc_info=True)

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

        llm_text: str | None = None
        for attempt in range(3):
            try:
                if settings.MOCK_LLM_ENABLED:
                    await asyncio.sleep(0.3)
                    llm_text = _build_llm_mock(enriched_query, chunks)
                    break
                messages = _build_messages(summary, history, chunks, enriched_query)
                result = await llm_client.complete(messages, cache_key=str(session_id))
                llm_text = result.content
                prompt_tokens = result.prompt_tokens
                completion_tokens = result.completion_tokens
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
            final_text, used_indices = await asyncio.wait_for(
                asyncio.to_thread(_enrich_citations, llm_text, chunks),
                timeout=30.0,
            )
        except Exception:
            warnings.append("Обогащение цитат недоступно.")
            logger.warning("citation enrichment skipped", extra={"message_id": message_id}, exc_info=True)
            final_text = llm_text
            used_indices = sorted({
                int(m.group(1)) for m in _SOURCE_REF_RE.finditer(llm_text)
                if int(m.group(1)) < len(chunks)
            })

        used_chunks = [chunks[i] for i in used_indices if i < len(chunks)] or chunks

        async with session_factory() as db:
            async with db.begin():
                processing_time_ms = int((_utcnow() - t_start).total_seconds() * 1000)
                result = await db.execute(
                    update(ChatMessage)
                    .where(ChatMessage.message_id == message_id)
                    .values(
                        content=final_text,
                        status="answered",
                        processing_time_ms=processing_time_ms,
                        prompt_tokens=prompt_tokens or None,
                        completion_tokens=completion_tokens or None,
                        model_used=settings.LLM_MODEL,
                        enrichment_skipped=enrichment_skipped,
                        warnings=warnings or None,
                    )
                )
                if result.rowcount == 0:
                    logger.warning("pipeline: message deleted before finish, skipping sources", extra={"message_id": message_id})
                    return
                for pos, chunk in enumerate(used_chunks, 1):
                    db.add(ChatSource(
                        message_id=message_id,
                        citation_index=pos,
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
