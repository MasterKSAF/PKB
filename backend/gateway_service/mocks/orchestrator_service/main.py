"""
Orchestrator Service — автономный шлюз API для документов, поиска, мониторинга.
Запуск: python main.py (порт ORCHESTRATOR_SERVICE_PORT, по умолчанию 8081)
"""

import copy
import hashlib
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import APIRouter, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Orchestrator Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

router = APIRouter()

# ── вспомогательные функции ──────────────────────────────────────────────
_counter = 0
def new_id() -> str:
    global _counter
    _counter += 1
    return str(_counter)

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def error_response(code: str, message: str, details: dict = None) -> JSONResponse:
    status_map = {
        "BAD_REQUEST": 400, "VALIDATION_ERROR": 400, "EMPTY_FILE": 400, "FILE_TOO_SMALL": 400,
        "EMPTY_DOCUMENT": 400,
        "UNAUTHORIZED": 401, "INVALID_TOKEN": 401,
        "FORBIDDEN": 403,
        "NOT_FOUND": 404, "DOCUMENT_NOT_FOUND": 404, "FILE_NOT_FOUND": 404,
        "DRAFT_NOT_FOUND": 404, "TASK_NOT_FOUND": 404,
        "DUPLICATE_FILE": 409, "DUPLICATE_DOCUMENT": 409,
        "DRAFT_ALREADY_DECIDED": 409, "DRAFT_ALREADY_PREVIEWED": 409,
        "FILE_TOO_LARGE": 413,
        "UNSUPPORTED_FILE_TYPE": 422, "VALIDATION_FAILED": 422,
        "INTERNAL_ERROR": 500, "OCR_FAILED": 500, "INDEXING_FAILED": 500,
        "NOT_IMPLEMENTED": 501, "GATEWAY_TIMEOUT": 504,
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

# ── сиды ──────────────────────────────────────────────────────────────────
SEED_DOCUMENTS = [
    {
        "document_id": "doc-001", "title": "Спецификация по ГОСТ 2.109", "doc_code": "2.109-73",
        "source_type": "GOST", "era": "CURRENT", "validity_status": "active",
        "jurisdiction": "RU", "issuing_body": "Госстандарт",
        "mks_oks_code": "01.100", "okstu_code": None,
        "classification_status": {"mks_status": "CONFIRMED", "okstu_status": "NOT_USED"},
        "successor_doc_id": None, "predecessor_doc_id": None, "chunk_container_id": None,
        "status": "completed", "file_size": 1024000, "pages_total": 12, "pages_processed": 12,
        "pages_failed": 0, "ocr_status": "completed", "index_status": "completed",
        "user_id": "u-001", "uploaded_by": "Иванов И.И.",
        "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T14:00:00Z",
        "chunk_count": 34, "chunk_validation": None,
        "metadata": {"year": 1981, "udc": "629.5.021", "tags": ["судостроение"]},
    }
]
SEED_DOCUMENT_ERRORS = [
    {"error_id": "err-001", "document_id": "doc-001", "stage": "ocr", "page": 5,
     "error_code": "LOW_CONFIDENCE", "error_message": "Качество распознавания ниже порога",
     "severity": "warning", "timestamp": "2026-04-27T10:01:00Z"}
]
SEED_METRICS = {
    "control_metrics": {"ocr_quality": 0.984, "retrieval_quality": 0.91, "answers_with_sources": 0.96, "avg_latency_ms": 1420},
    "answer_metrics": {"useful_rate": 0.84, "rated_answers": 43, "flagged_for_review": 5, "open_questions": 3},
    "logs": [{"time": "12:34:02", "type": "search", "text": "Поиск 'ледовый класс'", "level": "info"}],
}

_documents: Dict[str, dict] = {}
_document_errors: List[dict] = []
_versions: Dict[str, List[dict]] = {}
_chunks: Dict[str, List[dict]] = {}
_history: Dict[str, List[dict]] = {}
_approvals: Dict[str, dict] = {}
_metrics: dict = {}
_drafts: Dict[str, dict] = {}  # draft_id -> draft record (incl. raw_data, preview_metadata)
_tasks: Dict[str, dict] = {}  # task_id -> task record (cross-service pipeline tracking)

def init_data():
    global _documents, _document_errors, _versions, _chunks, _history, _approvals, _metrics
    _documents = {d["document_id"]: copy.deepcopy(d) for d in SEED_DOCUMENTS}
    _document_errors = copy.deepcopy(SEED_DOCUMENT_ERRORS)
    _metrics = copy.deepcopy(SEED_METRICS)
    for doc_id, doc in _documents.items():
        ver = doc.get("total_versions", 1)
        _versions[doc_id] = []
        for v in range(ver):
            _versions[doc_id].append({
                "version_id": f"ver-{new_id()}", "version_number": v+1, "document_id": doc_id,
                "title": doc.get("title",""), "file_size": doc.get("file_size",0),
                "content_hash_sha256": hashlib.sha256(f"{doc_id}-v{v+1}".encode()).hexdigest(),
                "title_hash_sha256": hashlib.sha256(doc.get("title","").encode()).hexdigest(),
                "status": "completed", "created_at": doc.get("created_at", utcnow()),
                "uploaded_by": doc.get("uploaded_by","")
            })
        _versions[doc_id].reverse()
        _history[doc_id] = [
            {"event_id": f"evt-{new_id()}", "document_id": doc_id, "from_status": None,
             "to_status": doc.get("status","uploaded"), "timestamp": doc.get("created_at", utcnow()),
             "user_id": doc.get("user_id","u-001"), "comment": "Документ создан"},
            {"event_id": f"evt-{new_id()}", "document_id": doc_id, "from_status": "uploaded",
             "to_status": doc.get("status","completed"), "timestamp": doc.get("updated_at", utcnow()),
             "user_id": doc.get("user_id","u-001"), "comment": "Обработка завершена"}
        ]
        cnt = doc.get("chunk_count", 0)
        _chunks[doc_id] = [
            {"chunk_id": f"chunk-{new_id()}", "chunk_number": i+1, "document_id": doc_id,
             "content": f"Фрагмент {i+1} документа {doc.get('title','')}",
             "page": (i % max(doc.get("pages_total",1),1)) + 1,
             "score": round(random.uniform(0.7, 0.99), 2),
             "is_indexed": doc.get("status") == "completed",
             "created_at": doc.get("created_at", utcnow())}
            for i in range(cnt)
        ]

init_data()

def _get_document(doc_id: str) -> dict:
    doc = _documents.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    return doc

def _get_page_block(doc_id: str, page_num: int) -> dict:
    return {
        "image_url": f"/api/v1/documents/{doc_id}/pages/{page_num}/image",
        "page": page_num, "width": 2480, "height": 3508,
        "blocks": [
            {"block_id": f"blk-{new_id()}", "type": "text", "coordinates": {"x":100,"y":200,"width":800,"height":50},
             "text": f"Текст на странице {page_num} документа {doc_id}.", "highlighted": False},
            {"block_id": f"blk-{new_id()}", "type": "table", "coordinates": {"x":100,"y":300,"width":800,"height":200},
             "text": "Таблица спецификации (mock)", "highlighted": False},
        ]
    }

def _get_queue_from_documents():
    queue = []
    for doc_id, doc in _documents.items():
        status = doc.get("status","unknown")
        if status in ("queued","processing","failed","uploaded","parsing","validation"):
            queue.append({
                "document_id": doc_id, "title": doc.get("title",""), "doc_code": doc.get("doc_code"),
                "source_type": doc.get("source_type",""), "status": status,
                "progress_percent": min(100, int((doc.get("pages_processed",0)/max(doc.get("pages_total",1),1))*100)),
                "current_step": "validation" if status == "validation" else "ocr",
                "steps": {"pipeline": {
                    "formation": {"status": "in_progress" if status != "failed" else "failed",
                                  "parsing": "completed" if status not in ("uploaded","parsing") else "pending",
                                  "validation": "in_progress" if status == "validation" else "pending",
                                  "registry": "pending"},
                    "indexation": {"status": "pending", "rag_indexing": "pending"}
                }},
                "user_id": doc.get("user_id",""), "uploaded_by": doc.get("uploaded_by",""),
                "created_at": doc.get("created_at",""), "started_at": doc.get("created_at"),
                "estimated_completion": None
            })
    return sorted(queue, key=lambda q: q.get("created_at",""), reverse=True)

# ── Pydantic модели ───────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = None

class ReprocessRequest(BaseModel):
    mode: Optional[str] = "full"

class DecideRequest(BaseModel):
    action: str  # "approve" | "reject"
    comment: Optional[str] = None

# ── утилиты для черновиков ────────────────────────────────────────────────
def _next_draft_id() -> int:
    """Черновики получают bigint-идентификаторы, монотонно возрастающие."""
    if not _drafts:
        return 420000
    return max(int(k) for k in _drafts.keys()) + 1

def _next_task_id() -> int:
    """task_id = draft_id для сквозной идентификации (см. common_api.md)."""
    return _next_draft_id()

def _build_title_hash(title: str) -> str:
    if not title:
        return ""
    return hashlib.sha256(title.encode("utf-8")).hexdigest()

def _get_draft(draft_id) -> dict:
    draft = _drafts.get(str(draft_id))
    if not draft:
        raise HTTPException(
            status_code=404,
            detail=error_response("DRAFT_NOT_FOUND", "Черновик не существует"),
        )
    return draft

# ── маршруты ─────────────────────────────────────────────────────────────
# NOTE: /api/v1/system/health зарегистрирован только в gateway.py (единая точка).
# Внутренний health для мониторинга — /api/v1/monitor/health.
@router.get("/api/v1/monitor/health")
async def monitor_health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": 86400,
        "services": {
            "auth": "ok",
            "rag_builder": "ok",
            "rag_search": "ok",
            "ocr": "ok",
            "validation": "ok",
            "integration": "ok",
        },
        "database": "ok",
        "search_index": "ok",
        "ocr_queue": "ok",
        "storage": "ok",
    }

@router.get("/api/v1/monitor/metrics")
async def get_metrics():
    return _metrics


# ===========================================================================
# DRAFTS (черновики) — обязательная точка входа при загрузке документа.
# Спецификация: docs/orchestrator_service_api.md, группа "drafts".
# ===========================================================================

@router.post("/api/v1/drafts", status_code=202)
async def create_draft(
    file: UploadFile = File(...),
    source_type: str = "OTHER",
    title: Optional[str] = None,
    doc_code: Optional[str] = None,
    mks_oks_code: Optional[str] = None,
    okstu_code: Optional[str] = None,
    era: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    issuing_body: Optional[str] = None,
    metadata: Optional[str] = None,
    request: Request = None,
):
    """Загрузка файла → создание черновика. Возвращает 202 + draft_id."""
    now = utcnow()
    user_id = "anonymous"
    if request and hasattr(request.state, "user"):
        user_id = request.state.user.get("user_id", "anonymous") or "anonymous"

    # 100 МБ лимит (см. common_api.md, edge-cases)
    if file.size is not None and file.size >= 100 * 1024 * 1024:
        return error_response("FILE_TOO_LARGE", "Файл превышает 100 МБ")
    content = await file.read()
    if len(content) == 0:
        return error_response("EMPTY_FILE", "Загружен пустой файл (0 байт)")
    if len(content) < 1024:
        return error_response("FILE_TOO_SMALL", "Файл менее 1 КБ")

    file_hash = hashlib.sha256(content).hexdigest()
    title_value = title or (file.filename or "untitled")
    title_hash = _build_title_hash(title_value)
    filename = file.filename or "untitled"
    document_key = f"sha256:{file_hash[:16]}"
    file_key = f"f-{file_hash[:12]}"

    draft_id = _next_draft_id()
    task_id = _next_task_id()
    version_id = task_id + 1

    draft = {
        "draft_id": draft_id,
        "task_id": task_id,
        "version_id": version_id,
        "file_key": file_key,
        "document_key": document_key,
        "filename": filename,
        "title": title_value,
        "doc_code": doc_code,
        "source_type": source_type,
        "mks_oks_code": mks_oks_code,
        "okstu_code": okstu_code,
        "era": era,
        "jurisdiction": jurisdiction,
        "issuing_body": issuing_body,
        "metadata_raw": metadata,
        "metadata": {},
        "status": "uploaded",
        "confidence": None,
        "preview_metadata": None,
        "raw_data": None,
        "error_code": None,
        "error_message": None,
        "approved_document_id": None,
        "file_hash_sha256": file_hash,
        "title_hash_sha256": title_hash,
        "file_size_bytes": len(content),
        "is_duplicate_file": False,
        "is_duplicate_document": False,
        "created_by": user_id,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }

    # Парсим metadata JSON-строку (если передана)
    if metadata:
        try:
            import json as _json
            draft["metadata"] = _json.loads(metadata)
        except Exception:
            draft["metadata"] = {}

    # detect duplicate
    for existing in _drafts.values():
        if existing.get("file_hash_sha256") == file_hash and existing.get("status") in (
            "uploaded", "previewing", "ready_for_approve"
        ):
            draft["is_duplicate_file"] = True
            draft["status"] = "uploaded"
            break

    _drafts[str(draft_id)] = draft
    _tasks[str(task_id)] = {
        "task_id": task_id,
        "draft_id": draft_id,
        "document_id": None,
        "status": "uploaded",
        "pipeline_stage": "upload",
        "progress_percent": 0,
        "created_at": now,
        "updated_at": now,
    }

    return {
        "draft_id": draft_id,
        "task_id": task_id,
        "version_id": version_id,
        "status": draft["status"],
        "file_hash_sha256": file_hash,
        "file_size_bytes": draft["file_size_bytes"],
        "is_duplicate_file": draft["is_duplicate_file"],
        "is_duplicate_document": False,
        "title_hash_sha256": title_hash,
        "created_at": now,
    }


@router.get("/api/v1/drafts")
async def list_drafts(
    document_key: str = Query(..., min_length=1),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    items = [d for d in _drafts.values() if d.get("document_key") == document_key]
    if status:
        items = [d for d in items if d.get("status") == status]
    items.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    paged = paginate(items, page, page_size)
    return {"items": paged["items"], "meta": paged["meta"]}


@router.get("/api/v1/drafts/{draft_id}")
async def get_draft(draft_id: str):
    draft = _get_draft(draft_id)
    return draft


@router.get("/api/v1/drafts/{draft_id}/preview")
async def get_draft_preview(draft_id: str):
    draft = _get_draft(draft_id)
    return {
        "draft_id": draft["draft_id"],
        "task_id": draft["task_id"],
        "file_key": draft["file_key"],
        "document_key": draft["document_key"],
        "status": draft["status"],
        "confidence": draft.get("confidence"),
        "preview_metadata": draft.get("preview_metadata"),
        "created_at": draft["created_at"],
    }


@router.post("/api/v1/drafts/{draft_id}/preview", status_code=202)
async def start_draft_preview(draft_id: str):
    draft = _get_draft(draft_id)
    if draft["status"] in ("previewing", "ready_for_approve"):
        return error_response(
            "DRAFT_ALREADY_PREVIEWED",
            "Preview уже запущен или завершён",
        )
    now = utcnow()
    draft["status"] = "previewing"
    draft["updated_at"] = now
    task = _tasks.get(str(draft["task_id"]))
    if task:
        task["status"] = "previewing"
        task["pipeline_stage"] = "preview"
        task["updated_at"] = now
    return {
        "draft_id": draft["draft_id"],
        "status": "previewing",
        "estimated_completion": now,
    }


@router.get("/api/v1/drafts/{draft_id}/preview/status")
async def draft_preview_status(draft_id: str, longpoll: int = Query(15, ge=0, le=60)):
    """Статус preview с longpoll-механикой (см. common_api.md)."""
    draft = _get_draft(draft_id)
    status = draft["status"]
    if status == "previewing":
        # Эмулируем завершение preview после первого обращения (mock).
        now = utcnow()
        draft["status"] = "ready_for_approve"
        draft["confidence"] = round(random.uniform(0.75, 0.98), 2)
        draft["preview_metadata"] = {
            "doc_code": draft.get("doc_code") or "—",
            "title": draft.get("title") or "—",
            "document_type": "normative",
            "year": (draft.get("metadata") or {}).get("year"),
            "revision": None,
        }
        draft["updated_at"] = now
        task = _tasks.get(str(draft["task_id"]))
        if task:
            task["status"] = "ready_for_approve"
            task["pipeline_stage"] = "decision"
            task["progress_percent"] = 40
            task["updated_at"] = now
    return {
        "draft_id": draft["draft_id"],
        "status": draft["status"],
        "ocr_parser_status": "completed",
        "converter_validator_status": "completed",
        "preview": draft.get("preview_metadata") or {},
        "duplicates": [],
        "decision_required": draft["status"] == "ready_for_approve",
    }


@router.patch("/api/v1/drafts/{draft_id}/decide")
async def decide_draft(draft_id: str, req: DecideRequest):
    """Решение по черновику: approve → создание документа, reject → discarded."""
    draft = _get_draft(draft_id)
    if draft["status"] != "ready_for_approve":
        return error_response(
            "DRAFT_ALREADY_DECIDED",
            f"Решение уже принято (статус: {draft['status']})",
        )
    if req.action not in ("approve", "reject"):
        return error_response(
            "VALIDATION_ERROR",
            "Некорректный action: допустимы approve|reject",
        )
    now = utcnow()
    user_id = "anonymous"

    if req.action == "approve":
        # Создаём документ в реестре (мок)
        new_doc_id = f"doc-{new_id()}"
        new_doc = {
            "document_id": new_doc_id, "title": draft.get("title") or f"Документ {new_doc_id}",
            "doc_code": draft.get("doc_code"), "source_type": draft.get("source_type") or "OTHER",
            "era": draft.get("era") or "CURRENT", "validity_status": "active",
            "jurisdiction": draft.get("jurisdiction") or "RF",
            "issuing_body": draft.get("issuing_body"),
            "mks_oks_code": draft.get("mks_oks_code"),
            "okstu_code": draft.get("okstu_code"),
            "classification_status": {"mks_status": "unknown", "okstu_status": "unknown"},
            "successor_doc_id": None, "predecessor_doc_id": None, "chunk_container_id": None,
            "status": "created", "file_size": draft.get("file_size_bytes", 0),
            "pages_total": 1, "pages_processed": 1, "pages_failed": 0,
            "ocr_status": "completed", "index_status": "pending",
            "user_id": user_id, "uploaded_by": user_id,
            "metadata": draft.get("metadata") or {},
            "created_at": now, "updated_at": now,
            "chunk_count": 0, "chunk_validation": None,
        }
        _documents[new_doc_id] = new_doc
        _versions[new_doc_id] = [{
            "version_id": draft["version_id"], "version_number": 1,
            "document_id": new_doc_id, "title": new_doc["title"],
            "file_size": new_doc["file_size"],
            "content_hash_sha256": draft["file_hash_sha256"],
            "title_hash_sha256": draft["title_hash_sha256"],
            "status": "completed", "created_at": now, "uploaded_by": user_id,
        }]
        _history[new_doc_id] = [{
            "event_id": f"evt-{new_id()}", "document_id": new_doc_id,
            "from_status": None, "to_status": "created", "timestamp": now,
            "user_id": user_id,
            "comment": f"Создано из черновика {draft['draft_id']}: {req.comment or ''}".strip(),
        }]
        _chunks[new_doc_id] = []

        draft["status"] = "approved"
        draft["approved_document_id"] = new_doc_id
        draft["updated_at"] = now
        task = _tasks.get(str(draft["task_id"]))
        if task:
            task["status"] = "created"
            task["document_id"] = new_doc_id
            task["pipeline_stage"] = "registry"
            task["progress_percent"] = 80
            task["updated_at"] = now
        return {
            "draft_id": draft["draft_id"],
            "status": "approved",
            "action": "approve",
            "approved_document_id": new_doc_id,
            "message": "Черновик завершён, документ создан в Registry. Запущен Пайплайн 2 (индексация).",
            "decided_by": user_id,
            "decided_at": now,
        }
    else:
        draft["status"] = "discarded"
        draft["updated_at"] = now
        task = _tasks.get(str(draft["task_id"]))
        if task:
            task["status"] = "failed"
            task["pipeline_stage"] = "decision"
            task["updated_at"] = now
        return {
            "draft_id": draft["draft_id"],
            "status": "discarded",
            "action": "reject",
            "approved_document_id": None,
            "message": "Черновик отклонён. Можно загрузить файл повторно для новой попытки.",
            "decided_by": user_id,
            "decided_at": now,
        }


@router.delete("/api/v1/drafts/{draft_id}")
async def delete_draft(draft_id: str):
    draft = _get_draft(draft_id)
    now = utcnow()
    draft["deleted_at"] = now
    draft["status"] = "discarded"
    draft["updated_at"] = now
    task = _tasks.get(str(draft["task_id"]))
    if task:
        task["status"] = "failed"
        task["updated_at"] = now
    return {"draft_id": draft["draft_id"], "deleted_at": now}


# ===========================================================================
# TASKS — внутренний (internal) сквозной ID для отслеживания пайплайна.
# ===========================================================================

@router.get("/api/v1/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Сквозной статус задачи (internal). UI не должен вызывать напрямую."""
    task = _tasks.get(str(task_id))
    if not task:
        return error_response("TASK_NOT_FOUND", "Задача не найдена")
    return {
        "task_id": task["task_id"],
        "draft_id": task.get("draft_id"),
        "document_id": task.get("document_id"),
        "status": task["status"],
        "pipeline_stage": task.get("pipeline_stage", "upload"),
        "progress_percent": task.get("progress_percent", 0),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    }


# ВАЖНО: search и queue ДО {doc_id}
@router.post("/api/v1/documents/search")
async def search_post(req: SearchRequest):
    mock_results = [
        {"section_id": "sec-001", "document_id": "doc-001", "document_title": "Спецификация по ГОСТ 2.109",
         "document_type": "specification", "clause": "Основные требования", "page": 3,
         "content": "Толщина стенки корпуса: 5 мм, материал: Сталь 45", "score": 0.95,
         "page_preview_url": "/documents/doc-001/pages/3/preview", "document_url": "/documents/doc-001/file"},
        {"section_id": "sec-002", "document_id": "rd-001", "document_title": "ГОСТ 2.109-73",
         "document_type": "normative", "clause": "Раздел 3", "page": 5,
         "content": "Толщина стенки не менее 4 мм", "score": 0.92,
         "page_preview_url": "/documents/rd-001/pages/5/preview", "document_url": "/documents/rd-001/file"},
    ]
    if req.document_ids:
        mock_results = [r for r in mock_results if r["document_id"] in req.document_ids]
    if req.filters and req.filters.get("document_type"):
        mock_results = [r for r in mock_results if r["document_type"] == req.filters["document_type"]]
    mock_results.sort(key=lambda r: r["score"], reverse=True)
    top_k = min(req.top_k or 10, len(mock_results))
    return {
        "query": req.query,
        "items": mock_results[:top_k],
        "total_found": len(mock_results),
        "processing_time_ms": random.randint(200, 1500),
    }

@router.get("/api/v1/documents/search")
async def search_get(q: str = Query(...), document_ids: Optional[str] = None,
                     top_k: int = 10, page: int = 1, page_size: int = 50):
    req = SearchRequest(query=q, document_ids=document_ids.split(",") if document_ids else None, top_k=top_k)
    return await search_post(req)

@router.get("/api/v1/documents/queue")
async def document_queue(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    queue = _get_queue_from_documents()
    paged = paginate(queue, page, page_size)
    return {"queue": paged["items"], "meta": {"total_in_queue": len(queue), **paged["meta"]}}

@router.post("/api/v1/documents", status_code=202)
async def upload_document(file: UploadFile = File(...), request: Request = None):
    doc_id = f"doc-{new_id()}"
    now = utcnow()
    user_id = "anonymous"
    if request and hasattr(request.state, "user"):
        user_id = request.state.user.get("user_id", "anonymous") or "anonymous"
    content_bytes = (file.filename or f"document_{doc_id}").encode()
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    title_hash = hashlib.sha256((file.filename or "untitled").encode()).hexdigest()
    version_id = f"ver-{new_id()}"
    new_doc = {
        "document_id": doc_id, "filename": file.filename, "title": file.filename or f"Документ {doc_id}",
        "doc_code": None, "source_type": "GOST", "era": "CURRENT", "validity_status": "active",
        "jurisdiction": "RF", "issuing_body": None, "mks_oks_code": None, "okstu_code": None,
        "classification_status": {"mks_status":"unknown","okstu_status":"unknown"},
        "successor_doc_id": None, "predecessor_doc_id": None, "chunk_container_id": None,
        "status": "uploaded", "file_size": 1024000, "pages_total": 0, "pages_processed": 0,
        "pages_failed": 0, "ocr_status": "pending", "index_status": "pending",
        "user_id": user_id, "uploaded_by": user_id,
        "metadata": {"year":2026,"udc":"","tags":[]},
        "pages": [], "parameters": {}, "extraction_confidence": 0.0, "unconfirmed_fields": [],
        "created_at": now, "updated_at": now, "registry_doc_id": None,
        "chunk_count": 0, "chunk_validation": None,
    }
    _documents[doc_id] = new_doc
    _versions[doc_id] = [{"version_id": version_id, "version_number": 1, "document_id": doc_id,
                          "title": new_doc["title"], "file_size": new_doc["file_size"],
                          "content_hash_sha256": content_hash, "title_hash_sha256": title_hash,
                          "status": "uploaded", "created_at": now, "uploaded_by": user_id}]
    _history[doc_id] = [{"event_id": f"evt-{new_id()}", "document_id": doc_id, "from_status": None,
                         "to_status": "uploaded", "timestamp": now, "user_id": user_id, "comment": "Документ загружен"}]
    _chunks[doc_id] = []
    return {"task_id": f"task-{new_id()}", "version_id": version_id, "status": "uploaded",
            "content_hash_sha256": content_hash, "is_duplicate_file": False,
            "is_duplicate_document": False, "title_hash_sha256": title_hash, "created_at": now}

@router.get("/api/v1/documents")
async def list_documents(
    status: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    items = list(_documents.values())
    if status:
        items = [d for d in items if d.get("status") == status]
    if source_type:
        items = [d for d in items if d.get("source_type") == source_type]
    if search:
        s = search.lower()
        items = [d for d in items if s in d.get("title","").lower() or s in d.get("filename","").lower()]
    items.sort(key=lambda d: d.get("created_at",""), reverse=True)
    summary = {
        "total": len(_documents),
        "uploaded": sum(1 for d in _documents.values() if d.get("status")=="uploaded"),
        "parsing": sum(1 for d in _documents.values() if d.get("status")=="parsing"),
        "validation": sum(1 for d in _documents.values() if d.get("status")=="validation"),
        "review_required": sum(1 for d in _documents.values() if d.get("status")=="review_required"),
        "ready_for_promotion": sum(1 for d in _documents.values() if d.get("status") in ("completed","ready_for_promotion")),
        "approved": sum(1 for d in _documents.values() if d.get("status")=="approved"),
        "failed": sum(1 for d in _documents.values() if d.get("status")=="failed"),
        "archived": sum(1 for d in _documents.values() if d.get("status")=="archived"),
    }
    result = []
    for d in items:
        result.append({
            "document_id": d["document_id"], "title": d.get("title",""), "doc_code": d.get("doc_code"),
            "source_type": d.get("source_type",""), "era": d.get("era",""), "validity_status": d.get("validity_status",""),
            "jurisdiction": d.get("jurisdiction"), "issuing_body": d.get("issuing_body"),
            "mks_oks_code": d.get("mks_oks_code"), "okstu_code": d.get("okstu_code"),
            "classification_status": d.get("classification_status", {}),
            "status": d.get("status",""), "latest_version": d.get("total_versions",1),
            "total_versions": d.get("total_versions",1), "chunk_count": d.get("chunk_count",0),
            "chunk_validation": d.get("chunk_validation"), "user_id": d.get("user_id",""),
            "uploaded_by": d.get("uploaded_by",""), "created_at": d.get("created_at",""), "updated_at": d.get("updated_at",""),
        })
    paged = paginate(result, page, page_size)
    return {"summary": summary, "items": paged["items"], "meta": paged["meta"]}

@router.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: str):
    doc = _get_document(doc_id)
    return {
        "document_id": doc["document_id"], "title": doc.get("title",""), "doc_code": doc.get("doc_code"),
        "source_type": doc.get("source_type",""), "title_hash_sha256": hashlib.sha256(doc.get("title","").encode()).hexdigest(),
        "status": doc.get("status",""), "era": doc.get("era",""), "validity_status": doc.get("validity_status",""),
        "jurisdiction": doc.get("jurisdiction"), "issuing_body": doc.get("issuing_body"),
        "mks_oks_code": doc.get("mks_oks_code"), "okstu_code": doc.get("okstu_code"),
        "classification_status": doc.get("classification_status", {}),
        "successor_doc_id": doc.get("successor_doc_id"), "predecessor_doc_id": doc.get("predecessor_doc_id"),
        "chunk_container_id": doc.get("chunk_container_id"), "metadata": doc.get("metadata", {}),
        "latest_version": {"version_id": _versions.get(doc_id, [{}])[0].get("version_id",""),
                           "version_number": doc.get("total_versions",1),
                           "format_code": "pdf_digital", "content_hash_sha256": "...", "size_bytes": doc.get("file_size",0)},
        "total_versions": doc.get("total_versions",1),
        "user_id": doc.get("user_id",""), "uploaded_by": doc.get("uploaded_by",""),
        "created_by": doc.get("user_id",""), "updated_by": doc.get("user_id",""),
        "created_at": doc.get("created_at",""), "updated_at": doc.get("updated_at",""),
    }

@router.get("/api/v1/documents/{doc_id}/status")
async def document_status(doc_id: str, longpoll: int = 15):
    # NOTE: Формат ответа приведён к спецификации orchestrator_service_api.md (L344-447).
    # Статусы: processing → pipeline.formation.preview + decision + indexation;
    # approval_required → pipeline.formation.preview;
    # completed → pipeline.formation + indexation + chunk_summary.
    doc = _get_document(doc_id)
    status = doc.get("status", "unknown")
    now = utcnow()

    # Определяем маппинг статусов документа в статусы спецификации
    if status in ("completed", "approved", "ready_for_promotion"):
        spec_status = "completed"
        progress = 100.0
    elif status in ("uploaded", "parsing", "validation", "processing", "queued"):
        spec_status = "processing"
        progress = 60.0
    elif status == "review_required":
        spec_status = "approval_required"
        progress = 40.0
    elif status == "failed":
        spec_status = "failed"
        progress = 0.0
    else:
        spec_status = status
        progress = 50.0

    if spec_status == "processing":
        # NOTE: processing → formation.preview (ocr_parser, converter_validator) + decision + indexation
        formation_status = "processing"
        preview_status = "completed" if status not in ("uploaded",) else "in_progress"
        decision_status = "pending"
        indexation_status = "pending"
        is_indexing = status in ("validation", "processing")
        return {
            "document_id": doc_id,
            "status": spec_status,
            "progress_percent": progress,
            "steps": {
                "pipeline": {
                    "formation": {
                        "status": formation_status,
                        "preview": {
                            "status": preview_status,
                            "ocr_parser": {"status": preview_status, "pages_processed": doc.get("pages_processed", 0)},
                            "converter_validator": {"status": preview_status, "metadata_extracted": preview_status == "completed"},
                        },
                        "decision": {
                            "status": decision_status,
                            "action": None,
                        },
                    },
                    "indexation": {
                        "status": indexation_status,
                        "rag_indexing": {"status": "in_progress" if is_indexing else "pending"},
                    },
                }
            },
            "started_at": doc.get("created_at", ""),
            "estimated_completion": now,
        }
    elif spec_status == "approval_required":
        # NOTE: approval_required → только formation.preview, без indexation
        return {
            "document_id": doc_id,
            "status": spec_status,
            "progress_percent": progress,
            "steps": {
                "pipeline": {
                    "formation": {
                        "status": "ready_for_approve",
                        "preview": {"status": "completed"},
                    }
                }
            },
        }
    elif spec_status == "completed":
        # NOTE: completed → formation + indexation + chunk_summary
        return {
            "document_id": doc_id,
            "status": spec_status,
            "progress_percent": progress,
            "steps": {
                "pipeline": {
                    "formation": {
                        "status": "completed",
                        "preview": {"status": "completed"},
                        "decision": {"status": "completed", "action": "approve"},
                    },
                    "indexation": {
                        "status": "completed",
                        "rag_indexing": {
                            "status": "completed",
                            "chunks_generated": doc.get("chunk_count", 0),
                        },
                    },
                }
            },
            "chunk_summary": {
                "sections": doc.get("pages_processed", 0),
                "chunks": doc.get("chunk_count", 0),
                "embeddings": doc.get("chunk_count", 0),
            },
            "started_at": doc.get("created_at", ""),
            "completed_at": doc.get("updated_at", ""),
        }
    else:
        # failed / unknown — минимальный ответ
        return {
            "document_id": doc_id,
            "status": spec_status,
            "progress_percent": progress,
            "steps": {
                "pipeline": {
                    "formation": {"status": "failed" if spec_status == "failed" else "unknown"},
                    "indexation": {"status": "failed" if spec_status == "failed" else "unknown"},
                }
            },
            "started_at": doc.get("created_at", ""),
        }

@router.get("/api/v1/documents/{doc_id}/file")
async def get_file(doc_id: str):
    doc = _get_document(doc_id)
    return {"document_id": doc_id, "version_id": _versions.get(doc_id, [{}])[0].get("version_id",""),
            "content_type": "application/pdf", "file_url": f"/files/{doc_id}/full.pdf"}

@router.post("/api/v1/documents/{doc_id}/approve", status_code=202)
async def approve_document(doc_id: str, request: Request = None):
    doc = _get_document(doc_id)
    doc["status"] = "approved"
    doc["updated_at"] = utcnow()
    return {"document_id": doc_id, "status": "approved", "promotion_task_id": f"promo-{new_id()}",
            "approved_by": "system", "approved_at": utcnow()}

@router.get("/api/v1/documents/{doc_id}/history")
async def document_history(doc_id: str):
    _get_document(doc_id)
    hist = _history.get(doc_id, [])
    return {"document_id": doc_id, "history": hist, "meta": {"total": len(hist)}}

@router.post("/api/v1/documents/{doc_id}/reprocess", status_code=202)
async def reprocess(doc_id: str, req: Optional[ReprocessRequest] = None):
    doc = _get_document(doc_id)
    doc["status"] = "parsing"
    doc["updated_at"] = utcnow()
    return {"task_id": f"task-{new_id()}", "version_id": _versions[doc_id][0]["version_id"],
            "status": "parsing", "content_hash_sha256": "...", "is_duplicate_file": False,
            "is_duplicate_document": False, "title_hash_sha256": "...", "created_at": utcnow()}

@router.delete("/api/v1/documents/{doc_id}")
async def delete_document(doc_id: str):
    _get_document(doc_id)
    del _documents[doc_id]
    _versions.pop(doc_id, None); _chunks.pop(doc_id, None); _history.pop(doc_id, None)
    return {"document_id": doc_id, "deleted_at": utcnow()}

@router.get("/api/v1/documents/{doc_id}/errors")
async def document_errors(doc_id: str, page: int = 1, page_size: int = 20):
    _get_document(doc_id)
    errs = [e for e in _document_errors if e["document_id"] == doc_id]
    paged = paginate(errs, page, page_size)
    return {"errors": paged["items"], "meta": paged["meta"]}

@router.post("/api/v1/documents/{doc_id}/versions", status_code=202)
async def add_version(doc_id: str, file: UploadFile = File(...)):
    doc = _get_document(doc_id)
    now = utcnow()
    ver_num = doc.get("total_versions", 1) + 1
    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()
    version_id = new_id()
    task_id = new_id()
    new_ver = {
        "version_id": version_id, "version_number": ver_num, "document_id": doc_id,
        "title": doc.get("title",""),
        "file_size": len(content) or doc.get("file_size",0),
        "content_hash_sha256": content_hash,
        "title_hash_sha256": _build_title_hash(doc.get("title","")),
        "status": "uploaded", "created_at": now, "uploaded_by": "system",
    }
    if doc_id not in _versions:
        _versions[doc_id] = []
    _versions[doc_id].insert(0, new_ver)
    doc["total_versions"] = ver_num
    doc["latest_version"] = ver_num
    doc["updated_at"] = now
    return {
        "document_id": doc_id,
        "version_id": version_id,
        "version_number": ver_num,
        "status": "uploaded",
        "task_id": task_id,
        "file_hash_sha256": content_hash,
        "is_duplicate_file": False,
        "created_at": now,
    }

@router.get("/api/v1/documents/{doc_id}/versions")
async def list_versions(
    doc_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Список версий файла в формате docs (format_code/format_label/file_key/size_bytes)."""
    doc = _get_document(doc_id)
    raw = _versions.get(doc_id, [])
    items = []
    for v in raw:
        items.append({
            "version_id": int(v["version_id"]) if str(v["version_id"]).isdigit() else v["version_id"],
            "version_number": v.get("version_number", 1),
            "format_code": "pdf_digital",
            "format_label": "PDF (цифровой)",
            "file_key": f"{doc_id}/v{v.get('version_number',1)}/{v.get('content_hash_sha256','unknown')[:32]}.pdf",
            "file_hash_sha256": v.get("content_hash_sha256"),
            "size_bytes": v.get("file_size", 0),
            "uploaded_at": v.get("created_at"),
            "uploaded_by": v.get("uploaded_by"),
        })
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "document_id": doc_id,
        "versions": items[start:end],
        "meta": {"total": len(items), "page": page, "page_size": page_size},
    }

@router.get("/api/v1/documents/{doc_id}/pages")
async def list_pages(doc_id: str, page: int = 1, page_size: int = 50):
    doc = _get_document(doc_id)
    pages = doc.get("pages", [])
    if not pages and doc.get("pages_total",0) > 0:
        pages = [{"page": i, "width": 2480, "height": 3508, "ocr_status": "completed",
                  "confidence": 0.95, "has_text_layer": True}
                 for i in range(1, doc["pages_total"]+1)]
    paged = paginate(pages, page, page_size)
    return {"document_id": doc_id, "pages_total": doc.get("pages_total",0),
            "pages": paged["items"], "meta": paged["meta"]}

@router.get("/api/v1/documents/{doc_id}/pages/{page_num}")
async def get_page(doc_id: str, page_num: int, highlight: Optional[str] = None):
    _get_document(doc_id)
    return _get_page_block(doc_id, page_num)

@router.get("/api/v1/documents/{doc_id}/pages/{page_num}/text")
async def page_text(doc_id: str, page_num: int):
    _get_document(doc_id)
    blocks = _get_page_block(doc_id, page_num)["blocks"]
    return {"page": page_num, "full_text": " ".join(b["text"] for b in blocks), "blocks": blocks}

@router.get("/api/v1/documents/{doc_id}/pages/{page_num}/preview")
async def page_preview(doc_id: str, page_num: int):
    doc = _get_document(doc_id)
    return {"document_id": doc_id, "page": page_num, "preview_url": f"/preview/{doc_id}/{page_num}"}

@router.get("/api/v1/documents/{doc_id}/parameters")
async def parameters(doc_id: str):
    doc = _get_document(doc_id)
    return {"document_id": doc_id, "parameters": doc.get("parameters", {}),
            "extraction_confidence": doc.get("extraction_confidence",0.0),
            "unconfirmed_fields": doc.get("unconfirmed_fields",[]), "updated_at": doc.get("updated_at","")}

app.include_router(router)

if __name__ == "__main__":
    import os
    port = int(os.getenv("ORCHESTRATOR_SERVICE_PORT", "8081"))
    uvicorn.run(app, host="0.0.0.0", port=port)