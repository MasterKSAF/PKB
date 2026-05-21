"""
Orchestrator Service Mock
Основной шлюз API — документы, поиск, мониторинг (in-memory).
Порт: 8081
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
import hashlib
import random
from typing import Any, Dict, List, Optional

from common import (
    SEED_DOCUMENT_ERRORS,
    SEED_DOCUMENTS,
    SEED_METRICS,
    error_response,
    new_id,
    paginate,
    utcnow,
)
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")

# ---------------------------------------------------------------------------
# In-memory хранилища
# ---------------------------------------------------------------------------

_documents: Dict[str, dict] = {}
_document_errors: List[dict] = {}
_versions: Dict[str, List[dict]] = {}
_chunks: Dict[str, List[dict]] = {}
_history: Dict[str, List[dict]] = {}
_approvals: Dict[str, dict] = {}
_metrics: dict = {}

# Счётчик для ID
_doc_id_counter: int = 100
_version_counter: int = 200


def _init_data():
    global \
        _documents, \
        _document_errors, \
        _versions, \
        _chunks, \
        _history, \
        _approvals, \
        _metrics
    if _documents:
        return
    _documents = {d["document_id"]: copy.deepcopy(d) for d in SEED_DOCUMENTS}
    _document_errors = copy.deepcopy(SEED_DOCUMENT_ERRORS)
    _metrics = copy.deepcopy(SEED_METRICS)

    # Инициализация версий для seed-документов
    for doc_id, doc in _documents.items():
        ver = doc.get("total_versions", 1)
        _versions[doc_id] = [
            {
                "version_id": f"ver-{new_id()}",
                "version_number": v + 1,
                "document_id": doc_id,
                "title": doc.get("title", ""),
                "file_size": doc.get("file_size", 0),
                "content_hash_sha256": hashlib.sha256(
                    f"{doc_id}-v{v + 1}".encode()
                ).hexdigest(),
                "title_hash_sha256": hashlib.sha256(
                    doc.get("title", "").encode()
                ).hexdigest(),
                "status": "completed",
                "created_at": doc.get("created_at", utcnow()),
                "uploaded_by": doc.get("uploaded_by", ""),
            }
            for v in range(ver)
        ]
        _versions[doc_id].reverse()  # newest first

        # Инициализация истории статусов
        _history[doc_id] = [
            {
                "event_id": f"evt-{new_id()}",
                "document_id": doc_id,
                "from_status": None,
                "to_status": doc.get("status", "uploaded"),
                "timestamp": doc.get("created_at", utcnow()),
                "user_id": doc.get("user_id", "u-001"),
                "comment": "Документ создан",
            },
            {
                "event_id": f"evt-{new_id()}",
                "document_id": doc_id,
                "from_status": "uploaded",
                "to_status": doc.get("status", "completed"),
                "timestamp": doc.get("updated_at", utcnow()),
                "user_id": doc.get("user_id", "u-001"),
                "comment": f"Обработка завершена со статусом {doc.get('status', 'completed')}",
            },
        ]

        # Инициализация chunks
        chunk_count = doc.get("chunk_count", 0)
        _chunks[doc_id] = [
            {
                "chunk_id": f"chunk-{new_id()}",
                "chunk_number": i + 1,
                "document_id": doc_id,
                "content": f"Фрагмент {i + 1} документа {doc.get('title', '')}. Содержание этого фрагмента описывает ключевые характеристики.",
                "page": (i % max(doc.get("pages_total", 1), 1)) + 1,
                "score": round(random.uniform(0.7, 0.99), 2),
                "is_indexed": doc.get("status") == "completed",
                "created_at": doc.get("created_at", utcnow()),
            }
            for i in range(chunk_count)
        ]


def _get_document(doc_id: str) -> dict:
    doc = _documents.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )
    return doc


def _get_page_block(doc_id: str, page_num: int) -> dict:
    """Генерирует mock-блоки страницы."""
    blocks = [
        {
            "block_id": f"blk-{new_id()}",
            "type": "text",
            "coordinates": {"x": 100, "y": 200, "width": 800, "height": 50},
            "text": f"Текст на странице {page_num} документа {doc_id}. Пример содержания для тестирования.",
            "highlighted": False,
        },
        {
            "block_id": f"blk-{new_id()}",
            "type": "table",
            "coordinates": {"x": 100, "y": 300, "width": 800, "height": 200},
            "text": "Таблица спецификации (mock)",
            "highlighted": False,
        },
        {
            "block_id": f"blk-{new_id()}",
            "type": "drawing",
            "coordinates": {"x": 500, "y": 600, "width": 400, "height": 300},
            "text": "Чертёж (mock)",
            "highlighted": False,
            "table_data": {
                "rows": [
                    {
                        "Поз.": "1",
                        "Наименование": "Корпус",
                        "Кол.": "1",
                        "Материал": "Сталь 45",
                    },
                    {
                        "Поз.": "2",
                        "Наименование": "Крышка",
                        "Кол.": "1",
                        "Материал": "Алюминий Д16Т",
                    },
                ]
            },
        },
    ]
    return {
        "image_url": f"/api/v1/documents/{doc_id}/pages/{page_num}/image",
        "page": page_num,
        "width": 2480,
        "height": 3508,
        "blocks": blocks,
    }


def _get_queue_from_documents():
    """Генерирует очередь из текущего состояния документов."""
    queue = []
    for doc_id, doc in _documents.items():
        status = doc.get("status", "unknown")
        if status in (
            "queued",
            "processing",
            "failed",
            "uploaded",
            "parsing",
            "validation",
        ):
            queue.append(
                {
                    "document_id": doc_id,
                    "title": doc.get("title", ""),
                    "document_type": doc.get("source_type", ""),
                    "status": status,
                    "progress_percent": doc.get("pages_processed", 0)
                    / max(doc.get("pages_total", 1), 1)
                    * 100
                    if doc.get("pages_total", 0) > 0
                    else 0,
                    "pipeline": {
                        "formation": {
                            "parsing": "completed"
                            if status
                            in (
                                "completed",
                                "validation",
                                "review_required",
                                "ready_for_promotion",
                                "approved",
                            )
                            else doc.get("ocr_status", "pending"),
                            "validation": "completed"
                            if status in ("ready_for_promotion", "approved")
                            else ("pending" if status == "parsing" else "pending"),
                            "registry": "completed"
                            if status in ("approved",)
                            else "pending",
                        },
                        "indexation": {
                            "rag_indexing": "completed"
                            if status == "approved"
                            else (
                                "pending"
                                if status == "ready_for_promotion"
                                else doc.get("index_status", "pending")
                            ),
                        },
                    },
                    "user_id": doc.get("user_id", ""),
                    "uploaded_by": doc.get("uploaded_by", ""),
                    "created_at": doc.get("created_at", ""),
                    "started_at": doc.get("created_at", "")
                    if status != "queued"
                    else None,
                    "estimated_completion": None,
                }
            )
    queue.sort(key=lambda q: q.get("created_at", ""), reverse=True)
    return queue


# ---------------------------------------------------------------------------
# Модели данных
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = None


class ReprocessRequest(BaseModel):
    mode: Optional[str] = None


# ---------------------------------------------------------------------------
# Response-модели для OpenAPI
# ---------------------------------------------------------------------------


class DocumentListItem(BaseModel):
    document_id: str
    title: str
    doc_code: Optional[str] = None
    source_type: str
    era: str
    validity_status: str
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    mks_oks_code: Optional[str] = None
    okstu_code: Optional[str] = None
    classification_status: Dict[str, str]
    status: str
    latest_version: int
    total_versions: int
    chunk_count: int
    chunk_validation: Optional[Dict[str, Any]] = None
    user_id: str
    uploaded_by: str
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    summary: Dict[str, Any]
    items: List[DocumentListItem]
    meta: Dict[str, Any]


class DocumentDetailResponse(BaseModel):
    document_id: str
    title: str
    doc_code: Optional[str] = None
    source_type: str
    era: str
    validity_status: str
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    mks_oks_code: Optional[str] = None
    okstu_code: Optional[str] = None
    classification_status: Dict[str, str]
    successor_doc_id: Optional[str] = None
    predecessor_doc_id: Optional[str] = None
    chunk_container_id: Optional[str] = None
    metadata: Dict[str, Any]
    latest_version: int
    total_versions: int
    chunk_count: int
    user_id: str
    uploaded_by: str
    status: str
    file_size: int
    pages_total: int
    pages_processed: int
    pages_failed: int
    created_at: str
    updated_at: str


class SearchResultItem(BaseModel):
    section_id: str
    document_id: str
    document_title: str
    document_type: str
    clause: str
    page: int
    content: str
    score: float
    page_preview_url: str
    document_url: str


class SearchResponse(BaseModel):
    query: str
    items: List[SearchResultItem]
    total_found: int
    processing_time_ms: int


# ---------------------------------------------------------------------------
# Инициализация
# ---------------------------------------------------------------------------

_init_data()


# ===========================================================================
# Группа documents
# ===========================================================================


@router.post("/documents", status_code=202)
async def upload_document(file: UploadFile = File(...), request: Request = None):
    """Загрузка документа (асинхронная)."""
    global _doc_id_counter
    _doc_id_counter += 1
    doc_id = f"doc-{new_id()}"
    now = utcnow()

    user_id = (request.state.user.get("user_id") or "system") if request else "system"
    user_name = (request.state.user.get("full_name") or user_id) if request else user_id

    content_bytes = (file.filename or f"document_{doc_id}").encode()
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    title_hash = hashlib.sha256(
        (file.filename or f"Документ {doc_id}").encode()
    ).hexdigest()

    version_id = f"ver-{new_id()}"

    new_doc = {
        "document_id": doc_id,
        "filename": file.filename or f"document_{doc_id}.pdf",
        "title": file.filename or f"Документ {doc_id}",
        "doc_code": None,
        "source_type": "GOST",
        "era": "CURRENT",
        "validity_status": "active",
        "jurisdiction": "RF",
        "issuing_body": None,
        "mks_oks_code": None,
        "okstu_code": None,
        "classification_status": {"mks_status": "unknown", "okstu_status": "unknown"},
        "successor_doc_id": None,
        "predecessor_doc_id": None,
        "chunk_container_id": None,
        "document_type": "specification",
        "source": "upload",
        "version": 1,
        "latest_version": 1,
        "total_versions": 1,
        "chunk_count": 0,
        "chunk_validation": None,
        "status": "uploaded",
        "file_size": 1024000,
        "pages_total": 0,
        "pages_processed": 0,
        "pages_failed": 0,
        "ocr_status": "pending",
        "index_status": "pending",
        "user_id": user_id,
        "uploaded_by": user_name,
        "metadata": {"year": 2026, "udc": "", "tags": []},
        "pages": [],
        "parameters": {},
        "extraction_confidence": 0.0,
        "unconfirmed_fields": [],
        "created_at": now,
        "updated_at": now,
        "registry_doc_id": None,
    }

    _documents[doc_id] = new_doc

    # Добавляем первую версию
    _versions[doc_id] = [
        {
            "version_id": version_id,
            "version_number": 1,
            "document_id": doc_id,
            "title": new_doc["title"],
            "file_size": new_doc["file_size"],
            "content_hash_sha256": content_hash,
            "title_hash_sha256": title_hash,
            "status": "uploaded",
            "created_at": now,
            "uploaded_by": user_name,
        }
    ]

    # Инициализируем историю
    _history[doc_id] = [
        {
            "event_id": f"evt-{new_id()}",
            "document_id": doc_id,
            "from_status": None,
            "to_status": "uploaded",
            "timestamp": now,
            "user_id": user_id,
            "comment": "Документ загружен",
        }
    ]

    # Инициализируем chunks
    _chunks[doc_id] = []

    return {
        "task_id": f"task-{new_id()}",
        "version_id": version_id,
        "status": "uploaded",
        "content_hash_sha256": content_hash,
        "is_duplicate_file": False,
        "is_duplicate_document": False,
        "title_hash_sha256": title_hash,
        "created_at": now,
    }


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    status: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Список документов."""
    items = list(_documents.values())

    if status:
        items = [d for d in items if d.get("status") == status]
    if document_type:
        items = [d for d in items if d.get("source_type") == document_type]
    if search:
        search_lower = search.lower()
        items = [
            d
            for d in items
            if search_lower in d.get("title", "").lower()
            or search_lower in d.get("filename", "").lower()
        ]

    # Сортируем по created_at (сначала новые)
    items.sort(key=lambda d: d.get("created_at", ""), reverse=True)

    # Summary с новыми статусами
    total = len(_documents)
    uploaded = sum(1 for d in _documents.values() if d.get("status") == "uploaded")
    parsing = sum(
        1
        for d in _documents.values()
        if d.get("status") == "parsing"
        or (d.get("status") == "processing" and d.get("ocr_status") == "processing")
    )
    validation = sum(1 for d in _documents.values() if d.get("status") == "validation")
    review_required = sum(
        1 for d in _documents.values() if d.get("status") == "review_required"
    )
    ready_for_promotion = sum(
        1
        for d in _documents.values()
        if d.get("status") == "ready_for_promotion" or d.get("status") == "completed"
    )
    approved = sum(1 for d in _documents.values() if d.get("status") == "approved")
    failed = sum(1 for d in _documents.values() if d.get("status") == "failed")
    archived = sum(1 for d in _documents.values() if d.get("status") == "archived")

    result = []
    for d in items:
        classification_status = d.get("classification_status", {})
        if not isinstance(classification_status, dict):
            classification_status = {"mks_status": "unknown", "okstu_status": "unknown"}

        result.append(
            {
                "document_id": d["document_id"],
                "title": d.get("title", ""),
                "doc_code": d.get("doc_code"),
                "source_type": d.get("source_type", ""),
                "era": d.get("era", ""),
                "validity_status": d.get("validity_status", ""),
                "jurisdiction": d.get("jurisdiction"),
                "issuing_body": d.get("issuing_body"),
                "mks_oks_code": d.get("mks_oks_code"),
                "okstu_code": d.get("okstu_code"),
                "classification_status": classification_status,
                "status": d.get("status", ""),
                "latest_version": d.get("total_versions", 1),
                "total_versions": d.get("total_versions", 1),
                "chunk_count": d.get("chunk_count", 0),
                "chunk_validation": d.get("chunk_validation"),
                "user_id": d.get("user_id", ""),
                "uploaded_by": d.get("uploaded_by", ""),
                "created_at": d.get("created_at", ""),
                "updated_at": d.get("updated_at", ""),
            }
        )

    paged = paginate(result, page, page_size)
    return {
        "summary": {
            "total": total,
            "uploaded": uploaded,
            "parsing": parsing,
            "validation": validation,
            "review_required": review_required,
            "ready_for_promotion": ready_for_promotion,
            "approved": approved,
            "failed": failed,
            "archived": archived,
        },
        "items": paged["items"],
        "meta": paged["meta"],
    }


@router.get("/documents/queue")
async def get_document_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Очередь обработки документов."""
    queue = _get_queue_from_documents()
    paged = paginate(queue, page, page_size)
    return {
        "queue": paged["items"],
        "meta": {
            "total_in_queue": len(queue),
            "page": paged["meta"]["page"],
            "page_size": paged["meta"]["page_size"],
        },
    }


# ===========================================================================
# Группа search
# ===========================================================================


@router.post("/documents/search", response_model=SearchResponse)
async def search_documents(req: SearchRequest):
    """Поиск по документам."""

    # Mock-результаты поиска с обновлёнными полями
    mock_results = [
        {
            "section_id": f"sec-{new_id()}",
            "document_id": "doc-001",
            "document_title": "Спецификация по ГОСТ 2.109",
            "document_type": "specification",
            "clause": "Основные требования",
            "page": 3,
            "content": "Толщина стенки корпуса: 5 мм, материал: Сталь 45",
            "score": 0.95,
            "page_preview_url": "/api/v1/documents/doc-001/pages/3/preview",
            "document_url": "/api/v1/documents/doc-001",
        },
        {
            "section_id": f"sec-{new_id()}",
            "document_id": "rd-001",
            "document_title": "ГОСТ 2.109-73",
            "document_type": "normative",
            "clause": "Раздел 3",
            "page": 5,
            "content": "Толщина стенки не менее 4 мм для изделий данного типа",
            "score": 0.92,
            "page_preview_url": "/api/v1/documents/rd-001/pages/5/preview",
            "document_url": "/api/v1/documents/rd-001",
        },
        {
            "section_id": f"sec-{new_id()}",
            "document_id": "doc-002",
            "document_title": "Чертеж детали 101",
            "document_type": "drawing",
            "clause": "Габаритные размеры",
            "page": 1,
            "content": "150x80x25 мм, Сталь 45",
            "score": 0.88,
            "page_preview_url": "/api/v1/documents/doc-002/pages/1/preview",
            "document_url": "/api/v1/documents/doc-002",
        },
        {
            "section_id": f"sec-{new_id()}",
            "document_id": "rd-002",
            "document_title": "ГОСТ 2.307-2011",
            "document_type": "normative",
            "clause": "Допуски",
            "page": 3,
            "content": "Предельные отклонения размеров: H11, h11",
            "score": 0.85,
            "page_preview_url": "/api/v1/documents/rd-002/pages/3/preview",
            "document_url": "/api/v1/documents/rd-002",
        },
    ]

    # Фильтр по document_ids
    if req.document_ids:
        mock_results = [r for r in mock_results if r["document_id"] in req.document_ids]

    # Фильтр по document_type
    if req.filters and req.filters.get("document_type"):
        mock_results = [
            r
            for r in mock_results
            if r["document_type"] == req.filters["document_type"]
        ]

    # Фильтр по датам (упрощённо)
    if req.filters and (req.filters.get("date_from") or req.filters.get("date_to")):
        pass

    # Сортируем по score
    mock_results.sort(key=lambda r: r["score"], reverse=True)
    top_k = min(req.top_k or 10, len(mock_results))
    results = mock_results[:top_k]

    return {
        "query": req.query,
        "items": results,
        "total_found": len(mock_results),
        "processing_time_ms": random.randint(200, 1500),
    }


@router.get("/documents/search")
async def search_documents_get(
    q: str = Query(..., description="Поисковый запрос"),
    document_ids: Optional[str] = Query(
        None, description="ID документов через запятую"
    ),
    top_k: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Поиск GET-методом."""
    doc_ids = document_ids.split(",") if document_ids else None
    return await search_documents(
        SearchRequest(query=q, document_ids=doc_ids, top_k=top_k)
    )


@router.get("/documents/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: str):
    """Детали документа."""
    doc = _get_document(doc_id)

    classification_status = doc.get("classification_status", {})
    if not isinstance(classification_status, dict):
        classification_status = {"mks_status": "unknown", "okstu_status": "unknown"}

    metadata = doc.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    return {
        "document_id": doc["document_id"],
        "title": doc.get("title", ""),
        "doc_code": doc.get("doc_code"),
        "source_type": doc.get("source_type", ""),
        "era": doc.get("era", ""),
        "validity_status": doc.get("validity_status", ""),
        "jurisdiction": doc.get("jurisdiction"),
        "issuing_body": doc.get("issuing_body"),
        "mks_oks_code": doc.get("mks_oks_code"),
        "okstu_code": doc.get("okstu_code"),
        "classification_status": classification_status,
        "successor_doc_id": doc.get("successor_doc_id"),
        "predecessor_doc_id": doc.get("predecessor_doc_id"),
        "chunk_container_id": doc.get("chunk_container_id"),
        "metadata": metadata,
        "latest_version": doc.get("total_versions", 1),
        "total_versions": doc.get("total_versions", 1),
        "chunk_count": doc.get("chunk_count", 0),
        "user_id": doc.get("user_id", ""),
        "uploaded_by": doc.get("uploaded_by", ""),
        "status": doc.get("status", ""),
        "file_size": doc.get("file_size", 0),
        "pages_total": doc.get("pages_total", 0),
        "pages_processed": doc.get("pages_processed", 0),
        "pages_failed": doc.get("pages_failed", 0),
        "created_at": doc.get("created_at", ""),
        "updated_at": doc.get("updated_at", ""),
    }


@router.get("/documents/{doc_id}/status")
async def get_document_status(doc_id: str):
    """Статус обработки документа с обновлённой структурой pipeline."""
    doc = _get_document(doc_id)
    status = doc.get("status", "unknown")

    # Определяем статусы этапов pipeline
    parsing_status = "pending"
    validation_status = "pending"
    registry_status = "pending"
    rag_indexing_status = "pending"

    if status == "completed" or status == "ready_for_promotion":
        parsing_status = "completed"
        validation_status = "completed"
        registry_status = "completed"
        rag_indexing_status = (
            "completed" if status == "ready_for_promotion" else "pending"
        )
    elif status == "approved":
        parsing_status = "completed"
        validation_status = "completed"
        registry_status = "completed"
        rag_indexing_status = "completed"
    elif status == "processing" or status == "parsing":
        parsing_status = doc.get("ocr_status", "processing")
    elif status == "validation":
        parsing_status = "completed"
        validation_status = "processing"
    elif status == "failed":
        parsing_status = "failed"
    elif status == "uploaded":
        parsing_status = "pending"
    else:
        parsing_status = doc.get("ocr_status", "pending")

    # Определяем признак наличия ошибок
    error_details = None
    if status == "failed":
        error_details = {
            "code": "OCR_FAILED",
            "message": "Ошибка OCR-распознавания",
            "details": {"failed_pages": doc.get("pages_failed", 0)},
        }

    return {
        "document_id": doc_id,
        "user_id": doc.get("user_id", ""),
        "status": status,
        "progress_percent": (
            100
            if status in ("completed", "ready_for_promotion", "approved")
            else (
                int(
                    (doc.get("pages_processed", 0) / max(doc.get("pages_total", 1), 1))
                    * 100
                )
                if doc.get("pages_total", 0) > 0
                else 0
            )
        ),
        "pipeline": {
            "formation": {
                "parsing": parsing_status,
                "validation": validation_status,
                "registry": registry_status,
            },
            "indexation": {
                "rag_indexing": rag_indexing_status,
            },
        },
        "chunk_summary": {
            "total": doc.get("chunk_count", 0),
            "indexed": doc.get("chunk_count", 0)
            if rag_indexing_status == "completed"
            else 0,
        },
        "started_at": doc.get("created_at", ""),
        "error": error_details,
    }


@router.get("/documents/{doc_id}/file")
async def get_document_file(doc_id: str):
    """Информация о файле документа."""
    doc = _get_document(doc_id)
    return {
        "document_id": doc_id,
        "document_title": doc.get("title", ""),
        "content_type": "application/pdf",
        "file_url": f"/api/v1/files/{doc_id}/{doc.get('filename', 'document.pdf')}",
    }


@router.get("/documents/{doc_id}/pages/{page_num}/preview")
async def get_page_preview(doc_id: str, page_num: int):
    """Превью страницы."""
    doc = _get_document(doc_id)
    return {
        "document_id": doc_id,
        "document_title": doc.get("title", ""),
        "page": page_num,
        "content_type": "image/png",
        "preview_url": f"/api/v1/previews/{doc_id}/page_{page_num}.png",
        "text": f"Mock OCR текст для страницы {page_num} документа {doc_id}. Здесь содержится распознанный текст.",
        "highlight": [],
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Удалить документ."""
    _get_document(doc_id)
    del _documents[doc_id]
    # Также удаляем связанные данные
    _versions.pop(doc_id, None)
    _chunks.pop(doc_id, None)
    _history.pop(doc_id, None)
    _approvals.pop(doc_id, None)
    return {
        "document_id": doc_id,
        "deleted_at": utcnow(),
    }


@router.post("/documents/{doc_id}/reprocess", status_code=202)
async def reprocess_document(
    doc_id: str, req: Optional[ReprocessRequest] = None, request: Request = None
):
    """Переобработка документа."""
    doc = _get_document(doc_id)
    mode = req.mode if req and req.mode else "full"
    user_id = (request.state.user.get("user_id") or "system") if request else "system"

    # Сбрасываем статус
    doc["status"] = "parsing"
    doc["ocr_status"] = "pending"
    doc["index_status"] = "pending"
    doc["updated_at"] = utcnow()

    # Добавляем запись в историю
    if doc_id not in _history:
        _history[doc_id] = []
    _history[doc_id].append(
        {
            "event_id": f"evt-{new_id()}",
            "document_id": doc_id,
            "from_status": doc.get("status", "unknown"),
            "to_status": "parsing",
            "timestamp": utcnow(),
            "user_id": user_id,
            "comment": f"Запущена переобработка (режим: {mode})",
        }
    )

    return {
        "mode": mode,
        "document_id": doc_id,
        "user_id": user_id,
        "task_id": f"task-{new_id()}",
        "status": "parsing",
        "created_at": utcnow(),
    }


@router.get("/documents/{doc_id}/errors")
async def get_document_errors(
    doc_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Ошибки обработки документа."""
    _get_document(doc_id)
    items = [e for e in _document_errors if e["document_id"] == doc_id]

    paged = paginate(items, page, page_size)
    return {
        "errors": paged["items"],
        "meta": paged["meta"],
    }


# ===========================================================================
# Группа versions
# ===========================================================================


@router.post("/documents/{doc_id}/versions", status_code=201)
async def add_document_version(
    doc_id: str, file: UploadFile = File(...), request: Request = None
):
    """Добавить новую версию документа."""
    doc = _get_document(doc_id)
    now = utcnow()
    user_id = (request.state.user.get("user_id") or "system") if request else "system"
    version_number = doc.get("total_versions", 1) + 1

    content_bytes = (file.filename or f"{doc_id}_v{version_number}").encode()
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    title_hash = hashlib.sha256(doc.get("title", "").encode()).hexdigest()

    version_id = f"ver-{new_id()}"

    new_version = {
        "version_id": version_id,
        "version_number": version_number,
        "document_id": doc_id,
        "title": doc.get("title", ""),
        "file_size": doc.get("file_size", 0),
        "content_hash_sha256": content_hash,
        "title_hash_sha256": title_hash,
        "status": "uploaded",
        "created_at": now,
        "uploaded_by": doc.get("uploaded_by", ""),
    }

    if doc_id not in _versions:
        _versions[doc_id] = []
    _versions[doc_id].insert(0, new_version)

    doc["total_versions"] = version_number
    doc["latest_version"] = version_number
    doc["updated_at"] = now

    # Добавляем запись в историю
    if doc_id not in _history:
        _history[doc_id] = []
    _history[doc_id].append(
        {
            "event_id": f"evt-{new_id()}",
            "document_id": doc_id,
            "from_status": None,
            "to_status": doc.get("status", "uploaded"),
            "timestamp": now,
            "user_id": user_id,
            "comment": f"Добавлена версия {version_number}",
        }
    )

    return {
        "version_id": version_id,
        "version_number": version_number,
        "document_id": doc_id,
        "content_hash_sha256": content_hash,
        "title_hash_sha256": title_hash,
        "status": "uploaded",
        "created_at": now,
    }


@router.get("/documents/{doc_id}/versions")
async def list_document_versions(doc_id: str):
    """Список версий документа."""
    _get_document(doc_id)
    versions = _versions.get(doc_id, [])
    return {
        "document_id": doc_id,
        "versions": versions,
        "total": len(versions),
    }


# ===========================================================================
# Группа approve
# ===========================================================================


@router.post("/documents/{doc_id}/approve")
async def approve_document(doc_id: str, request: Request = None):
    """Подтверждение валидации документа."""
    doc = _get_document(doc_id)
    now = utcnow()
    user_id = (request.state.user.get("user_id") or "system") if request else "system"

    old_status = doc.get("status", "")
    doc["status"] = "approved"
    doc["updated_at"] = now

    _approvals[doc_id] = {
        "document_id": doc_id,
        "approved_by": user_id,
        "approved_at": now,
        "previous_status": old_status,
    }

    if doc_id not in _history:
        _history[doc_id] = []
    _history[doc_id].append(
        {
            "event_id": f"evt-{new_id()}",
            "document_id": doc_id,
            "from_status": old_status,
            "to_status": "approved",
            "timestamp": now,
            "user_id": user_id,
            "comment": "Документ подтверждён",
        }
    )

    return {
        "document_id": doc_id,
        "status": "approved",
        "approved_at": now,
        "previous_status": old_status,
    }


@router.get("/documents/{doc_id}/history")
async def get_document_history(doc_id: str):
    """История статусов документа."""
    _get_document(doc_id)
    events = _history.get(doc_id, [])
    # Сортируем от новых к старым
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return {
        "document_id": doc_id,
        "events": events,
        "total": len(events),
    }


# ===========================================================================
# Группа pages
# ===========================================================================


@router.get("/documents/{doc_id}/pages")
async def get_document_pages(
    doc_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Список страниц документа."""
    doc = _get_document(doc_id)
    pages = doc.get("pages", [])

    # Если страниц нет, генерируем mock
    if not pages and doc.get("pages_total", 0) > 0:
        pages = []
        for i in range(1, doc["pages_total"] + 1):
            pages.append(
                {
                    "page": i,
                    "width": 2480,
                    "height": 3508,
                    "ocr_status": "completed"
                    if i <= doc.get("pages_processed", 0)
                    else "pending",
                    "confidence": round(random.uniform(0.7, 0.99), 2),
                    "has_text_layer": random.choice([True, False]),
                }
            )

    paged = paginate(pages, page, page_size)
    return {
        "document_id": doc_id,
        "pages_total": doc.get("pages_total", 0),
        "pages": paged["items"],
        "meta": paged["meta"],
    }


@router.get("/documents/{doc_id}/pages/{page_num}")
async def get_page_detail(doc_id: str, page_num: int):
    """Детальная информация о странице."""
    _get_document(doc_id)
    return _get_page_block(doc_id, page_num)


@router.get("/documents/{doc_id}/pages/{page_num}/text")
async def get_page_text(doc_id: str, page_num: int):
    """Текст страницы."""
    _get_document(doc_id)
    blocks = _get_page_block(doc_id, page_num)["blocks"]

    return {
        "page": page_num,
        "full_text": " ".join(b.get("text", "") for b in blocks),
        "blocks": [
            {
                "block_id": b["block_id"],
                "type": b["type"],
                "coordinates": b["coordinates"],
                "text": b.get("text", ""),
                "confidence": round(random.uniform(0.8, 0.98), 2),
                "table_data": b.get("table_data"),
                "highlighted": b.get("highlighted", False),
            }
            for b in blocks
        ],
    }


@router.get("/documents/{doc_id}/parameters")
async def get_document_parameters(doc_id: str):
    """Извлечённые параметры документа."""
    doc = _get_document(doc_id)
    params = doc.get("parameters", {})

    return {
        "document_id": doc_id,
        "document_type": doc.get("source_type", ""),
        "parameters": params,
        "extraction_confidence": doc.get("extraction_confidence", 0.0),
        "unconfirmed_fields": doc.get("unconfirmed_fields", []),
        "updated_at": doc.get("updated_at", ""),
    }


# ===========================================================================
# Группа monitor
# ===========================================================================


@router.get("/monitor/metrics")
async def get_metrics():
    """Метрики системы."""
    return _metrics


# ===========================================================================
# Группа system
# ===========================================================================


@router.get("/system/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": 86400,
        "services": {
            "auth": "ok",
            "rag": "ok",
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
# Запуск
# ===========================================================================

from fastapi import FastAPI

app = FastAPI(title="Orchestrator Service Mock", version="1.0.0")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8081)
