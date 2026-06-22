"""
Orchestrator handlers — extracted from orchestrator_service/main.py.
All data stores imported from mocks.common.
"""

import hashlib
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mocks.common import (
    _documents, _document_errors, _versions, _chunks, _history,
    _approvals, _metrics, _drafts, _tasks,
    new_id, utcnow, error_response, paginate,
)

logger = logging.getLogger("orchestrator_service")

router = APIRouter()


# ── Pydantic модели ──────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[int]] = None
    top_k: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = None


class ReprocessRequest(BaseModel):
    mode: Optional[str] = "full"


class DecideRequest(BaseModel):
    action: str = ""
    decision: str = ""
    comment: Optional[str] = None
    metadata_overrides: Optional[Dict[str, Any]] = None  # OR-3


# ── утилиты ──────────────────────────────────────────────────────────────────

def _next_draft_id() -> int:
    return new_id()


def _next_task_id() -> int:
    return new_id()


def _build_title_hash(title: str) -> str:
    if not title:
        return ""
    return hashlib.sha256(title.encode("utf-8")).hexdigest()


def _get_draft(draft_id: int) -> dict:
    draft = _drafts.get(draft_id)
    if not draft:
        raise HTTPException(
            status_code=404,
            detail=error_response("DRAFT_NOT_FOUND", "Черновик не существует"),
        )
    return draft


def _get_document(doc_id: int) -> dict:
    doc = _documents.get(doc_id)
    if not doc:
        logger.info("get_document: doc_id=%s NOT FOUND, creating mock", doc_id)
        now = utcnow()
        doc = {
            "document_id": doc_id,
            "title": f"Документ {doc_id}",
            "doc_code": f"DOC-{doc_id:04d}",
            "source_type": "GOST",
            "status": "completed",
            "era": "CURRENT",
            "validity_status": "active",
            "jurisdiction": "RU",
            "issuing_body": "Госстандарт",
            "group": "ПО4",
            "mks_oks_code": "31.240",
            "okstu_code": None,
            "classification_status": {"mks": ["31.240"], "okstu": [], "udk": [], "subject_area": ["Электроника", "Монтажные изделия"]},
            "successor_doc_id": None,
            "predecessor_doc_id": None,
            "chunk_container_id": None,
            "file_size": 1024000,
            "pages_total": 10,
            "pages_processed": 10,
            "pages_failed": 0,
            "ocr_status": "completed",
            "index_status": "completed",
            "user_id": 1,
            "created_by": "system",
            "total_versions": 1,
            "chunk_count": 34,
            "chunk_validation": None,
            "metadata": {"year": 2024, "udk_code": "629.5", "tags": []},
            "pages": [{"page": i, "width": 2480, "height": 3508,
                       "ocr_status": "completed", "confidence": 0.95,
                       "has_text_layer": True}
                      for i in range(1, 11)],
            "parameters": {},
            "extraction_confidence": 0.0,
            "unconfirmed_fields": [],
            "created_at": now,
            "updated_at": now,
            "registry_doc_id": doc_id,
        }
        _documents[doc_id] = doc
        _versions[doc_id] = [{"version_id": new_id(), "version_number": 1,
                               "document_id": doc_id, "title": doc["title"],
                               "file_size": doc["file_size"],
                               "content_hash_sha256": hashlib.sha256(f"{doc_id}".encode()).hexdigest(),
                               "title_hash_sha256": hashlib.sha256(doc["title"].encode()).hexdigest(),
                               "status": "completed", "created_at": now,
                               "created_by": "system"}]
        _history[doc_id] = [{"event_id": new_id(), "document_id": doc_id,
                              "from_status": None, "to_status": "completed",
                              "timestamp": now, "user_id": 1, "comment": "Документ создан автоматически"}]
        _chunks[doc_id] = []
        _document_errors.extend([
            {"error_id": new_id(), "document_id": doc_id, "stage": "ocr",
             "page": 1, "error_code": "LOW_CONFIDENCE",
             "error_message": "Качество распознавания ниже порога",
             "severity": "warning", "timestamp": now}
        ])
        logger.info("get_document: auto-created mock for doc_id=%s", doc_id)
    return doc


def _get_page_block(doc_id: int, page_num: int) -> dict:
    return {
        "image_url": f"/api/v1/documents/{doc_id}/pages/{page_num}/image",
        "page": page_num, "width": 2480, "height": 3508,
        "blocks": [
            {"block_id": new_id(), "type": "text", "coordinates": {"x": 100, "y": 200, "width": 800, "height": 50},
             "text": f"Текст на странице {page_num} документа {doc_id}.", "highlighted": False},
            {"block_id": new_id(), "type": "table", "coordinates": {"x": 100, "y": 300, "width": 800, "height": 200},
             "text": "Таблица спецификации (mock)", "highlighted": False},
        ]
    }


def _get_queue_from_documents():
    queue = []
    for doc_id, doc in _documents.items():
        status = doc.get("status", "unknown")
        if status in ("queued", "processing", "failed", "uploaded", "parsing", "validation"):
            queue.append({
                "document_id": doc_id, "title": doc.get("title", ""), "doc_code": doc.get("doc_code"),
                "source_type": doc.get("source_type", ""), "status": status,
                "progress_percent": min(100, int((doc.get("pages_processed", 0) / max(doc.get("pages_total", 1), 1)) * 100)),
                "current_step": "validation" if status == "validation" else "ocr",
                "steps": {"pipeline": {
                    "formation": {"status": "in_progress" if status != "failed" else "failed",
                                  "parsing": "completed" if status not in ("uploaded", "parsing") else "pending",
                                  "validation": "in_progress" if status == "validation" else "pending",
                                  "registry": "pending"},
                    "indexation": {"status": "pending", "rag_indexing": "pending"}
                }},
                "user_id": doc.get("user_id", ""), "created_by": doc.get("created_by", ""),
                "created_at": doc.get("created_at", ""), "started_at": doc.get("created_at"),
                "estimated_completion": None
            })
    return sorted(queue, key=lambda q: q.get("created_at", ""), reverse=True)


# ── Маршруты ─────────────────────────────────────────────────────────────────

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


# ===========================================================================
# DRAFTS
# ===========================================================================

@router.post("/api/v1/drafts", status_code=202)
@router.post("/api/v1/drafts/", status_code=202)
async def create_draft(request: Request):
    now = utcnow()
    user_id = "anonymous"

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        body = await request.json()
        logger.info("create_draft (JSON): body=%s", body)
        file_key = body.get("file_key", f"json-{new_id()}")
        document_key = body.get("document_key", f"json-doc-{new_id()}")
        title = body.get("title", document_key)
        doc_code = body.get("doc_code")
        source_type = body.get("source_type", "OTHER")

        draft_id = _next_draft_id()
        task_id = _next_task_id()
        version_id = task_id + 1

        file_hash = hashlib.sha256(document_key.encode()).hexdigest()
        title_hash = _build_title_hash(title)

        draft = {
            "draft_id": draft_id,
            "task_id": task_id,
            "version_id": version_id,
            "file_key": file_key,
            "document_key": document_key,
            "filename": f"{file_key}.pdf",
            "title": title,
            "doc_code": body.get("doc_code"),
            "source_type": source_type,
            "mks_oks_code": body.get("mks_oks_code"),
            "okstu_code": body.get("okstu_code"),
            "status": "uploaded",
            "confidence": None,
            "preview_metadata": None,
            "raw_data": None,
            "error_code": None,
            "error_message": None,
            "approved_document_id": None,
            "file_hash_sha256": file_hash,
            "title_hash_sha256": title_hash,
            "file_size_bytes": 0,
            "is_duplicate_file": False,
            "is_duplicate_document": False,
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }

        _drafts[draft_id] = draft
        _tasks[task_id] = {
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
            "file_size_bytes": 0,
            "is_duplicate_file": False,
            "is_duplicate_document": False,
            "title_hash_sha256": title_hash,
            "created_at": now,
        }

    form = await request.form()
    file = form.get("file")
    if file is None or not hasattr(file, "read"):
        if not form:
            raise HTTPException(status_code=400, detail=error_response("VALIDATION_ERROR", "Файл не передан"))
        # multipart без файла, но с полями формы — обрабатываем как JSON (checker кейс)
        body = {k: v for k, v in form.items()}
        file_key = body.get("file_key", f"json-{new_id()}")
        document_key = body.get("document_key", f"json-doc-{new_id()}")
        title = body.get("title", document_key)
        doc_code = body.get("doc_code")
        source_type = body.get("source_type", "OTHER")

        draft_id = _next_draft_id()
        task_id = _next_task_id()
        version_id = task_id + 1

        file_hash = hashlib.sha256(document_key.encode()).hexdigest()
        title_hash = _build_title_hash(title)

        draft = {
            "draft_id": draft_id, "task_id": task_id, "version_id": version_id,
            "file_key": file_key, "document_key": document_key,
            "filename": f"{file_key}.pdf", "title": title,
            "doc_code": doc_code, "source_type": source_type,
            "mks_oks_code": body.get("mks_oks_code"), "okstu_code": body.get("okstu_code"),
            "status": "uploaded", "confidence": None, "preview_metadata": None,
            "raw_data": None, "error_code": None, "error_message": None,
            "approved_document_id": None, "file_hash_sha256": file_hash,
            "title_hash_sha256": title_hash, "file_size_bytes": 0,
            "is_duplicate_file": False, "is_duplicate_document": False,
            "created_by": user_id, "created_at": now, "updated_at": now, "deleted_at": None,
        }
        _drafts[draft_id] = draft
        _tasks[task_id] = {
            "task_id": task_id, "draft_id": draft_id, "document_id": None,
            "status": "uploaded", "pipeline_stage": "upload",
            "progress_percent": 0, "created_at": now, "updated_at": now,
        }
        return {
            "draft_id": draft_id, "task_id": task_id, "version_id": version_id,
            "status": draft["status"], "file_hash_sha256": file_hash,
            "file_size_bytes": 0, "is_duplicate_file": False,
            "is_duplicate_document": False, "title_hash_sha256": title_hash,
            "created_at": now,
        }

    source_type = form.get("source_type", "OTHER")
    title = form.get("title")
    doc_code = form.get("doc_code")
    mks_oks_code = form.get("mks_oks_code")
    okstu_code = form.get("okstu_code")
    era = form.get("era")
    jurisdiction = form.get("jurisdiction")
    issuing_body = form.get("issuing_body")
    metadata_str = form.get("metadata")

    if request and hasattr(request.state, "user"):
        user_id = request.state.user.get("user_id", "anonymous") or "anonymous"

    if file.size is not None and file.size >= 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail=error_response("FILE_TOO_LARGE", "Файл превышает 100 МБ"))
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail=error_response("EMPTY_FILE", "Загружен пустой файл (0 байт)"))
    if len(content) < 1024:
        raise HTTPException(status_code=400, detail=error_response("FILE_TOO_SMALL", "Файл менее 1 КБ"))

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
        "metadata_raw": metadata_str,
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

    if metadata_str:
        try:
            import json as _json
            draft["metadata"] = _json.loads(metadata_str)
        except Exception:
            draft["metadata"] = {}

    for existing in _drafts.values():
        if existing.get("file_hash_sha256") == file_hash and existing.get("status") in (
            "uploaded", "previewing", "ready_for_approve"
        ):
            draft["is_duplicate_file"] = True
            draft["status"] = "uploaded"
            break

    _drafts[draft_id] = draft
    _tasks[task_id] = {
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
    document_key: Optional[str] = Query(None, description="Фильтр по document_key (бизнес-ключ документа)"),
    draft_id: Optional[int] = Query(None, description="Фильтр по draft_id (конкретный черновик)"),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    logger.info("list_drafts: document_key=%s draft_id=%s status=%s", document_key, draft_id, status)
    items = list(_drafts.values())
    if document_key:
        items = [d for d in items if d.get("document_key") == document_key]
    if draft_id:
        items = [d for d in items if d.get("draft_id") == draft_id]
    if status:
        items = [d for d in items if d.get("status") == status]
    items.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    paged = paginate(items, page, page_size)
    return {"items": paged["items"], "meta": paged["meta"]}


@router.get("/api/v1/drafts/{draft_id}")
async def get_draft(draft_id: int):
    draft = _get_draft(draft_id)
    # OR-6: уведомления качества
    notifications = draft.get("notifications", [])
    return {
        "draft_id": draft["draft_id"],
        "task_id": draft["task_id"],
        "file_key": draft.get("file_key"),
        "document_key": draft.get("document_key"),
        "status": draft.get("status"),
        "document_id": draft.get("approved_document_id"),
        "version_id": draft.get("version_id"),
        "file_hash_sha256": draft.get("file_hash_sha256"),
        "is_new_document": draft.get("approved_document_id") is None and draft.get("status") not in ("discarded",),
        "has_notifications": len(notifications) > 0,
        "critical_count": sum(1 for n in notifications if n.get("severity") == "critical"),
        "notifications": notifications,
        "created_at": draft.get("created_at"),
        "updated_at": draft.get("updated_at"),
    }


@router.get("/api/v1/drafts/{draft_id}/preview")
async def get_draft_preview(draft_id: int):
    draft = _get_draft(draft_id)
    preview = draft.get("preview_metadata") or {}
    return {
        "draft_id": draft["draft_id"],
        "task_id": draft["task_id"],
        "file_key": draft["file_key"],
        "document_key": draft["document_key"],
        "status": draft["status"],
        "confidence": draft.get("confidence"),
        "preview_metadata": {
            "doc_code": preview.get("doc_code"),
            "title": preview.get("title"),
            "document_type": preview.get("document_type"),
            "source_type": preview.get("source_type"),
            "era": preview.get("era"),
            "jurisdiction": preview.get("jurisdiction"),
            "issuing_body": preview.get("issuing_body"),
            "year": preview.get("year"),
            "revision": preview.get("revision"),
            "mks_oks_code": preview.get("mks_oks_code"),
            "okstu_code": preview.get("okstu_code"),
        },
        "created_at": draft["created_at"],
        "updated_at": draft.get("updated_at"),
    }


@router.post("/api/v1/drafts/{draft_id}/preview", status_code=202)
async def start_draft_preview(draft_id: int):
    draft = _get_draft(draft_id)
    if draft["status"] != "uploaded":
        if draft["status"] in ("previewing", "ready_for_approve"):
            raise HTTPException(status_code=409, detail=error_response(
                "DRAFT_ALREADY_PREVIEWED",
                "Preview уже запущен или завершён (статус: %s)" % draft["status"],
            ))
        raise HTTPException(status_code=409, detail=error_response(
            "DRAFT_ALREADY_PREVIEWED",
            "Preview недоступен для черновика в статусе: %s" % draft["status"],
        ))
    now = utcnow()
    draft["status"] = "previewing"
    draft["updated_at"] = now
    task = _tasks.get(draft["task_id"])
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
async def draft_preview_status(draft_id: int, longpoll: int = Query(15, ge=0, le=60)):
    draft = _get_draft(draft_id)
    status = draft["status"]
    if status == "previewing":
        now = utcnow()
        draft["status"] = "ready_for_approve"
        draft["confidence"] = round(random.uniform(0.75, 0.98), 2)
        draft["preview_metadata"] = {
            "doc_code": draft.get("doc_code") or "—",
            "title": draft.get("title") or "—",
            "document_type": "normative",
            "source_type": draft.get("source_type") or "OTHER",
            "era": draft.get("era") or "CURRENT",
            "jurisdiction": draft.get("jurisdiction") or "RU",
            "issuing_body": draft.get("issuing_body"),
            "year": (draft.get("metadata") or {}).get("year"),
            "revision": None,
            "mks_oks_code": draft.get("mks_oks_code"),
            "okstu_code": draft.get("okstu_code"),
        }
        draft["updated_at"] = now
        task = _tasks.get(draft["task_id"])
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
async def decide_draft(draft_id: int, req: DecideRequest):
    draft = _get_draft(draft_id)
    if draft["status"] != "ready_for_approve":
        raise HTTPException(status_code=409, detail=error_response(
            "DRAFT_ALREADY_DECIDED",
            f"Решение уже принято (статус: {draft['status']})",
        ))
    action = req.action or req.decision
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail=error_response(
            "VALIDATION_ERROR",
            "Некорректный action: допустимы approve|reject",
        ))
    now = utcnow()
    user_id = "anonymous"

    if action == "approve":
        new_doc_id = new_id()
        # OR-3: применение metadata_overrides
        metadata = dict(draft.get("metadata") or {})
        if req.metadata_overrides:
            metadata.update(req.metadata_overrides)
        new_doc = {
            "document_id": new_doc_id, "title": draft.get("title") or f"Документ {new_doc_id}",
            "doc_code": draft.get("doc_code"), "source_type": draft.get("source_type") or "OTHER",
            "era": draft.get("era") or "CURRENT", "validity_status": "active",
            "jurisdiction": draft.get("jurisdiction") or "RF",
            "issuing_body": draft.get("issuing_body"),
            "group": draft.get("group"),
            "mks_oks_code": draft.get("mks_oks_code"),
            "okstu_code": draft.get("okstu_code"),
            "classification_status": {"mks": [], "okstu": [], "udk": [], "subject_area": []},
            "successor_doc_id": None, "predecessor_doc_id": None, "chunk_container_id": None,
            "status": "created", "file_size": draft.get("file_size_bytes", 0),
            "pages_total": 1, "pages_processed": 1, "pages_failed": 0,
            "ocr_status": "completed", "index_status": "pending",
            "user_id": user_id, "created_by": user_id,
            "metadata": metadata,
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
            "status": "completed", "created_at": now, "created_by": user_id,
        }]
        _history[new_doc_id] = [{
            "event_id": new_id(), "document_id": new_doc_id,
            "from_status": None, "to_status": "created", "timestamp": now,
            "user_id": user_id,
            "comment": f"Создано из черновика {draft['draft_id']}: {req.comment or ''}".strip(),
        }]
        _chunks[new_doc_id] = []

        draft["status"] = "approved"
        draft["approved_document_id"] = new_doc_id
        draft["updated_at"] = now
        task = _tasks.get(draft["task_id"])
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
        task = _tasks.get(draft["task_id"])
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
async def delete_draft(draft_id: int):
    draft = _get_draft(draft_id)
    now = utcnow()
    draft["deleted_at"] = now
    draft["status"] = "discarded"
    draft["updated_at"] = now
    task = _tasks.get(draft["task_id"])
    if task:
        task["status"] = "failed"
        task["updated_at"] = now
    return {"draft_id": draft["draft_id"], "deleted_at": now}


# ===========================================================================
# TASKS
# ===========================================================================


def _generate_task_steps(task: dict) -> list:
    """Генерирует шаги задачи на основе её статуса и pipeline_stage.

    Маппинг pipeline_stage → набор step_name с service_name для мока.
    """
    stage = task.get("pipeline_stage", "upload")
    now = task.get("updated_at", task.get("created_at", ""))

    # Карта: pipeline_stage → имя шага, на котором мы находимся
    # Используется для failed-статуса: на каком шаге произошла ошибка
    STAGE_TO_STEP: dict[str, str] = {
        "upload": "upload",
        "preview": "preview_ocr",
        "decision": "decision_approve",
        "full": "full_ocr",
        "registry": "registry_save",
        "indexation": "indexation",
    }

    # Все возможные шаги в порядке выполнения
    # (step_name, service_name)
    all_step_defs = [
        ("upload", "Orchestrator"),
        ("preview_ocr", "OCR Service"),
        ("preview_parse", "Parser"),
        ("preview_convert", "Converter-validator"),
        ("decision_approve", "Orchestrator"),
        ("full_ocr", "OCR Service"),
        ("full_convert", "Converter-validator"),
        ("registry_save", "Registry"),
        ("indexation", "RAG Builder"),
    ]

    # Определяем статус для каждого шага в нормальном режиме
    def _step_status(step_name: str) -> str:
        if stage == "upload":
            return "completed" if step_name == "upload" else "pending"
        if stage == "preview":
            if step_name == "upload":
                return "completed"
            if step_name == "preview_ocr":
                return "running"
            return "pending"
        if stage in ("decision",):
            completed_until = {"upload", "preview_ocr", "preview_parse", "preview_convert"}
            if step_name in completed_until:
                return "completed"
            return "pending"
        if stage in ("full",):
            completed_until = {"upload", "preview_ocr", "preview_parse", "preview_convert", "decision_approve"}
            if step_name in completed_until:
                return "completed"
            return "pending"
        if stage in ("registry",):
            completed_until = {"upload", "preview_ocr", "preview_parse", "preview_convert",
                              "decision_approve", "full_ocr", "full_convert"}
            if step_name in completed_until:
                return "completed"
            return "pending"
        if stage in ("indexation",):
            completed_until = {"upload", "preview_ocr", "preview_parse", "preview_convert",
                              "decision_approve", "full_ocr", "full_convert", "registry_save"}
            if step_name in completed_until:
                return "completed"
            if step_name == "indexation":
                return "running"
            return "pending"
        return "pending"

    # Если статус failed — определяем индекс шага, на котором ошибка
    if task.get("status") == "failed":
        failed_step_name = STAGE_TO_STEP.get(stage, "upload")
        failed_index = -1
        for i, (name, _) in enumerate(all_step_defs):
            if name == failed_step_name:
                failed_index = i
                break
        steps = []
        for i, (name, svc) in enumerate(all_step_defs):
            if i < failed_index:
                steps.append({"step_name": name, "service_name": svc, "status": "completed",
                              "input_data": {"mock": True}, "output_data": {"mock": True},
                              "started_at": now, "completed_at": now})
            elif i == failed_index:
                steps.append({"step_name": name, "service_name": svc, "status": "failed",
                              "input_data": {"mock": True}, "output_data": None,
                              "started_at": now, "completed_at": now})
            else:
                steps.append({"step_name": name, "service_name": svc, "status": "cancelled",
                              "input_data": None, "output_data": None,
                              "started_at": None, "completed_at": None})
        return steps

    # Нормальный режим
    steps = []
    for name, svc in all_step_defs:
        st = _step_status(name)
        if st == "pending":
            steps.append({"step_name": name, "service_name": svc, "status": "pending",
                          "input_data": None, "output_data": None,
                          "started_at": None, "completed_at": None})
        else:
            is_completed = st == "completed"
            steps.append({"step_name": name, "service_name": svc, "status": st,
                          "input_data": {"mock": True}, "output_data": {"mock": True},
                          "started_at": now,
                          "completed_at": now if is_completed else None})
    return steps


@router.get("/api/v1/tasks/{task_id}/status")
async def get_task_status(task_id: int):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=error_response("TASK_NOT_FOUND", "Задача не найдена"))
    steps = _generate_task_steps(task)
    return {
        "task_id": task["task_id"],
        "draft_id": task.get("draft_id"),
        "document_id": task.get("document_id"),
        "status": task["status"],
        "pipeline_stage": task.get("pipeline_stage", "upload"),
        "progress_percent": task.get("progress_percent", 0),
        "steps": steps,
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    }


@router.get("/api/v1/tasks/{task_id}/steps")
async def get_task_steps(task_id: int):
    """Шаги задачи (без общей обёртки статуса).

    Доступ: system_admin (на уровне Gateway).
    """
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=error_response("TASK_NOT_FOUND", "Задача не найдена"))
    steps = _generate_task_steps(task)
    return {
        "task_id": task["task_id"],
        "steps": steps,
    }


@router.get("/api/v1/drafts/{draft_id}/tasks")
async def get_draft_tasks(draft_id: int):
    """Список задач для черновика.

    Доступ: system_admin, knowledge_admin (на уровне Gateway).
    """
    draft = _get_draft(draft_id)
    # Ищем все задачи, привязанные к черновику
    draft_tasks = [
        {
            "task_id": t["task_id"],
            "status": t.get("status", "unknown"),
            "pipeline_stage": t.get("pipeline_stage", "unknown"),
            "initiated_by": "system",
            "created_at": t.get("created_at", ""),
            "updated_at": t.get("updated_at", ""),
        }
        for t in _tasks.values()
        if t.get("draft_id") == draft_id
    ]
    return {
        "draft_id": draft_id,
        "tasks": draft_tasks,
    }


# ── Documents ──────────────────────────────────────────────────────────────

@router.post("/api/v1/documents/search")
async def search_post(req: SearchRequest):
    mock_results = [
        {"section_id": 1, "document_id": 1, "document_title": "Спецификация по ГОСТ 2.109",
         "document_type": "specification", "clause": "Основные требования", "page": 3,
         "content": "Толщина стенки корпуса: 5 мм, материал: Сталь 45", "score": 0.95,
         "page_preview_url": "/documents/1/pages/3/preview", "document_url": "/documents/1/file"},
        {"section_id": 2, "document_id": 2, "document_title": "ГОСТ 2.109-73",
         "document_type": "normative", "clause": "Раздел 3", "page": 5,
         "content": "Толщина стенки не менее 4 мм", "score": 0.92,
         "page_preview_url": "/documents/2/pages/5/preview", "document_url": "/documents/2/file"},
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
async def search_get(q: str = Query(default="", description="Поисковый запрос"),
                     document_ids: Optional[str] = None,
                     top_k: int = 10, page: int = 1, page_size: int = 50):
    logger.info("search_get: q=%s top_k=%d document_ids=%s", q, top_k, document_ids)
    if not q:
        return {"query": "", "items": [], "total_found": 0, "processing_time_ms": 0}
    req = SearchRequest(query=q, document_ids=document_ids.split(",") if document_ids else None, top_k=top_k)
    return await search_post(req)


@router.get("/api/v1/documents/queue")
async def document_queue(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    queue = _get_queue_from_documents()
    paged = paginate(queue, page, page_size)
    return {"queue": paged["items"], "meta": {"total_in_queue": len(queue), **paged["meta"]}}


@router.post("/api/v1/documents")
async def upload_document_deprecated():
    """Устаревший эндпоинт. Используйте POST /drafts (OR-11)."""
    raise HTTPException(status_code=410, detail=error_response(
        "ENDPOINT_DEPRECATED",
        "POST /documents устарел. Используйте POST /drafts как единую точку входа.",
    ))


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
        items = [d for d in items if s in d.get("title", "").lower() or s in d.get("filename", "").lower()]
    items.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    summary = {
        "total": len(_documents),
        "uploaded": sum(1 for d in _documents.values() if d.get("status") == "uploaded"),
        "parsing": sum(1 for d in _documents.values() if d.get("status") == "parsing"),
        "validation": sum(1 for d in _documents.values() if d.get("status") == "validation"),
        "review_required": sum(1 for d in _documents.values() if d.get("status") == "review_required"),
        "ready_for_promotion": sum(1 for d in _documents.values() if d.get("status") in ("completed", "ready_for_promotion")),
        "approved": sum(1 for d in _documents.values() if d.get("status") == "approved"),
        "failed": sum(1 for d in _documents.values() if d.get("status") == "failed"),
        "archived": sum(1 for d in _documents.values() if d.get("status") == "archived"),
    }
    result = []
    for d in items:
        result.append({
            "document_id": d["document_id"], "title": d.get("title", ""), "doc_code": d.get("doc_code"),
            "source_type": d.get("source_type", ""), "era": d.get("era", ""), "validity_status": d.get("validity_status", ""),
            "jurisdiction": d.get("jurisdiction"), "issuing_body": d.get("issuing_body"),
            "group": d.get("group"),
            "mks_oks_code": d.get("mks_oks_code"), "okstu_code": d.get("okstu_code"),
            "classification_status": d.get("classification_status", {}),
            "status": d.get("status", ""), "latest_version": d.get("total_versions", 1),
            "total_versions": d.get("total_versions", 1), "chunk_count": d.get("chunk_count", 0),
            "chunk_validation": d.get("chunk_validation"), "user_id": d.get("user_id", ""),
            "created_by": d.get("created_by", ""), "created_at": d.get("created_at", ""), "updated_at": d.get("updated_at", "")
        })
    paged = paginate(result, page, page_size)
    return {"summary": summary, "items": paged["items"], "meta": paged["meta"]}


@router.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: int):
    doc = _get_document(doc_id)
    return {
        "id": doc["document_id"],
        "document_id": doc["document_id"], "title": doc.get("title", ""), "doc_code": doc.get("doc_code"),
        "source_type": doc.get("source_type", ""), "title_hash_sha256": hashlib.sha256(doc.get("title", "").encode()).hexdigest(),
        "status": doc.get("status", ""), "era": doc.get("era", ""), "validity_status": doc.get("validity_status", ""),
        "jurisdiction": doc.get("jurisdiction"), "issuing_body": doc.get("issuing_body"),
        "group": doc.get("group"),
        "mks_oks_code": doc.get("mks_oks_code"), "okstu_code": doc.get("okstu_code"),
        "classification_status": doc.get("classification_status", {}),
        "successor_doc_id": doc.get("successor_doc_id"), "predecessor_doc_id": doc.get("predecessor_doc_id"),
        "chunk_container_id": doc.get("chunk_container_id"), "metadata": doc.get("metadata", {}),
        "latest_version": {"version_id": _versions.get(doc_id, [{}])[0].get("version_id", ""),
                           "version_number": doc.get("total_versions", 1),
                           "format_code": "pdf_digital", "content_hash_sha256": "...", "size_bytes": doc.get("file_size", 0)},
        "total_versions": doc.get("total_versions", 1),
        "user_id": doc.get("user_id", ""), "created_by": doc.get("created_by", ""),
        "updated_by": doc.get("user_id", ""),
        "created_at": doc.get("created_at", ""), "updated_at": doc.get("updated_at", ""),
    }


@router.get("/api/v1/documents/{doc_id}/status")
async def document_status(doc_id: int, longpoll: int = 15):
    doc = _get_document(doc_id)
    status = doc.get("status", "unknown")
    now = utcnow()

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
async def get_file(doc_id: int):
    doc = _get_document(doc_id)
    return {"document_id": doc_id, "version_id": _versions.get(doc_id, [{}])[0].get("version_id", ""),
            "content_type": "application/pdf", "file_url": f"/files/{doc_id}/full.pdf"}


@router.post("/api/v1/documents/{doc_id}/approve")
async def approve_document_deprecated(doc_id: int):
    """Устаревший эндпоинт. Используйте PATCH /drafts/{draft_id}/decide (OR-12)."""
    raise HTTPException(status_code=410, detail=error_response(
        "ENDPOINT_DEPRECATED",
        "POST /documents/{id}/approve устарел. Используйте PATCH /drafts/{id}/decide.",
    ))


@router.get("/api/v1/documents/{doc_id}/history")
async def document_history(doc_id: int):
    _get_document(doc_id)
    hist = _history.get(doc_id, [])
    return {"document_id": doc_id, "history": hist, "meta": {"total": len(hist)}}


@router.post("/api/v1/documents/{doc_id}/reprocess", status_code=202)
async def reprocess(doc_id: int, req: Optional[ReprocessRequest] = None):
    doc = _get_document(doc_id)
    doc["status"] = "parsing"
    doc["updated_at"] = utcnow()
    return {"task_id": new_id(), "version_id": _versions[doc_id][0]["version_id"],
            "status": "parsing", "content_hash_sha256": "...", "is_duplicate_file": False,
            "is_duplicate_document": False, "title_hash_sha256": "...", "created_at": utcnow()}


@router.delete("/api/v1/documents/{doc_id}")
async def delete_document(doc_id: int):
    _get_document(doc_id)
    del _documents[doc_id]
    _versions.pop(doc_id, None)
    _chunks.pop(doc_id, None)
    _history.pop(doc_id, None)
    return {"document_id": doc_id, "deleted_at": utcnow()}


@router.get("/api/v1/documents/{doc_id}/errors")
async def document_errors(doc_id: int, page: int = 1, page_size: int = 20):
    _get_document(doc_id)
    errs = [e for e in _document_errors if e["document_id"] == doc_id]
    paged = paginate(errs, page, page_size)
    return {"errors": paged["items"], "meta": paged["meta"]}


@router.post("/api/v1/documents/{doc_id}/versions", status_code=202)
async def add_version(doc_id: int, request: Request):
    doc = _get_document(doc_id)
    now = utcnow()
    ver_num = doc.get("total_versions", 1) + 1
    version_id = new_id()
    task_id = new_id()
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        file_key = body.get("file_key", f"v{ver_num}-{new_id()}")
        content_hash = hashlib.sha256(file_key.encode()).hexdigest()
        new_ver = {
            "version_id": version_id, "version_number": ver_num, "document_id": doc_id,
            "title": doc.get("title", ""),
            "file_size": doc.get("file_size", 0),
            "content_hash_sha256": content_hash,
            "title_hash_sha256": _build_title_hash(doc.get("title", "")),
            "status": "uploaded", "created_at": now, "created_by": "system",
        }
    else:
        form = await request.form()
        file = form.get("file")
        if file is None or not hasattr(file, "read"):
            raise HTTPException(status_code=400, detail=error_response("VALIDATION_ERROR", "Файл не передан"))
        content = await file.read()
        content_hash = hashlib.sha256(content).hexdigest()
        new_ver = {
            "version_id": version_id, "version_number": ver_num, "document_id": doc_id,
            "title": doc.get("title", ""),
            "file_size": len(content) or doc.get("file_size", 0),
            "content_hash_sha256": content_hash,
            "title_hash_sha256": _build_title_hash(doc.get("title", "")),
            "status": "uploaded", "created_at": now, "created_by": "system",
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
    doc_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    doc = _get_document(doc_id)
    raw = _versions.get(doc_id, [])
    items = []
    for v in raw:
        items.append({
            "version_id": v["version_id"],
            "version_number": v.get("version_number", 1),
            "format_code": "pdf_digital",
            "format_label": "PDF (цифровой)",
            "file_key": f"{doc_id}/v{v.get('version_number', 1)}/{v.get('content_hash_sha256', 'unknown')[:32]}.pdf",
            "file_hash_sha256": v.get("content_hash_sha256"),
            "size_bytes": v.get("file_size", 0),
            "created_at": v.get("created_at"),
            "created_by": v.get("created_by"),
        })
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "document_id": doc_id,
        "versions": items[start:end],
        "meta": {"total": len(items), "page": page, "page_size": page_size},
    }


@router.get("/api/v1/documents/{doc_id}/pages")
async def list_pages(doc_id: int, page: int = 1, page_size: int = 50):
    doc = _get_document(doc_id)
    pages = doc.get("pages", [])
    if not pages and doc.get("pages_total", 0) > 0:
        pages = [{"page": i, "width": 2480, "height": 3508, "ocr_status": "completed",
                  "confidence": 0.95, "has_text_layer": True}
                 for i in range(1, doc["pages_total"] + 1)]
    paged = paginate(pages, page, page_size)
    return {"document_id": doc_id, "pages_total": doc.get("pages_total", 0),
            "pages": paged["items"], "meta": paged["meta"]}


@router.get("/api/v1/documents/{doc_id}/pages/{page_num}")
async def get_page(doc_id: int, page_num: int, highlight: Optional[str] = None):
    _get_document(doc_id)
    return _get_page_block(doc_id, page_num)


@router.get("/api/v1/documents/{doc_id}/pages/{page_num}/text")
async def page_text(doc_id: int, page_num: int):
    _get_document(doc_id)
    blocks = _get_page_block(doc_id, page_num)["blocks"]
    return {"page": page_num, "full_text": " ".join(b["text"] for b in blocks), "blocks": blocks}


@router.get("/api/v1/documents/{doc_id}/pages/{page_num}/preview")
async def page_preview(doc_id: int, page_num: int):
    doc = _get_document(doc_id)
    return {"document_id": doc_id, "page": page_num, "preview_url": f"/preview/{doc_id}/{page_num}"}


@router.get("/api/v1/documents/{doc_id}/parameters")
async def parameters(doc_id: int):
    doc = _get_document(doc_id)
    return {"document_id": doc_id, "parameters": doc.get("parameters", {}),
            "extraction_confidence": doc.get("extraction_confidence", 0.0),
            "unconfirmed_fields": doc.get("unconfirmed_fields", []), "updated_at": doc.get("updated_at", "")}
