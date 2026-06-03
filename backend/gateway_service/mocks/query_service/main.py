"""
Query Service — автономный сервис чата и текстового поиска.
Запуск: python main.py (порт QUERY_SERVICE_PORT, по умолчанию 8083)
"""

import copy
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Query Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_counter = 0
def new_id() -> str:
    global _counter
    _counter += 1
    return str(_counter)

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def error_response(code: str, message: str, details: dict = None) -> JSONResponse:
    status_map = {
        "VALIDATION_ERROR": 400, "UNAUTHORIZED": 401, "INVALID_TOKEN": 401,
        "FORBIDDEN": 403, "NOT_FOUND": 404, "SESSION_NOT_FOUND": 404,
        "INTERNAL_ERROR": 500,
    }
    return JSONResponse(
        status_code=status_map.get(code, 400),
        content={"error": {"code": code, "message": message, "details": details or {}}}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, JSONResponse):
        return exc.detail
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response("VALIDATION_ERROR", "Ошибка валидации полей", {"errors": exc.errors()})

def paginate(items: list, page: int, page_size: int) -> dict:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {"items": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}}

SEED_SESSIONS = [
    {"session_id": "sess-001", "title": "Тестовая сессия", "user_id": "u-001",
     "document_ids": ["doc-001"], "options": {},
     "message_count": 2, "messages": [
         {"message_id":"msg-001","role":"user","content":"Привет","timestamp":"2026-04-27T10:00:00Z","status":"completed"},
         {"message_id":"msg-002","role":"assistant","status":"completed",
          "content":"Здравствуйте! Чем могу помочь?","sources":[],"model_used":"gpt-4","processing_time_ms":500,
          "timestamp":"2026-04-27T10:00:01Z","feedback":None}
     ], "has_more": False, "last_message_preview": "Здравствуйте!",
     "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T10:00:01Z"}
]
SEED_HISTORY = [
    {"history_id":"hist-001","session_id":"sess-001","created_at":"2026-04-27T10:00:01Z",
     "user_id":"u-001","user_name":"Иванов И.И.","question":"Привет","answer_preview":"Здравствуйте!",
     "status":"completed","source_count":0,"answer_id":"ans-001"}
]

_sessions: Dict[str, dict] = {}
_history: List[dict] = []
_feedback_store: List[dict] = []
_export_store: Dict[str, dict] = {}

def init_data():
    global _sessions, _history
    _sessions = {s["session_id"]: copy.deepcopy(s) for s in SEED_SESSIONS}
    _history = copy.deepcopy(SEED_HISTORY)

init_data()

_MOCK_ANSWERS = [
    "На основании анализа проектной документации, толщина стенки корпуса составляет 5 мм, что соответствует требованиям ГОСТ 2.109-73.",
    "В спецификации указаны материалы: Сталь 45 (корпус), Алюминий Д16Т (крышка).",
    "Размеры детали: 150x80x25 мм. Предельные отклонения по H11/h11.",
    "Рекомендуется проверить допуски на отверстие Ø12H12.",
    "Ссылки на НСИ: ГОСТ 2.109-73, ГОСТ 2.307-2011.",
]

def _generate_sources() -> list:
    return [
        {"document_id":"doc-001","document_title":"Спецификация по ГОСТ 2.109","page":3,
         "section_id":f"sect-{new_id()}","excerpt":"Толщина стенки корпуса: 5 мм","score":0.95,
         "clause":"Основные требования","page_preview_url":"/documents/doc-001/pages/3/preview",
         "document_url":"/documents/doc-001/file"},
        {"document_id":"rd-001","document_title":"ГОСТ 2.109-73","page":5,
         "section_id":f"sect-{new_id()}","excerpt":"Толщина стенки не менее 4 мм","score":0.92,
         "clause":"п. 3.2","page_preview_url":"/documents/rd-001/pages/5/preview",
         "document_url":"/documents/rd-001/file"},
    ]

def _generate_answer(question: str) -> dict:
    sources = _generate_sources()
    return {
        "content": random.choice(_MOCK_ANSWERS),
        "sources": random.sample(sources, min(2, len(sources))),
        "model_used": "gpt-4",
        "processing_time_ms": random.randint(500, 3000),
    }

# Модели
class CreateSessionRequest(BaseModel):
    title: Optional[str] = None
    document_ids: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None
class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    document_ids: Optional[List[str]] = None
class SendMessageRequest(BaseModel):
    content: str
    attachments: Optional[List[dict]] = None
    options: Optional[Dict[str, Any]] = None
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
    answer_id: Optional[str] = None
    useful: Optional[bool] = None
    opened_citation_ids: Optional[List[str]] = None
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

# Маршруты
@app.post("/api/v1/chat/sessions", status_code=201)
async def create_session(req: CreateSessionRequest):
    session_id = f"sess-{new_id()}"
    now = utcnow()
    new_session = {
        "session_id": session_id, "title": req.title or f"Сессия {session_id}",
        "user_id": "anonymous", "document_ids": req.document_ids or [],
        "options": req.options or {"model":"gpt-4","temperature":0.3},
        "message_count": 0, "messages": [], "has_more": False,
        "last_message_preview": "", "created_at": now, "updated_at": now,
    }
    _sessions[session_id] = new_session
    return new_session

@app.get("/api/v1/chat/sessions")
async def list_sessions(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    items = sorted(_sessions.values(), key=lambda s: s.get("updated_at",""), reverse=True)
    result = [{
        "session_id": s["session_id"], "title": s.get("title",""),
        "document_ids": s.get("document_ids",[]), "message_count": s.get("message_count",0),
        "last_message_preview": s.get("last_message_preview",""),
        "created_at": s.get("created_at",""), "updated_at": s.get("updated_at",""),
    } for s in items]
    paged = paginate(result, page, page_size)
    return {"sessions": paged["items"], "meta": paged["meta"]}

@app.get("/api/v1/chat/sessions/{session_id}")
async def get_session(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=error_response("SESSION_NOT_FOUND", "Сессия не найдена"))
    return {
        "session_id": session["session_id"], "title": session.get("title",""),
        "document_ids": session.get("document_ids",[]),
        "messages": session.get("messages",[]), "has_more": session.get("has_more",False),
    }

@app.put("/api/v1/chat/sessions/{session_id}")
async def update_session(session_id: str, req: UpdateSessionRequest):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=error_response("SESSION_NOT_FOUND", "Сессия не найдена"))
    if req.title is not None:
        session["title"] = req.title
    if req.document_ids is not None:
        session["document_ids"] = req.document_ids
    session["updated_at"] = utcnow()
    return session

@app.delete("/api/v1/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=error_response("SESSION_NOT_FOUND", "Сессия не найдена"))
    del _sessions[session_id]
    return {"session_id": session_id, "deleted_at": utcnow()}

@app.post("/api/v1/chat/sessions/{session_id}/messages")
async def send_message(session_id: str, req: SendMessageRequest):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=error_response("SESSION_NOT_FOUND", "Сессия не найдена"))
    now = utcnow()
    user_msg = {"message_id": f"msg-{new_id()}", "role": "user", "content": req.content,
                "timestamp": now, "status": "completed"}
    session.setdefault("messages", []).append(user_msg)

    # Определяем статус ответа по ключевым словам (рус/англ)
    content_lower = req.content.lower()
    if "error" in content_lower or "ошибка" in content_lower:
        status = "failed"
        asst_content = "Произошла ошибка при генерации ответа."
    elif "pending" in content_lower or "долго" in content_lower:
        status = "pending"
        asst_content = "Ответ генерируется..."
    else:
        answer = _generate_answer(req.content)
        status = "completed"
        asst_content = answer["content"]

    asst_msg = {
        "message_id": f"msg-{new_id()}", "role": "assistant", "status": status,
        "content": asst_content,
        "sources": answer.get("sources", []) if status == "completed" else [],
        "model_used": "gpt-4", "processing_time_ms": answer.get("processing_time_ms", 0),
        "timestamp": utcnow(), "feedback": None,
    }
    session["messages"].append(asst_msg)
    session["message_count"] = len(session["messages"])
    session["last_message_preview"] = asst_content[:80] + "..."
    session["updated_at"] = utcnow()

    _history.append({
        "history_id": f"hist-{new_id()}", "session_id": session_id, "created_at": utcnow(),
        "user_id": "anonymous", "user_name": "Аноним",
        "question": req.content, "answer_preview": asst_content[:80] + "...",
        "status": status, "source_count": len(asst_msg.get("sources", [])),
        "answer_id": f"ans-{new_id()}",
    })
    return {
        "message_id": asst_msg["message_id"], "session_id": session_id,
        "role": "assistant", "status": status, "content": asst_content,
        "timestamp": asst_msg["timestamp"],
    }

@app.post("/api/v1/chat/sessions/{session_id}/context")
async def manage_context(session_id: str, req: ContextActionRequest):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=error_response("SESSION_NOT_FOUND", "Сессия не найдена"))
    return {"session_id": session_id, "action": req.action, "status": "completed",
            "message": f"Контекст обновлён: {req.action}", "timestamp": utcnow()}

@app.post("/api/v1/chat/sessions/{session_id}/export")
async def export_session(session_id: str, req: ExportSessionRequest):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=error_response("SESSION_NOT_FOUND", "Сессия не найдена"))
    export_id = f"export-{new_id()}"
    _export_store[export_id] = {"export_id": export_id, "session_id": session_id, "format": req.format,
                                "status": "completed", "url": f"/exports/{export_id}.{req.format}",
                                "expires_at": utcnow(), "created_at": utcnow()}
    return _export_store[export_id]

@app.post("/api/v1/chat/feedback")
async def submit_feedback(req: FeedbackRequest):
    fb_id = f"fb-{new_id()}"
    _feedback_store.append({
        "feedback_id": fb_id, "session_id": req.session_id, "message_id": req.message_id,
        "rating": req.rating, "comment": req.comment, "aspects": req.aspects or [],
        "answer_id": req.answer_id, "useful": req.useful,
        "opened_citation_ids": req.opened_citation_ids or [], "created_at": utcnow(),
    })
    return {"feedback_id": fb_id, "saved": True,
            "metrics_changed": {"rated_answers": len(_feedback_store), "useful_rate": 0.78, "flagged_for_review": 0}}

@app.get("/api/v1/chat/history")
async def chat_history(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                      user_id: Optional[str] = Query(None)):
    items = sorted(_history, key=lambda h: h.get("created_at",""), reverse=True)
    if user_id:
        items = [h for h in items if h.get("user_id") == user_id]
    paged = paginate(items, page, page_size)
    return {"items": paged["items"], "meta": paged["meta"]}

@app.get("/api/v1/chat/history/export")
async def export_history(format: str = Query("csv")):
    export_id = f"export-{new_id()}"
    _export_store[export_id] = {"export_id": export_id, "format": format,
                                "url": f"/exports/history_{export_id}.{format}", "created_at": utcnow()}
    return _export_store[export_id]

@app.post("/api/v1/chat")
async def chat_ask(req: ChatRequest):
    query_lower = req.question.lower()
    if "неопределён" in query_lower or "ambiguous" in query_lower:
        return {"scenario": "needs_clarification", "missing_fields": ["document_ids"]}
    if "конфликт" in query_lower or "conflict" in query_lower:
        return {"scenario": "conflict", "conflicts": [{"type":"normative_conflict","sources":[]}]}
    if "сбой" in query_lower or "fail" in query_lower:
        return {"scenario": "failed", "answer_id": f"ans-{new_id()}", "status":"failed", "message":"Внутренняя ошибка"}
    if "долго" in query_lower or "pending" in query_lower:
        return {"scenario": "pending", "answer_id": f"ans-{new_id()}", "status":"pending", "message":"Запрос обрабатывается"}
    # default completed
    answer = _generate_answer(req.question)
    return {
        "scenario": "completed",
        "answer_id": f"ans-{new_id()}",
        "session_id": req.session_id or f"sess-{new_id()}",
        "status": "completed",
        "message": "Ответ сгенерирован",
        "answer_items": [{
            "number": 1,
            "text": answer["content"],
            "sources": [{
                "section_id": s["section_id"], "document_id": s["document_id"],
                "document_title": s["document_title"], "clause": s.get("clause",""),
                "page": s["page"], "excerpt": s["excerpt"],
                "page_preview_url": s.get("page_preview_url",""), "document_url": s.get("document_url",""),
            } for s in answer["sources"]]
        }],
        "latency_ms": answer["processing_time_ms"],
    }

@app.post("/api/v1/text/search")
async def text_search(req: TextSearchRequest):
    all_results = [
        {"section_id":"sect-001","document_id":"doc-001","document_title":"Спецификация",
         "page":3,"content":"Толщина стенки: 5 мм","score":0.95,"document_type":"specification"},
        {"section_id":"sect-002","document_id":"rd-001","document_title":"ГОСТ 2.109-73",
         "page":5,"content":"Не менее 4 мм","score":0.92,"document_type":"normative"},
    ]
    if req.document_ids:
        all_results = [r for r in all_results if r["document_id"] in req.document_ids]
    if req.filters and req.filters.get("document_type"):
        all_results = [r for r in all_results if r["document_type"] == req.filters["document_type"]]
    all_results.sort(key=lambda x: x["score"], reverse=True)
    top_k = min(req.top_k or 5, len(all_results))
    results = all_results[:top_k]
    return {
        "original_text": req.text,
        "analysis": {"normalized_query": req.text.lower(), "entities": [], "subqueries": [req.text]},
        "results": [{
            "section_id": r["section_id"], "document_id": r["document_id"],
            "document_title": r["document_title"], "page": r["page"],
            "content": r["content"], "score": r["score"],
            "document_type": r["document_type"], "matched_subquery": req.text,
        } for r in results],
        "total_found": len(all_results),
        "processing_time_ms": random.randint(100, 1000),
    }

@app.post("/api/v1/text/ask")
async def text_ask(req: TextAskRequest):
    answer = _generate_answer(req.text)
    return {
        "original_text": req.text,
        "normalized_question": req.text.lower(),
        "answer": answer["content"],
        "sources": [{
            "document_id": s["document_id"], "document_title": s["document_title"],
            "page": s["page"], "section_id": s["section_id"],
            "excerpt": s["excerpt"], "score": s["score"],
        } for s in answer["sources"]],
        "disclaimer": "Требуется инженерная верификация.",
        "processing_time_ms": answer["processing_time_ms"],
        "model_used": answer["model_used"],
    }

@app.get("/api/v1/system/health")
async def health():
    return {"status": "ok", "service": "query-service", "timestamp": utcnow()}

if __name__ == "__main__":
    import os
    port = int(os.getenv("QUERY_SERVICE_PORT", "8083"))
    uvicorn.run(app, host="0.0.0.0", port=port)