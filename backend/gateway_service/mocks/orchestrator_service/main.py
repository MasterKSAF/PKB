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
        "BAD_REQUEST": 400, "VALIDATION_ERROR": 400,
        "UNAUTHORIZED": 401, "INVALID_TOKEN": 401,
        "FORBIDDEN": 403,
        "NOT_FOUND": 404, "DOCUMENT_NOT_FOUND": 404, "FILE_NOT_FOUND": 404,
        "DUPLICATE_DOCUMENT": 409,
        "VALIDATION_FAILED": 422,
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

# ── маршруты ─────────────────────────────────────────────────────────────
@router.get("/api/v1/system/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "uptime_seconds": 86400,
            "services": {"auth":"ok","rag":"ok","ocr":"ok","validation":"ok","integration":"ok"},
            "database":"ok","search_index":"ok","ocr_queue":"ok","storage":"ok"}

@router.get("/api/v1/monitor/health")
async def monitor_health():
    return await health()

@router.get("/api/v1/monitor/metrics")
async def get_metrics():
    return _metrics

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
    doc = _get_document(doc_id)
    status = doc.get("status")
    steps = {
        "pipeline": {
            "formation": {"status": "completed" if status in ("completed","approved","ready_for_promotion") else "in_progress",
                          "parsing": {"status": "completed" if status not in ("uploaded","parsing") else "pending"},
                          "validation": {"status": "valid" if status == "ready_for_promotion" else "pending"},
                          "registry": {"status": "completed" if status in ("approved","ready_for_promotion") else "pending"}},
            "indexation": {"status": "completed" if status == "ready_for_promotion" else "pending",
                           "rag_indexing": {"status": "completed" if status == "ready_for_promotion" else "pending"}}
        }
    }
    progress = 100.0 if status in ("completed","approved","ready_for_promotion") else 60.0
    return {
        "document_id": doc_id, "status": status, "progress_percent": progress,
        "pipeline": steps["pipeline"],   # исправлено: вынесено на верхний уровень
        "started_at": doc.get("created_at",""), "completed_at": doc.get("updated_at","") if progress == 100 else None,
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

@router.post("/api/v1/documents/{doc_id}/versions", status_code=201)
async def add_version(doc_id: str, file: UploadFile = File(...)):
    doc = _get_document(doc_id)
    now = utcnow()
    ver_num = doc.get("total_versions", 1) + 1
    content_hash = hashlib.sha256(file.filename.encode()).hexdigest()
    version_id = f"ver-{new_id()}"
    new_ver = {
        "version_id": version_id, "version_number": ver_num, "document_id": doc_id,
        "title": doc.get("title",""), "file_size": doc.get("file_size",0),
        "content_hash_sha256": content_hash, "title_hash_sha256": "...",
        "status": "uploaded", "created_at": now, "uploaded_by": "system"
    }
    if doc_id not in _versions:
        _versions[doc_id] = []
    _versions[doc_id].insert(0, new_ver)
    doc["total_versions"] = ver_num
    doc["latest_version"] = ver_num
    doc["updated_at"] = now
    return {"document_id": doc_id, "version_id": version_id, "version_number": ver_num,
            "status": "uploaded", "task_id": f"task-{new_id()}", "content_hash_sha256": content_hash,
            "is_duplicate_file": False, "created_at": now}

@router.get("/api/v1/documents/{doc_id}/versions")
async def list_versions(doc_id: str):
    _get_document(doc_id)
    vers = _versions.get(doc_id, [])
    return {"document_id": doc_id, "versions": vers, "meta": {"total": len(vers)}}

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