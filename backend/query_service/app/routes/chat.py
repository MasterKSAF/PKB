import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import get_settings
from ..db import get_db, get_session_factory
from ..models import ChatSession, ChatMessage, ChatSource, ChatExport
from ..schemas import (
    ChatRequest, ChatResponse, AnswerItem, CitationResponse,
    CreateSessionRequest, SessionResponse, SessionListResponse, SessionListItem, SessionListMeta,
    UpdateSessionRequest, DeleteSessionResponse,
    SendMessageRequest, MessageResponse, PendingMessageResponse, SourceResponse, SessionMessagesResponse,
    ContextRequest, ContextResponse,
    ExportRequest, ExportResponse,
    FeedbackRequest, FeedbackResponse,
    HistoryResponse, HistoryItem, HistoryMeta, HistoryExportResponse,
)
from ..repositories import session_repo, message_repo, feedback_repo
from ..services.auth import get_current_user
from ..services.pipeline import run_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])

_FINAL_STATUSES = {"answered", "failed", "not_found", "out_of_scope", "needs_clarification", "source_conflict"}


def _session_to_response(s: ChatSession, msg_count: int = 0) -> SessionResponse:
    return SessionResponse(
        session_id=s.session_id,
        title=s.title,
        user_id=s.user_id,
        project_id=s.project_id,
        document_ids=s.document_ids or [],
        options=s.options or {},
        message_count=msg_count,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _source_dict(src: ChatSource) -> dict:
    return {
        "document_id": src.document_id,
        "document_title": src.document_title,
        "section_id": src.section_id,
        "page": src.page_number,
        "clause": src.clause,
        "section_title": src.section_title,
        "excerpt": src.excerpt,
        "score": src.score,
        "confidence": src.confidence,
        "page_preview_url": src.page_preview_url,
        "document_url": src.document_url,
    }


def _msg_dict(m: ChatMessage) -> dict:
    base = {
        "message_id": m.message_id,
        "role": m.role,
        "content": m.content,
        "status": m.status,
        "timestamp": m.timestamp.isoformat(),
    }
    if m.role == "assistant":
        base["sources"] = [_source_dict(src) for src in m.sources]
        base["processing_time_ms"] = m.processing_time_ms
    return base


@router.post("/sessions", status_code=201, response_model=SessionResponse)
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        s = await session_repo.create_session(db, user_id, body.title, body.document_ids, body.options.model_dump(), body.project_id)
    return _session_to_response(s, 0)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    sessions, total = await session_repo.list_sessions(db, user_id, page, page_size, search, project_id)
    items = []
    for s in sessions:
        cnt = await session_repo.message_count(db, s.session_id)
        last = await session_repo.last_assistant_message(db, s.session_id)
        preview = last.content[:120] if last and last.content else None
        items.append(SessionListItem(
            session_id=s.session_id,
            title=s.title,
            project_id=s.project_id,
            document_ids=s.document_ids or [],
            message_count=cnt,
            last_message_preview=preview,
            created_at=s.created_at,
            updated_at=s.updated_at,
        ))
    return SessionListResponse(sessions=items, meta=SessionListMeta(total=total, page=page, page_size=page_size))


@router.get("/sessions/{session_id}", response_model=SessionMessagesResponse)
async def get_session(
    session_id: int,
    limit: int = Query(50, ge=1, le=200),
    before: str | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    s = await session_repo.get_session(db, session_id, user_id)
    if not s:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})
    msgs, has_more = await message_repo.get_session_messages(db, session_id, limit, before)
    return SessionMessagesResponse(
        session_id=s.session_id,
        title=s.title,
        document_ids=s.document_ids or [],
        messages=[_msg_dict(m) for m in msgs],
        has_more=has_more,
    )


@router.get("/sessions/{session_id}/messages/last")
async def get_last_messages(
    session_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    s = await session_repo.get_session(db, session_id, user_id)
    if not s:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})

    q = (
        select(ChatMessage)
        .options(selectinload(ChatMessage.sources))
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(limit)
    )
    msgs = (await db.execute(q)).scalars().all()

    total_q = select(func.count()).where(ChatMessage.session_id == session_id)
    total = (await db.execute(total_q)).scalar_one()

    return {
        "session_id": session_id,
        "document_ids": s.document_ids or [],
        "messages": [_msg_dict(m) for m in msgs],
        "has_older": total > limit,
    }


@router.get("/sessions/{session_id}/messages")
async def list_messages(
    session_id: int,
    after: int | None = None,
    before: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    s = await session_repo.get_session(db, session_id, user_id)
    if not s:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})

    q = (
        select(ChatMessage)
        .options(selectinload(ChatMessage.sources))
        .where(ChatMessage.session_id == session_id)
    )

    if after:
        anchor_q = select(ChatMessage.timestamp).where(ChatMessage.message_id == after)
        anchor_ts = (await db.execute(anchor_q)).scalar_one_or_none()
        if anchor_ts:
            q = q.where(ChatMessage.timestamp > anchor_ts)
    elif before:
        anchor_q = select(ChatMessage.timestamp).where(ChatMessage.message_id == before)
        anchor_ts = (await db.execute(anchor_q)).scalar_one_or_none()
        if anchor_ts:
            q = q.where(ChatMessage.timestamp < anchor_ts)

    q = q.order_by(ChatMessage.timestamp.asc()).limit(limit + 1)
    rows = (await db.execute(q)).scalars().all()
    has_more = len(rows) > limit
    msgs = rows[:limit]

    return {
        "session_id": session_id,
        "messages": [_msg_dict(m) for m in msgs],
        "has_more": has_more,
    }


@router.get("/sessions/{session_id}/messages/{message_id}")
async def get_message(
    session_id: int,
    message_id: int,
    longpoll: int | None = Query(None, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    s = await session_repo.get_session(db, session_id, user_id)
    if not s:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})

    async def _fetch_message(db_session: AsyncSession) -> ChatMessage | None:
        q = (
            select(ChatMessage)
            .options(selectinload(ChatMessage.sources))
            .where(ChatMessage.message_id == message_id, ChatMessage.session_id == session_id)
        )
        return (await db_session.execute(q)).scalar_one_or_none()

    msg = await _fetch_message(db)
    if not msg:
        raise HTTPException(status_code=404, detail={"error": {"code": "MESSAGE_NOT_FOUND", "message": "Сообщение не найдено", "details": {}}})

    if longpoll and msg.status not in _FINAL_STATUSES:
        session_factory = get_session_factory()
        deadline = asyncio.get_event_loop().time() + longpoll
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(0.5)
            async with session_factory() as fresh_db:
                msg = await _fetch_message(fresh_db)
                if msg and msg.status in _FINAL_STATUSES:
                    break

    return {
        "session_id": session_id,
        "document_ids": s.document_ids or [],
        "message": _msg_dict(msg) if msg else None,
    }


@router.post("/sessions/{session_id}/messages", status_code=202, response_model=PendingMessageResponse)
async def send_message(
    session_id: int,
    body: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        s = await session_repo.get_session(db, session_id, user_id)
        if not s:
            raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})

        await message_repo.save_user_message(db, session_id, body.content)

        msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            status="pending",
            content=None,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(msg)
        await db.flush()
        message_id = msg.message_id
        msg.answer_id = message_id  # answer_id == message_id для ответов ассистента
        s.updated_at = datetime.now(timezone.utc)

    session_factory = get_session_factory()
    background_tasks.add_task(run_pipeline, session_factory, message_id, session_id, body.content)

    return PendingMessageResponse(
        message_id=message_id,
        session_id=session_id,
        role="user",
        status="pending",
        content=body.content,
        timestamp=datetime.now(timezone.utc),
    )


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    body: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        s = await session_repo.get_session(db, session_id, user_id)
        if not s:
            raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})
        s = await session_repo.update_session(db, s, body.title, body.document_ids, body.project_id)
    cnt = await session_repo.message_count(db, session_id)
    return _session_to_response(s, cnt)


@router.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        s = await session_repo.get_session(db, session_id, user_id)
        if not s:
            raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})
        await session_repo.delete_session(db, s)
    return DeleteSessionResponse(session_id=session_id, deleted_at=datetime.now(timezone.utc))


@router.post("/sessions/{session_id}/context", response_model=ContextResponse)
async def manage_context(
    session_id: int,
    body: ContextRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    s = await session_repo.get_session(db, session_id, user_id)
    if not s:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})

    messages_map = {
        "clear": "История диалога очищена.",
        "summarize": "Резюме диалога сгенерировано.",
        "add_documents": "Документы добавлены в область поиска.",
        "remove_documents": "Документы удалены из области поиска.",
    }
    return ContextResponse(
        session_id=session_id,
        action=body.action,
        status="completed",
        message=messages_map.get(body.action, "Операция выполнена."),
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/sessions/{session_id}/export", response_model=ExportResponse)
async def export_session(
    session_id: int,
    body: ExportRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    s = await session_repo.get_session(db, session_id, user_id)
    if not s:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})
    now = datetime.now(timezone.utc)
    async with db.begin():
        exp = ChatExport(
            session_id=session_id, format=body.format,
            status="completed", created_at=now, expires_at=now + timedelta(days=7),
        )
        db.add(exp)
        await db.flush()
        export_id = exp.export_id
        exp.url = f"/files/exports/{export_id}/download"
    return ExportResponse(
        export_id=export_id, session_id=session_id, format=body.format,
        status="completed", url=f"/files/exports/{export_id}/download",
        expires_at=now + timedelta(days=7), created_at=now,
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def post_feedback(
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    rating = body.rating
    if body.useful is not None and rating is None:
        rating = "positive" if body.useful else "negative"

    async with db.begin():
        fb = await feedback_repo.save_feedback(
            db, user_id,
            message_id=body.message_id,
            answer_id=body.answer_id,
            rating=rating,
            useful=body.useful,
            comment=body.comment,
            aspects=[a.model_dump() for a in body.aspects] if body.aspects else None,
            opened_citation_ids=body.opened_citation_ids,
        )
        fb_id = fb.feedback_id
    return FeedbackResponse(
        feedback_id=fb_id,
        saved=True,
        metrics_changed={"rated_answers": 1, "useful_rate": 1.0 if body.useful else 0.0, "flagged_for_review": 0},
    )


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        if body.session_id:
            s = await session_repo.get_session(db, body.session_id, user_id)
            if not s:
                raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Сессия не найдена", "details": {}}})
        else:
            title = body.question[:60] if body.question else "Новый диалог"
            doc_ids = body.context.document_ids if body.context else []
            project_id = body.context.project_id if body.context else None
            s = await session_repo.create_session(db, user_id, title, doc_ids, {}, project_id)

        await message_repo.save_user_message(db, s.session_id, body.question)

        msg = ChatMessage(
            session_id=s.session_id,
            role="assistant",
            status="pending",
            content=None,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(msg)
        await db.flush()
        message_id = msg.message_id
        msg.answer_id = message_id
        session_id_snapshot = s.session_id
        s.updated_at = datetime.now(timezone.utc)

    session_factory = get_session_factory()
    background_tasks.add_task(run_pipeline, session_factory, message_id, session_id_snapshot, body.question)

    return ChatResponse(
        answer_id=message_id,
        session_id=session_id_snapshot,
        status="pending",
        message=None,
        answer_items=[],
        missing_fields=None,
        conflicts=None,
        latency_ms=0,
    )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    user_id_filter: str | None = Query(None, alias="user_id"),
    status_filter: str | None = Query(None, alias="status"),
    project_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    settings = get_settings()
    q = (
        select(ChatMessage)
        .options(selectinload(ChatMessage.sources))
        .where(ChatMessage.role == "assistant")
        .join(ChatSession, ChatMessage.session_id == ChatSession.session_id)
        .where(ChatSession.user_id == user_id)
    )
    if status_filter:
        q = q.where(ChatMessage.status == status_filter)
    if project_id is not None:
        q = q.where(ChatSession.project_id == project_id)

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar_one()

    q = q.order_by(ChatMessage.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    msgs = (await db.execute(q)).scalars().all()

    items = []
    for m in msgs:
        user_msg = (await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == m.session_id, ChatMessage.role == "user")
            .order_by(ChatMessage.timestamp.desc())
            .limit(1)
        )).scalar_one_or_none()

        items.append(HistoryItem(
            history_id=f"hist-{m.message_id}",
            session_id=m.session_id,
            created_at=m.timestamp,
            user_id=user_id,
            user_name=settings.DEV_USER_NAME,
            question=user_msg.content or "" if user_msg else "",
            answer_preview=(m.content or "")[:120],
            status=m.status or "answered",
            source_count=len(m.sources),
            answer_id=m.answer_id,
        ))

    return HistoryResponse(items=items, meta=HistoryMeta(total=total, page=page, page_size=page_size))


@router.get("/history/export", response_model=HistoryExportResponse)
async def export_history(
    user_id: str = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    return HistoryExportResponse(
        export_id="pending",
        format="xlsx",
        url="/files/exports/history/download",
        created_at=now,
    )
