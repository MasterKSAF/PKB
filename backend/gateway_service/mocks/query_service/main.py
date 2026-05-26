"""
Query Service Mock
Сервис чата и текстового поиска/вопросов (in-memory).
Порт: 8083
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
import random
from typing import Any

from common import (
    SEED_HISTORY,
    SEED_SESSIONS,
    error_response,
    new_id,
    paginate,
    utcnow,
)
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1")

# ---------------------------------------------------------------------------
# In-memory хранилища
# ---------------------------------------------------------------------------

_sessions: dict[str, dict] = {}
_history: list[dict] = []
_feedback_store: list[dict] = []
_export_store: dict[str, dict] = {}


def _init_data():
    global _sessions, _history
    if not _sessions:
        _sessions = copy.deepcopy({s["session_id"]: s for s in SEED_SESSIONS})
    if not _history:
        _history = copy.deepcopy(SEED_HISTORY)


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

_MOCK_ANSWERS = [
    "На основании анализа проектной документации, толщина стенки корпуса составляет 5 мм, что соответствует требованиям ГОСТ 2.109-73 (не менее 4 мм).",
    "В спецификации указаны следующие материалы: Сталь 45 (корпус), Алюминий Д16Т (крышка). Марки материалов соответствуют требованиям конструкторской документации.",
    "Размеры детали: 150x80x25 мм. Предельные отклонения по H11/h11 соответствуют ГОСТ 2.307-2011.",
    "Рекомендуется проверить допуски на отверстие Ø12H12. По ГОСТ 2.307-2011 рекомендуется H11 для данного типа соединений.",
    "Ссылки на НСИ: ГОСТ 2.109-73 (п. 3.2), ГОСТ 2.307-2011 (п. 4.1), ГОСТ 2.309-73 (п. 2.5).",
]


def _generate_sources() -> list:
    """Генерирует источники динамически, чтобы разные запросы ссылались на разные документы."""
    all_sources = [
        {
            "document_id": "doc-001",
            "document_title": "Спецификация по ГОСТ 2.109",
            "page": 3,
            "section_id": f"sect-{new_id()}",
            "excerpt": "Толщина стенки корпуса: 5 мм, материал: Сталь 45",
            "score": round(random.uniform(0.85, 0.99), 2),
            "clause": "Основные требования",
            "page_preview_url": "/api/v1/documents/doc-001/pages/3/preview",
            "document_url": "/api/v1/documents/doc-001",
        },
        {
            "document_id": "doc-002",
            "document_title": "Чертеж детали 101",
            "page": 1,
            "section_id": f"sect-{new_id()}",
            "excerpt": "Габаритные размеры: 150x80x25 мм",
            "score": round(random.uniform(0.85, 0.99), 2),
            "clause": "Габаритные размеры",
            "page_preview_url": "/api/v1/documents/doc-002/pages/1/preview",
            "document_url": "/api/v1/documents/doc-002",
        },
        {
            "document_id": "rd-001",
            "document_title": "ГОСТ 2.109-73",
            "page": 5,
            "section_id": f"sect-{new_id()}",
            "excerpt": "Толщина стенки не менее 4 мм для изделий данного типа",
            "score": round(random.uniform(0.90, 1.0), 2),
            "clause": "п. 3.2",
            "page_preview_url": "/api/v1/documents/rd-001/pages/5/preview",
            "document_url": "/api/v1/documents/rd-001",
        },
        {
            "document_id": "rd-002",
            "document_title": "ГОСТ 2.307-2011",
            "page": 3,
            "section_id": f"sect-{new_id()}",
            "excerpt": "Предельные отклонения размеров: H11, h11",
            "score": round(random.uniform(0.80, 0.95), 2),
            "clause": "п. 4.1",
            "page_preview_url": "/api/v1/documents/rd-002/pages/3/preview",
            "document_url": "/api/v1/documents/rd-002",
        },
    ]
    # Динамически добавляем варианты источников для разнообразия
    extra = [
        {
            "document_id": "doc-003",
            "document_title": "Архивная копия альбома чертежей 1985",
            "page": random.randint(1, 45),
            "section_id": f"sect-{new_id()}",
            "excerpt": "Фрагмент архивного чертежа, масштаб 1:1",
            "score": round(random.uniform(0.60, 0.80), 2),
            "clause": "Архивные данные",
            "page_preview_url": "/api/v1/documents/doc-003/pages/{page}/preview",
            "document_url": "/api/v1/documents/doc-003",
        },
        {
            "document_id": "rd-003",
            "document_title": "ОСТ 1.00000-80 — Общие требования",
            "page": random.randint(1, 10),
            "section_id": f"sect-{new_id()}",
            "excerpt": "Общие требования к изделиям авиационной техники",
            "score": round(random.uniform(0.75, 0.93), 2),
            "clause": "Раздел 1",
            "page_preview_url": "/api/v1/documents/rd-003/pages/{page}/preview",
            "document_url": "/api/v1/documents/rd-003",
        },
        {
            "document_id": "rd-004",
            "document_title": "ГОСТ 2.104-2006 — Основные надписи",
            "page": random.randint(1, 8),
            "section_id": f"sect-{new_id()}",
            "excerpt": "Форма и размеры основной надписи",
            "score": round(random.uniform(0.80, 0.95), 2),
            "clause": "Приложение А",
            "page_preview_url": "/api/v1/documents/rd-004/pages/{page}/preview",
            "document_url": "/api/v1/documents/rd-004",
        },
    ]
    return all_sources + extra


def _generate_answer(question: str) -> dict:
    """Генерирует mock-ответ на вопрос."""
    sources_pool = _generate_sources()
    return {
        "content": random.choice(_MOCK_ANSWERS),
        "sources": random.sample(sources_pool, min(3, len(sources_pool))),
        "model_used": "gpt-4",
        "processing_time_ms": random.randint(500, 3000),
    }


# ---------------------------------------------------------------------------
# Модели данных
# ---------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    title: str | None = None
    document_ids: list[str] | None = None
    options: dict[str, Any] | None = None


class UpdateSessionRequest(BaseModel):
    title: str | None = None
    document_ids: list[str] | None = None


class AttachmentModel(BaseModel):
    type: str = "text"
    text: str | None = None
    source_document_id: str | None = None
    source_page_number: int | None = None


class MessageOptions(BaseModel):
    search_in_session_docs: bool | None = True
    use_full_context: bool | None = False


class SendMessageRequest(BaseModel):
    content: str
    attachments: list[AttachmentModel] | None = None
    options: MessageOptions | None = None


class ContextActionRequest(BaseModel):
    action: str
    params: dict[str, Any] | None = None


class ExportSessionRequest(BaseModel):
    format: str = "pdf"
    options: dict[str, Any] | None = None


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: int | None = None
    comment: str | None = None
    aspects: list[dict[str, Any]] | None = None
    answer_id: str | None = None
    useful: bool | None = None
    opened_citation_ids: list[str] | None = None


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    context: dict[str, Any] | None = None


class TextSearchRequest(BaseModel):
    text: str
    document_ids: list[str] | None = None
    top_k: int | None = 5
    filters: dict[str, Any] | None = None
    options: dict[str, Any] | None = None


class TextAskRequest(BaseModel):
    text: str
    document_ids: list[str] | None = None
    options: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Response-модели для OpenAPI
# ---------------------------------------------------------------------------


class SourceItem(BaseModel):
    section_id: str
    document_id: str
    document_title: str
    clause: str
    page: int
    excerpt: str
    page_preview_url: str
    document_url: str


class AnswerItem(BaseModel):
    number: int
    text: str
    sources: list[SourceItem]


class ChatResponse(BaseModel):
    scenario: str = "completed"
    answer_id: str | None = None
    session_id: str | None = None
    status: str | None = None
    message: str | None = None
    answer_items: list[AnswerItem] | None = None
    latency_ms: int | None = None
    missing_fields: list[str] | None = None
    conflicts: list[dict] | None = None


class TextSearchResultItem(BaseModel):
    section_id: str
    document_id: str
    document_title: str
    page: int
    content: str
    score: float
    document_type: str
    matched_subquery: str


class TextSearchResponse(BaseModel):
    original_text: str
    analysis: dict[str, Any]
    results: list[TextSearchResultItem]
    total_found: int
    processing_time_ms: int


class TextAskSource(BaseModel):
    document_id: str
    document_title: str
    page: int
    section_id: str
    excerpt: str
    score: float


class TextAskResponse(BaseModel):
    original_text: str
    normalized_question: str
    answer: str
    sources: list[TextAskSource]
    disclaimer: str
    processing_time_ms: int
    model_used: str


# ---------------------------------------------------------------------------
# Инициализация
# ---------------------------------------------------------------------------

_init_data()


# ===========================================================================
# Группа chat
# ===========================================================================


@router.post("/chat/sessions", status_code=201)
async def create_session(req: CreateSessionRequest, request: Request = None):
    """Создать сессии чата."""
    user_id = (request.state.user.get("user_id") or "system") if request else "system"
    session_id = f"sess-{new_id()}"
    now = utcnow()
    new_session = {
        "session_id": session_id,
        "title": req.title or f"Сессия {session_id}",
        "user_id": user_id,
        "document_ids": req.document_ids or [],
        "options": req.options
        or {
            "model": "gpt-4",
            "temperature": 0.3,
            "max_context_messages": 10,
        },
        "message_count": 0,
        "messages": [],
        "has_more": False,
        "last_message_preview": "",
        "created_at": now,
        "updated_at": now,
    }
    _sessions[session_id] = new_session
    return new_session


@router.get("/chat/sessions")
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Список сессий."""
    items = list(_sessions.values())
    # Сортируем по updated_at (сначала новые)
    items.sort(key=lambda s: s.get("updated_at", ""), reverse=True)

    result = []
    for s in items:
        result.append(
            {
                "session_id": s["session_id"],
                "title": s.get("title", ""),
                "document_ids": s.get("document_ids", []),
                "message_count": s.get("message_count", 0),
                "last_message_preview": s.get("last_message_preview", ""),
                "created_at": s.get("created_at", ""),
                "updated_at": s.get("updated_at", ""),
            }
        )

    paged = paginate(result, page, page_size)
    return {
        "sessions": paged["items"],
        "meta": paged["meta"],
    }


@router.get("/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """Детали сессии с сообщениями."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=error_response("SESSION_NOT_FOUND", "Сессия чата не найдена"),
        )

    result = {
        "session_id": session["session_id"],
        "title": session.get("title", ""),
        "document_ids": session.get("document_ids", []),
        "messages": session.get("messages", []),
        "has_more": session.get("has_more", False),
    }
    return result


@router.put("/chat/sessions/{session_id}")
async def update_session(session_id: str, req: UpdateSessionRequest):
    """Обновить сессию."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=error_response("SESSION_NOT_FOUND", "Сессия чата не найдена"),
        )

    if req.title is not None:
        session["title"] = req.title
    if req.document_ids is not None:
        session["document_ids"] = req.document_ids
    session["updated_at"] = utcnow()

    return session


@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """Удалить сессию."""
    if session_id not in _sessions:
        raise HTTPException(
            status_code=404,
            detail=error_response("SESSION_NOT_FOUND", "Сессия чата не найдена"),
        )
    del _sessions[session_id]
    return {
        "session_id": session_id,
        "deleted_at": utcnow(),
    }


@router.post("/chat/sessions/{session_id}/messages")
async def send_message(
    session_id: str, req: SendMessageRequest, request: Request = None
):
    """Отправить сообщение в сессию."""
    user_id = (request.state.user.get("user_id") or "system") if request else "system"
    user_name = (request.state.user.get("full_name") or user_id) if request else user_id
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=error_response("SESSION_NOT_FOUND", "Сессия чата не найдена"),
        )

    # Сохраняем сообщение пользователя
    user_msg_id = f"msg-{new_id()}"
    now = utcnow()
    user_message = {
        "message_id": user_msg_id,
        "role": "user",
        "content": req.content,
        "timestamp": now,
        "status": "completed",
    }
    session.setdefault("messages", []).append(user_message)

    # Генерируем ответ ассистента
    asst_msg_id = f"msg-{new_id()}"

    # Эмулируем разные статусы ответа в зависимости от содержимого вопроса
    if "ошибка" in req.content.lower() or "error" in req.content.lower():
        # Ошибка генерации ответа
        assistant_message = {
            "message_id": asst_msg_id,
            "session_id": session_id,
            "role": "assistant",
            "status": "failed",
            "content": "Произошла ошибка при генерации ответа. Попробуйте переформулировать вопрос.",
            "sources": [],
            "model_used": "gpt-4",
            "processing_time_ms": 0,
            "timestamp": utcnow(),
            "feedback": None,
            "error_details": {
                "code": "GENERATION_FAILED",
                "message": "Ошибка генерации ответа",
            },
        }
        status = "failed"
    elif "долго" in req.content.lower() or "long" in req.content.lower():
        # Ответ ещё генерируется (pending)
        assistant_message = {
            "message_id": asst_msg_id,
            "session_id": session_id,
            "role": "assistant",
            "status": "pending",
            "content": "Ответ генерируется. Пожалуйста, ожидайте.",
            "sources": [],
            "model_used": "gpt-4",
            "processing_time_ms": 200,
            "timestamp": utcnow(),
            "feedback": None,
        }
        status = "pending"
    else:
        # Успешная генерация
        answer = _generate_answer(req.content)
        assistant_message = {
            "message_id": asst_msg_id,
            "session_id": session_id,
            "role": "assistant",
            "status": "completed",
            "content": answer["content"],
            "sources": answer["sources"],
            "model_used": answer["model_used"],
            "processing_time_ms": answer["processing_time_ms"],
            "timestamp": utcnow(),
            "feedback": None,
        }
        status = "completed"

    session["messages"].append(assistant_message)
    session["message_count"] = len(session["messages"])
    session["last_message_preview"] = assistant_message["content"][:80] + "..."
    session["updated_at"] = utcnow()

    # Добавляем в историю
    _history.append(
        {
            "history_id": f"hist-{new_id()}",
            "session_id": session_id,
            "created_at": utcnow(),
            "user_id": user_id,
            "user_name": user_name,
            "question": req.content,
            "answer_preview": assistant_message["content"][:80] + "...",
            "status": status,
            "source_count": len(assistant_message.get("sources", [])),
            "answer_id": f"ans-{new_id()}",
        }
    )

    # Упрощённый ответ
    return {
        "message_id": asst_msg_id,
        "session_id": session_id,
        "role": "assistant",
        "status": status,
        "content": assistant_message["content"],
        "timestamp": assistant_message["timestamp"],
    }


@router.post("/chat/sessions/{session_id}/context")
async def manage_context(session_id: str, req: ContextActionRequest):
    """Управление контекстом сессии."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=error_response("SESSION_NOT_FOUND", "Сессия чата не найдена"),
        )

    return {
        "session_id": session_id,
        "action": req.action,
        "status": "completed",
        "message": f"Контекст обновлён: {req.action}",
        "timestamp": utcnow(),
    }


@router.post("/chat/sessions/{session_id}/export")
async def export_session(session_id: str, req: ExportSessionRequest):
    """Экспорт сессии."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=error_response("SESSION_NOT_FOUND", "Сессия чата не найдена"),
        )

    export_id = f"export-{new_id()}"
    export_data = {
        "export_id": export_id,
        "session_id": session_id,
        "format": req.format,
        "status": "completed",
        "url": f"/api/v1/exports/{export_id}.{req.format}",
        "expires_at": utcnow(),
        "created_at": utcnow(),
    }
    _export_store[export_id] = export_data
    return export_data


@router.post("/chat/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Отправка обратной связи."""
    feedback_id = f"fb-{new_id()}"
    _feedback_store.append(
        {
            "feedback_id": feedback_id,
            "session_id": req.session_id,
            "message_id": req.message_id,
            "rating": req.rating,
            "comment": req.comment,
            "aspects": req.aspects or [],
            "answer_id": req.answer_id,
            "useful": req.useful,
            "opened_citation_ids": req.opened_citation_ids or [],
            "created_at": utcnow(),
        }
    )

    return {
        "feedback_id": feedback_id,
        "saved": True,
        "metrics_changed": {
            "rated_answers": len(_feedback_store),
            "useful_rate": 0.78,
            "flagged_for_review": 12,
        },
    }


@router.get("/chat/history")
async def get_chat_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: str | None = Query(None),
):
    """История вопросов."""
    items = list(_history)
    if user_id:
        items = [h for h in items if h.get("user_id") == user_id]

    # Сортируем по created_at (сначала новые)
    items.sort(key=lambda h: h.get("created_at", ""), reverse=True)

    paged = paginate(items, page, page_size)
    return {
        "items": paged["items"],
        "meta": paged["meta"],
    }


@router.get("/chat/history/export")
async def export_history(
    format: str = Query("csv"),
):
    """Экспорт истории."""
    export_id = f"export-{new_id()}"
    export_data = {
        "export_id": export_id,
        "format": format,
        "url": f"/api/v1/exports/history_{export_id}.{format}",
        "created_at": utcnow(),
    }
    _export_store[export_id] = export_data
    return export_data


@router.post("/chat", response_model=ChatResponse)
async def chat_ask(req: ChatRequest):
    """Задать вопрос (вне сессии).

    Поддерживает три сценария ответа:
    - completed:      содержит answer_items со sources
    - needs_clarification: содержит missing_fields
    - conflict:       содержит conflicts
    """
    # Эмулируем разные сценарии в зависимости от ключевых слов вопроса
    query_lower = req.question.lower()

    if "неопределён" in query_lower or "ambiguous" in query_lower:
        return {
            "scenario": "needs_clarification",
            "missing_fields": ["document_ids", "nsi_version"],
        }

    if "конфликт" in query_lower or "conflict" in query_lower:
        return {
            "scenario": "conflict",
            "conflicts": [
                {
                    "type": "normative_conflict",
                    "description": "Обнаружено противоречие между ГОСТ 2.109-73 (п.3.2) и ОСТ 1.00000-80 (п.5.1)",
                    "sources": [
                        {"document_id": "rd-001", "clause": "п. 3.2"},
                        {"document_id": "rd-003", "clause": "п. 5.1"},
                    ],
                }
            ],
        }

    # Сценарий pending (ответ в процессе генерации)
    if "долго" in query_lower or "wait" in query_lower or "pending" in query_lower:
        answer_id = f"ans-{new_id()}"
        return {
            "scenario": "pending",
            "answer_id": answer_id,
            "session_id": req.session_id or f"sess-{new_id()}",
            "status": "pending",
            "message": "Запрос обрабатывается, пожалуйста, ожидайте",
            "latency_ms": None,
        }

    # Сценарий failed (ошибка обработки)
    if "сбой" in query_lower or "fail" in query_lower or "ошибк" in query_lower:
        answer_id = f"ans-{new_id()}"
        return {
            "scenario": "failed",
            "answer_id": answer_id,
            "session_id": req.session_id or f"sess-{new_id()}",
            "status": "failed",
            "message": "Не удалось обработать запрос из-за внутренней ошибки",
            "latency_ms": None,
            "conflicts": [
                {
                    "type": "generation_error",
                    "description": "Ошибка генерации ответа модели",
                    "sources": [],
                }
            ],
        }

    # Сценарий completed по умолчанию
    answer = _generate_answer(req.question)
    answer_id = f"ans-{new_id()}"

    return {
        "scenario": "completed",
        "answer_id": answer_id,
        "session_id": req.session_id or f"sess-{new_id()}",
        "status": "completed",
        "message": "Ответ сгенерирован",
        "answer_items": [
            {
                "number": 1,
                "text": answer["content"],
                "sources": [
                    {
                        "section_id": s.get("section_id", f"sect-{new_id()}"),
                        "document_id": s["document_id"],
                        "document_title": s["document_title"],
                        "clause": s.get("clause", "Основные требования"),
                        "page": s["page"],
                        "excerpt": s["excerpt"],
                        "page_preview_url": s.get(
                            "page_preview_url",
                            f"/api/v1/documents/{s['document_id']}/pages/{s['page']}/preview",
                        ),
                        "document_url": s.get(
                            "document_url",
                            f"/api/v1/documents/{s['document_id']}",
                        ),
                    }
                    for s in answer["sources"]
                ],
            }
        ],
        "latency_ms": answer["processing_time_ms"],
    }


# ===========================================================================
# Группа text
# ===========================================================================


@router.post("/text/search", response_model=TextSearchResponse)
async def text_search(req: TextSearchRequest):
    """Поиск по тексту."""
    # Эмулируем семантический поиск
    query_lower = req.text.lower()
    mock_results = []

    # Используем seed-данные для имитации результатов
    all_texts = [
        {
            "section_id": "sect-001",
            "document_id": "doc-001",
            "document_title": "Спецификация по ГОСТ 2.109",
            "page": 3,
            "content": "Толщина стенки корпуса: 5 мм, материал: Сталь 45",
            "score": 0.95,
            "document_type": "specification",
        },
        {
            "section_id": "sect-002",
            "document_id": "rd-001",
            "document_title": "ГОСТ 2.109-73",
            "page": 5,
            "content": "Толщина стенки не менее 4 мм для изделий данного типа",
            "score": 0.92,
            "document_type": "normative",
        },
        {
            "section_id": "sect-003",
            "document_id": "doc-002",
            "document_title": "Чертеж детали 101",
            "page": 1,
            "content": "Габаритные размеры: 150x80x25 мм. Материал: Сталь 45.",
            "score": 0.88,
            "document_type": "drawing",
        },
        {
            "section_id": "sect-004",
            "document_id": "rd-002",
            "document_title": "ГОСТ 2.307-2011",
            "page": 3,
            "content": "Предельные отклонения размеров: H11, h11 для свободных размеров",
            "score": 0.85,
            "document_type": "normative",
        },
    ]

    # Фильтрация по document_ids
    if req.document_ids:
        all_texts = [t for t in all_texts if t["document_id"] in req.document_ids]

    # Фильтрация по типу документа
    if req.filters and req.filters.get("document_type"):
        all_texts = [
            t for t in all_texts if t["document_type"] == req.filters["document_type"]
        ]

    # Сортируем по score
    all_texts.sort(key=lambda x: x["score"], reverse=True)
    top_k = min(req.top_k or 5, len(all_texts))
    results = all_texts[:top_k]

    # Иногда добавляем заглушку "не найдено"
    if "no_match" in query_lower or "notfound" in query_lower:
        results = []
        total_found = 0
    else:
        total_found = len(all_texts)

    return {
        "original_text": req.text,
        "analysis": {
            "normalized_query": req.text.lower(),
            "entities": [
                {"type": "DIMENSION", "value": "5 мм"},
                {"type": "MATERIAL", "value": "Сталь 45"},
            ],
            "subqueries": [req.text],
        },
        "results": [
            {
                "section_id": r["section_id"],
                "document_id": r["document_id"],
                "document_title": r["document_title"],
                "page": r["page"],
                "content": r["content"],
                "score": r["score"],
                "document_type": r["document_type"],
                "matched_subquery": req.text,
            }
            for r in results
        ],
        "total_found": total_found,
        "processing_time_ms": random.randint(100, 1000),
    }


@router.post("/text/ask", response_model=TextAskResponse)
async def text_ask(req: TextAskRequest):
    """Задать вопрос к тексту."""
    answer = _generate_answer(req.text)

    return {
        "original_text": req.text,
        "normalized_question": req.text.lower(),
        "answer": answer["content"],
        "sources": [
            {
                "document_id": s["document_id"],
                "document_title": s["document_title"],
                "page": s["page"],
                "section_id": s["section_id"],
                "excerpt": s["excerpt"],
                "score": s["score"],
            }
            for s in answer["sources"]
        ],
        "disclaimer": "Результат требует инженерной верификации.",
        "processing_time_ms": answer["processing_time_ms"],
        "model_used": answer["model_used"],
    }


# ===========================================================================
# Health check
# ===========================================================================


@router.get("/system/health")
async def health():
    return {
        "status": "ok",
        "service": "query-service",
        "timestamp": utcnow(),
    }


# ===========================================================================
# Запуск
# ===========================================================================

app = FastAPI(title="Query Service Mock", version="1.0.0")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8083)
