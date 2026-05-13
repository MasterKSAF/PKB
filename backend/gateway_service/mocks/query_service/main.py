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
from typing import Any, Dict, List, Optional

from common import (
    SEED_HISTORY,
    SEED_SESSIONS,
    error_response,
    new_id,
    paginate,
    utcnow,
)
from fastapi import APIRouter, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1")

# ---------------------------------------------------------------------------
# In-memory хранилища
# ---------------------------------------------------------------------------

_sessions: Dict[str, dict] = {}
_history: List[dict] = []
_feedback_store: List[dict] = []
_export_store: Dict[str, dict] = {}


def _init_data():
    global _sessions, _history
    _sessions = copy.deepcopy({s["session_id"]: s for s in SEED_SESSIONS})
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

_MOCK_SOURCES = [
    {
        "document_id": "doc-001",
        "document_title": "Спецификация по ГОСТ 2.109",
        "page_number": 3,
        "fragment_id": f"frag-{new_id()}",
        "text": "Толщина стенки корпуса: 5 мм, материал: Сталь 45",
        "score": round(random.uniform(0.85, 0.99), 2),
    },
    {
        "document_id": "doc-002",
        "document_title": "Чертеж детали 101",
        "page_number": 1,
        "fragment_id": f"frag-{new_id()}",
        "text": "Габаритные размеры: 150x80x25 мм",
        "score": round(random.uniform(0.85, 0.99), 2),
    },
    {
        "document_id": "rd-001",
        "document_title": "ГОСТ 2.109-73",
        "page_number": 5,
        "fragment_id": f"frag-{new_id()}",
        "text": "Толщина стенки не менее 4 мм для изделий данного типа",
        "score": round(random.uniform(0.90, 1.0), 2),
    },
    {
        "document_id": "rd-002",
        "document_title": "ГОСТ 2.307-2011",
        "page_number": 3,
        "fragment_id": f"frag-{new_id()}",
        "text": "Предельные отклонения размеров: H11, h11",
        "score": round(random.uniform(0.80, 0.95), 2),
    },
]


def _generate_answer(question: str) -> dict:
    """Генерирует mock-ответ на вопрос."""
    return {
        "content": random.choice(_MOCK_ANSWERS),
        "sources": random.sample(_MOCK_SOURCES, min(3, len(_MOCK_SOURCES))),
        "model_used": "gpt-4",
        "processing_time_ms": random.randint(500, 3000),
    }


# ---------------------------------------------------------------------------
# Модели данных
# ---------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None
    document_ids: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    document_ids: Optional[List[str]] = None


class AttachmentModel(BaseModel):
    type: str = "text"
    text: Optional[str] = None
    source_document_id: Optional[str] = None
    source_page_number: Optional[int] = None


class MessageOptions(BaseModel):
    search_in_session_docs: Optional[bool] = True
    use_full_context: Optional[bool] = False


class SendMessageRequest(BaseModel):
    content: str
    attachments: Optional[List[AttachmentModel]] = None
    options: Optional[MessageOptions] = None


class ContextActionRequest(BaseModel):
    action: str
    params: Optional[Dict[str, Any]] = None


class ExportSessionRequest(BaseModel):
    format: str = "pdf"
    options: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: Optional[int] = None
    comment: Optional[str] = None
    aspects: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class TextSearchRequest(BaseModel):
    text: str
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = 5
    filters: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None


class TextAskRequest(BaseModel):
    text: str
    document_ids: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Response-модели для OpenAPI
# ---------------------------------------------------------------------------


class CitationModel(BaseModel):
    citation_id: str
    document_id: str
    document_title: str
    section: str
    page: int
    fragment: str
    page_preview_url: str
    document_url: str


class AnswerItem(BaseModel):
    number: int
    text: str
    citations: List[CitationModel]


class ChatResponse(BaseModel):
    answer_id: str
    session_id: str
    status: str
    message: str
    answer_items: List[AnswerItem]
    latency_ms: int


class TextSearchResultItem(BaseModel):
    fragment_id: str
    document_id: str
    document_title: str
    page_number: int
    text: str
    score: float
    document_type: str
    matched_subquery: str


class TextSearchResponse(BaseModel):
    original_text: str
    analysis: Dict[str, Any]
    results: List[TextSearchResultItem]
    total_found: int
    processing_time_ms: int


class TextAskSource(BaseModel):
    document_id: str
    document_title: str
    page_number: int
    fragment_id: str
    text: str
    score: float


class TextAskResponse(BaseModel):
    original_text: str
    normalized_question: str
    answer: str
    sources: List[TextAskSource]
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
async def create_session(req: CreateSessionRequest):
    """Создать сессию чата."""
    session_id = f"sess-{new_id()}"
    now = utcnow()
    new_session = {
        "session_id": session_id,
        "title": req.title or f"Сессия {session_id}",
        "user_id": "u-001",
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
async def send_message(session_id: str, req: SendMessageRequest):
    """Отправить сообщение в сессию."""
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
    answer = _generate_answer(req.content)
    asst_msg_id = f"msg-{new_id()}"
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
    }
    session["messages"].append(assistant_message)
    session["message_count"] = len(session["messages"])
    session["last_message_preview"] = answer["content"][:80] + "..."
    session["updated_at"] = utcnow()

    # Добавляем в историю
    _history.append(
        {
            "history_id": f"hist-{new_id()}",
            "session_id": session_id,
            "created_at": utcnow(),
            "user_id": "u-001",
            "user_name": "Иванов С.П.",
            "question": req.content,
            "answer_preview": answer["content"][:80] + "...",
            "status": "completed",
            "source_count": len(answer["sources"]),
            "answer_id": f"ans-{new_id()}",
        }
    )

    return assistant_message


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
    user_id: Optional[str] = Query(None),
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
    """Задать вопрос (вне сессии)."""
    answer = _generate_answer(req.question)
    answer_id = f"ans-{new_id()}"

    return {
        "answer_id": answer_id,
        "session_id": req.session_id or f"sess-{new_id()}",
        "status": "completed",
        "message": "Ответ сгенерирован",
        "answer_items": [
            {
                "number": 1,
                "text": answer["content"],
                "citations": [
                    {
                        "citation_id": f"cit-{new_id()}",
                        "document_id": s["document_id"],
                        "document_title": s["document_title"],
                        "section": "Основные требования",
                        "page": s["page_number"],
                        "fragment": s["text"][:100],
                        "page_preview_url": f"/api/v1/documents/{s['document_id']}/pages/{s['page_number']}/preview",
                        "document_url": f"/api/v1/documents/{s['document_id']}",
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
            "fragment_id": "frag-001",
            "document_id": "doc-001",
            "document_title": "Спецификация по ГОСТ 2.109",
            "page_number": 3,
            "text": "Толщина стенки корпуса: 5 мм, материал: Сталь 45",
            "score": 0.95,
            "document_type": "specification",
        },
        {
            "fragment_id": "frag-002",
            "document_id": "rd-001",
            "document_title": "ГОСТ 2.109-73",
            "page_number": 5,
            "text": "Толщина стенки не менее 4 мм для изделий данного типа",
            "score": 0.92,
            "document_type": "normative",
        },
        {
            "fragment_id": "frag-003",
            "document_id": "doc-002",
            "document_title": "Чертеж детали 101",
            "page_number": 1,
            "text": "Габаритные размеры: 150x80x25 мм. Материал: Сталь 45.",
            "score": 0.88,
            "document_type": "drawing",
        },
        {
            "fragment_id": "frag-004",
            "document_id": "rd-002",
            "document_title": "ГОСТ 2.307-2011",
            "page_number": 3,
            "text": "Предельные отклонения размеров: H11, h11 для свободных размеров",
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
                "fragment_id": r["fragment_id"],
                "document_id": r["document_id"],
                "document_title": r["document_title"],
                "page_number": r["page_number"],
                "text": r["text"],
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
                "page_number": s["page_number"],
                "fragment_id": s["fragment_id"],
                "text": s["text"],
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
