import asyncio
import json
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
    "У тебя есть инструмент rag_search для поиска по документам. "
    "Используй его когда нужна конкретная техническая информация из нормативных документов. "
    "Если вопрос можно решить на основе истории диалога — отвечай напрямую без поиска. "
    "Если поиск не вернул результатов — сообщи коротко: «В документах ПКБ не найдена информация по данному запросу.» "
    "Не задавай уточняющих вопросов, не используй общие знания, не предлагай альтернатив — только документы. "
    "После каждого утверждения, основанного на найденном фрагменте, ставь ссылку [source:N], "
    "где N — индекс фрагмента из результата поиска начиная с 0. "
    "Не объединяй индексы через запятую или дефис — используй отдельные [source:N] для каждого фрагмента. "
    "Не пиши идентификаторы документов в тексте — только [source:N]. "
    "Не используй LaTeX, Markdown и HTML — пиши обычным текстом. "
    "Химические формулы записывай буквами и цифрами без спецсимволов: CF3CH2F, а не $\\text{CF}_3$."
)

_SUMMARY_PROMPT = (
    "Сожми переписку инженера с ассистентом в краткое резюме на русском: "
    "сохрани заданные вопросы, ключевые выводы, упомянутые документы и параметры. "
    "Без воды, только факты, необходимые для продолжения диалога."
)

_FINAL_ASSISTANT_STATUSES = ("answered", "not_found")
_SOURCE_REF_RE = re.compile(r"\[source:(\d+)\]")
_SOURCE_REF_COMBINED_RE = re.compile(r"\[source:\s*(\d+(?:\s*,\s*\d+)*)\s*\]")
_SOURCE_REF_RANGE_RE = re.compile(r"\[source:(\d+)-(\d+)\]")
_OLD_MARKER_RE = re.compile(r"\s*%\[[^\]]*\]%")

_RAG_TOOL = {
    "type": "function",
    "function": {
        "name": "rag_search",
        "description": (
            "Поиск по инженерным нормативно-техническим документам ПКБ. "
            "Вызывай когда нужна конкретная техническая информация из нормативных документов."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос на русском языке"},
            },
            "required": ["query"],
        },
    },
}

_GET_PAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_document_page",
        "description": (
            "Получить текст конкретной страницы документа ПКБ. "
            "Используй когда знаешь document_id и номер страницы из результатов поиска "
            "и хочешь прочитать соседние страницы или уточнить контекст."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {"type": "integer", "description": "ID документа"},
                "page": {"type": "integer", "description": "Номер страницы (1-based)"},
            },
            "required": ["document_id", "page"],
        },
    },
}

_TOOLS = [_RAG_TOOL, _GET_PAGE_TOOL]

_MAX_TOOL_ITERS = 5

_CONTEXT_TOKEN_BUDGET = 6000
_SUMMARY_MAX_TOKENS = 1024
_RECENT_KEEP_MESSAGES = 4


def _normalize_source_refs(text: str) -> str:
    text = _SOURCE_REF_RANGE_RE.sub(
        lambda m: "".join(
            f"[source:{i}]" for i in range(int(m.group(1)), int(m.group(2)) + 1)
        ),
        text,
    )
    text = _SOURCE_REF_COMBINED_RE.sub(
        lambda m: "".join(f"[source:{i.strip()}]" for i in m.group(1).split(",")),
        text,
    )
    return text


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _clean_content(role: str, content: str) -> str:
    if role == "assistant":
        content = _normalize_source_refs(content)
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
        clause = f" §{chunk.clause}" if chunk.clause else ""
        page = f", стр. {chunk.page}" if chunk.page else ""
        return f"[document_id:{chunk.document_id}, section_id:{chunk.section_id}{clause}{page}]"

    normalized = _normalize_source_refs(llm_text)
    enriched = _SOURCE_REF_RE.sub(replace, normalized)
    return enriched, used_indices


def _format_chunks(chunks: list[rag_client.Chunk], start_index: int) -> str:
    parts = []
    for i, c in enumerate(chunks):
        clause = f" §{c.clause}" if c.clause else ""
        page = f", стр. {c.page}" if c.page else ""
        parts.append(f"[{start_index + i}] «{c.document_title}»{clause}{page}:\n{c.content}")
    return "\n\n".join(parts)


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
    result = await llm_client.complete(prompt, max_tokens=_SUMMARY_MAX_TOKENS)
    return result.content or ""


async def _prepare_context(
    session_factory: async_sessionmaker,
    session_id: str,
    exclude_message_id: str,
    settings,
) -> tuple[str | None, list[dict]]:
    summary, until = await _load_session_meta(session_factory, session_id)
    history = await _load_messages_after(session_factory, session_id, exclude_message_id, until)

    budget = _CONTEXT_TOKEN_BUDGET
    keep = _RECENT_KEEP_MESSAGES

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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _set_status(
    session_factory: async_sessionmaker,
    message_id: str,
    status: str,
    status_message: str | None = None,
    progress: int | None = None,
) -> None:
    async with session_factory() as db:
        async with db.begin():
            values: dict = {"status": status}
            if status_message is not None:
                values["message"] = status_message
            if progress is not None:
                values["progress"] = progress
            await db.execute(
                update(ChatMessage)
                .where(ChatMessage.message_id == message_id)
                .values(**values)
            )


def _build_llm_mock(query: str, chunks: list[rag_client.Chunk]) -> str:
    if not chunks:
        return "По данному запросу релевантные фрагменты в базе знаний не найдены."

    parts = []
    for i, chunk in enumerate(chunks[:3]):
        parts.append(f"{chunk.excerpt} [source:{i}]")
    return " ".join(parts)


_ANALYZE_PROGRESS = [30, 50, 60, 68, 75]
_SEARCH_PROGRESS = [40, 55, 65, 72, 78]


async def _run_tool_loop(
    messages: list[dict],
    settings,
    valid_at: str,
    message_id: str,
    session_factory: async_sessionmaker,
) -> tuple[str, list[rag_client.Chunk], int, int]:
    all_chunks: list[rag_client.Chunk] = []
    total_prompt = 0
    total_completion = 0

    for i in range(_MAX_TOOL_ITERS):
        p = _ANALYZE_PROGRESS[i] if i < len(_ANALYZE_PROGRESS) else 78
        await _set_status(session_factory, message_id, "analyzing", "Обращение к LLM...", progress=p)
        result = await llm_client.complete(messages, tools=_TOOLS)
        total_prompt += result.prompt_tokens
        total_completion += result.completion_tokens

        if not result.tool_calls:
            return result.content or "", all_chunks, total_prompt, total_completion

        messages.append({
            "role": "assistant",
            "content": result.content,
            "tool_calls": result.tool_calls,
        })

        for tc in result.tool_calls:
            fn = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])

            if fn == "rag_search":
                query = args.get("query", "")
                logger.info("tool_call rag_search query=%r", query, extra={"message_id": message_id})
                sp = _SEARCH_PROGRESS[i] if i < len(_SEARCH_PROGRESS) else 78
                await _set_status(session_factory, message_id, "searching", f"Поиск: {query[:60]}...", progress=sp)
                try:
                    chunks = await asyncio.wait_for(
                        rag_client.search(query, top_k=10, valid_at=valid_at),
                        timeout=60.0,
                    )
                except Exception:
                    logger.warning("tool_call rag_search failed", extra={"message_id": message_id}, exc_info=True)
                    chunks = []
                start_idx = len(all_chunks)
                all_chunks.extend(chunks)
                tool_content = _format_chunks(chunks, start_idx) if chunks else "Релевантные фрагменты не найдены."

            elif fn == "get_document_page":
                doc_id = int(args.get("document_id", 0))
                page = int(args.get("page", 1))
                logger.info("tool_call get_document_page doc_id=%d page=%d", doc_id, page, extra={"message_id": message_id})
                sp = _SEARCH_PROGRESS[i] if i < len(_SEARCH_PROGRESS) else 78
                await _set_status(session_factory, message_id, "searching", f"Чтение страницы {page} документа {doc_id}...", progress=sp)
                try:
                    tool_content = await asyncio.wait_for(
                        registry_client.get_document_page_text(doc_id, page),
                        timeout=15.0,
                    )
                except Exception:
                    logger.warning("tool_call get_document_page failed", extra={"message_id": message_id}, exc_info=True)
                    tool_content = f"Не удалось получить страницу {page} документа {doc_id}."

            else:
                tool_content = f"Неизвестный инструмент: {fn}"

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_content,
            })

    await _set_status(session_factory, message_id, "analyzing", "Формирование ответа...", progress=80)
    result = await llm_client.complete(messages)
    total_prompt += result.prompt_tokens
    total_completion += result.completion_tokens
    return result.content or "", all_chunks, total_prompt, total_completion


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

        await _set_status(session_factory, message_id, "enriching", "Нормализация терминов запроса...", progress=10)
        enrichment_skipped = False
        try:
            enriched_query, _synonyms = await asyncio.wait_for(
                registry_client.enrich_query(user_query), timeout=30.0
            )
        except Exception:
            enriched_query = user_query
            enrichment_skipped = True
            warnings.append("Обогащение терминов недоступно. Поиск выполнен без нормализации.")
            logger.warning("query enrichment skipped", extra={"message_id": message_id}, exc_info=True)

        await _set_status(session_factory, message_id, "generating", "Подготовка контекста диалога...", progress=20)
        summary, history = await _prepare_context(
            session_factory, session_id, message_id, settings
        )

        if settings.MOCK_LLM_ENABLED:
            await _set_status(session_factory, message_id, "searching", f"Поиск: {enriched_query[:60]}...", progress=30)
            try:
                chunks = await asyncio.wait_for(
                    rag_client.search(enriched_query, top_k=10, valid_at=_utcnow().strftime("%Y-%m-%d")),
                    timeout=60.0,
                )
            except Exception:
                logger.error("rag search failed", extra={"message_id": message_id}, exc_info=True)
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

            await asyncio.sleep(0.3)
            llm_text = _build_llm_mock(enriched_query, chunks)
            all_chunks = chunks
        else:
            messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
            if summary:
                messages.append({"role": "system", "content": f"Резюме предыдущего диалога:\n{summary}"})
            messages.extend(history)
            messages.append({"role": "user", "content": enriched_query})

            try:
                llm_text, all_chunks, prompt_tokens, completion_tokens = await asyncio.wait_for(
                    _run_tool_loop(messages, settings, _utcnow().strftime("%Y-%m-%d"), message_id, session_factory),
                    timeout=180.0,
                )
            except Exception:
                logger.error("tool loop failed", extra={"message_id": message_id}, exc_info=True)
                await _set_status(session_factory, message_id, "failed")
                return

        await _set_status(session_factory, message_id, "enriching_citations", "Обогащение цитат...", progress=90)
        try:
            final_text, used_indices = await asyncio.wait_for(
                asyncio.to_thread(_enrich_citations, llm_text, all_chunks),
                timeout=30.0,
            )
        except Exception:
            warnings.append("Обогащение цитат недоступно.")
            logger.warning("citation enrichment skipped", extra={"message_id": message_id}, exc_info=True)
            final_text = llm_text
            used_indices = sorted({
                int(m.group(1)) for m in _SOURCE_REF_RE.finditer(_normalize_source_refs(llm_text))
                if int(m.group(1)) < len(all_chunks)
            })

        used_chunks = [all_chunks[i] for i in used_indices if i < len(all_chunks)] or all_chunks

        async with session_factory() as db:
            async with db.begin():
                processing_time_ms = int((_utcnow() - t_start).total_seconds() * 1000)
                result = await db.execute(
                    update(ChatMessage)
                    .where(ChatMessage.message_id == message_id)
                    .values(
                        content=final_text,
                        status="answered",
                        progress=100,
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

        logger.info("pipeline finished", extra={"message_id": message_id, "chunks": len(all_chunks)})

    except Exception:
        logger.error("pipeline error", extra={"message_id": message_id}, exc_info=True)
        async with session_factory() as db:
            async with db.begin():
                await db.execute(
                    update(ChatMessage)
                    .where(ChatMessage.message_id == message_id)
                    .values(
                        content="Внутренняя ошибка при обработке запроса. Попробуйте повторить.",
                        status="failed",
                        processing_time_ms=0,
                    )
                )
