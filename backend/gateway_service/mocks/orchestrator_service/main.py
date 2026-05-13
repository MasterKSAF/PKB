"""
Orchestrator Service Mock
Основной шлюз API — документы, поиск, валидация, мониторинг (in-memory).
Порт: 8081
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
import random
from typing import Any, Dict, List, Optional

from common import (
    SEED_COMPARISONS,
    SEED_DOCUMENT_ERRORS,
    SEED_DOCUMENTS,
    SEED_METRICS,
    SEED_QUEUE,
    SEED_VALIDATION_CHECKS,
    error_response,
    new_id,
    paginate,
    utcnow,
)
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1")

# ---------------------------------------------------------------------------
# In-memory хранилища
# ---------------------------------------------------------------------------

_documents: Dict[str, dict] = {}
_document_errors: List[dict] = {}
_queue: List[dict] = {}
_validation_checks: Dict[str, dict] = {}
_comparisons: Dict[str, dict] = {}
_metrics: dict = {}

# Счётчик для версий документов
_doc_id_counter: int = 100


def _init_data():
    global \
        _documents, \
        _document_errors, \
        _queue, \
        _validation_checks, \
        _comparisons, \
        _metrics
    _documents = {d["document_id"]: copy.deepcopy(d) for d in SEED_DOCUMENTS}
    _document_errors = copy.deepcopy(SEED_DOCUMENT_ERRORS)
    _queue = copy.deepcopy(SEED_QUEUE)
    _validation_checks = {
        c["check_run_id"]: copy.deepcopy(c) for c in SEED_VALIDATION_CHECKS
    }
    _comparisons = {c["comparison_id"]: copy.deepcopy(c) for c in SEED_COMPARISONS}
    _metrics = copy.deepcopy(SEED_METRICS)


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


# ---------------------------------------------------------------------------
# Модели данных
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = None


class ValidateCompareRequest(BaseModel):
    normative_query: Optional[str] = None
    project_document_id: Optional[str] = None
    normative_fragment_id: Optional[str] = None
    project_fragment_id: Optional[str] = None


class ValidateChecksRequest(BaseModel):
    project_document_ids: List[str]
    nsi_document_ids: Optional[List[str]] = None
    parameters: Optional[List[str]] = None


class ReprocessRequest(BaseModel):
    mode: Optional[str] = None


# ---------------------------------------------------------------------------
# Response-модели для OpenAPI
# ---------------------------------------------------------------------------


class DocumentListItem(BaseModel):
    document_id: str
    title: str
    document_type: str
    source: str
    version: int
    pages: int
    ocr_status: str
    index_status: str
    user_id: str
    uploaded_by: str
    created_at: str
    updated_at: str
    registry_doc_id: Optional[str] = None


class DocumentListResponse(BaseModel):
    summary: Dict[str, Any]
    items: List[DocumentListItem]
    meta: Dict[str, Any]


class DocumentDetailResponse(BaseModel):
    document_id: str
    filename: str
    document_type: str
    status: str
    file_size: int
    pages_total: int
    pages_processed: int
    pages_failed: int
    user_id: str
    uploaded_by: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    registry_doc_id: Optional[str] = None


class CheckItemSource(BaseModel):
    document_id: str
    page: int
    page_preview_url: str
    document_url: str


class CheckItem(BaseModel):
    check_item_id: str
    project: str
    section: str
    parameter: str
    project_value: str
    nsi_requirement: str
    nsi_document: str
    status: str
    match_status: str
    comment: str
    project_source: CheckItemSource
    nsi_source: CheckItemSource


class CheckResultResponse(BaseModel):
    check_run_id: str
    status: str
    summary: Dict[str, int]
    items: List[CheckItem]
    created_at: str
    updated_at: str


class SearchResultItem(BaseModel):
    fragment_id: str
    document_id: str
    document_title: str
    document_type: str
    section: str
    page: int
    fragment: str
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
async def upload_document(
    file: UploadFile = File(None),
    document_type: str = Form("normative"),
    title: str = Form(None),
    metadata: str = Form(None),
):
    """Загрузка документа (асинхронная)."""
    global _doc_id_counter
    _doc_id_counter += 1
    doc_id = f"doc-{new_id()}"
    now = utcnow()

    new_doc = {
        "document_id": doc_id,
        "filename": file.filename if file else f"document_{doc_id}.pdf",
        "title": title or file.filename or f"Документ {doc_id}",
        "document_type": document_type,
        "source": "upload",
        "version": 1,
        "status": "queued",
        "file_size": 1024000,
        "pages_total": 0,
        "pages_processed": 0,
        "pages_failed": 0,
        "ocr_status": "pending",
        "index_status": "pending",
        "user_id": "u-001",
        "uploaded_by": "Иванов С.П.",
        "metadata": {"project": "ПКБ-101", "author": "Иванов С.П."},
        "pages": [],
        "parameters": {},
        "extraction_confidence": 0.0,
        "unconfirmed_fields": [],
        "created_at": now,
        "updated_at": now,
    }

    _documents[doc_id] = new_doc

    # Добавляем в очередь
    _queue.append(
        {
            "document_id": doc_id,
            "title": new_doc["title"],
            "document_type": document_type,
            "status": "queued",
            "progress_percent": 0,
            "steps": {
                "ocr": "pending",
                "layout_parsing": "pending",
                "indexing": "pending",
            },
            "user_id": "u-001",
            "uploaded_by": "Иванов С.П.",
            "created_at": now,
            "started_at": None,
            "estimated_completion": None,
        }
    )

    return {
        "document_id": doc_id,
        "status": "queued",
        "user_id": "u-001",
        "task_id": f"task-{new_id()}",
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
        items = [d for d in items if d.get("document_type") == document_type]
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

    # Summary
    total = len(_documents)
    ocr_completed = sum(
        1 for d in _documents.values() if d.get("ocr_status") == "completed"
    )
    indexed = sum(
        1 for d in _documents.values() if d.get("index_status") == "completed"
    )
    need_attention = sum(
        1 for d in _documents.values() if d.get("status") in ("failed", "processing")
    )

    result = []
    for d in items:
        result.append(
            {
                "document_id": d["document_id"],
                "title": d.get("title", ""),
                "document_type": d.get("document_type", ""),
                "source": d.get("source", ""),
                "version": d.get("version", 1),
                "pages": d.get("pages_total", 0),
                "ocr_status": d.get("ocr_status", "pending"),
                "index_status": d.get("index_status", "pending"),
                "user_id": d.get("user_id", ""),
                "uploaded_by": d.get("uploaded_by", ""),
                "created_at": d.get("created_at", ""),
                "updated_at": d.get("updated_at", ""),
                "registry_doc_id": d.get("metadata", {}).get("registry_doc_id"),
            }
        )

    paged = paginate(result, page, page_size)
    return {
        "summary": {
            "total": total,
            "ocr_completed": ocr_completed,
            "indexed": indexed,
            "need_attention": need_attention,
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
    paged = paginate(list(_queue), page, page_size)
    return {
        "queue": paged["items"],
        "meta": {
            "total_in_queue": len(_queue),
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
    query_lower = req.query.lower()

    # Mock-результаты поиска
    mock_results = [
        {
            "fragment_id": f"frag-{new_id()}",
            "document_id": "doc-001",
            "document_title": "Спецификация по ГОСТ 2.109",
            "document_type": "specification",
            "section": "Основные требования",
            "page": 3,
            "fragment": "Толщина стенки корпуса: 5 мм, материал: Сталь 45",
            "score": 0.95,
            "page_preview_url": "/api/v1/documents/doc-001/pages/3/preview",
            "document_url": "/api/v1/documents/doc-001",
        },
        {
            "fragment_id": f"frag-{new_id()}",
            "document_id": "rd-001",
            "document_title": "ГОСТ 2.109-73",
            "document_type": "normative",
            "section": "Раздел 3",
            "page": 5,
            "fragment": "Толщина стенки не менее 4 мм для изделий данного типа",
            "score": 0.92,
            "page_preview_url": "/api/v1/documents/rd-001/pages/5/preview",
            "document_url": "/api/v1/documents/rd-001",
        },
        {
            "fragment_id": f"frag-{new_id()}",
            "document_id": "doc-002",
            "document_title": "Чертеж детали 101",
            "document_type": "drawing",
            "section": "Габаритные размеры",
            "page": 1,
            "fragment": "150x80x25 мм, Сталь 45",
            "score": 0.88,
            "page_preview_url": "/api/v1/documents/doc-002/pages/1/preview",
            "document_url": "/api/v1/documents/doc-002",
        },
        {
            "fragment_id": f"frag-{new_id()}",
            "document_id": "rd-002",
            "document_title": "ГОСТ 2.307-2011",
            "document_type": "normative",
            "section": "Допуски",
            "page": 3,
            "fragment": "Предельные отклонения размеров: H11, h11",
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
        # Для мока просто возвращаем все результаты
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
    # Перенаправляем на POST-метод
    doc_ids = document_ids.split(",") if document_ids else None
    return await search_documents(
        SearchRequest(query=q, document_ids=doc_ids, top_k=top_k)
    )


@router.get("/documents/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: str):
    """Детали документа."""
    doc = _get_document(doc_id)
    return {
        "document_id": doc["document_id"],
        "filename": doc.get("filename", ""),
        "document_type": doc.get("document_type", ""),
        "status": doc.get("status", ""),
        "file_size": doc.get("file_size", 0),
        "pages_total": doc.get("pages_total", 0),
        "pages_processed": doc.get("pages_processed", 0),
        "pages_failed": doc.get("pages_failed", 0),
        "user_id": doc.get("user_id", ""),
        "uploaded_by": doc.get("uploaded_by", ""),
        "created_at": doc.get("created_at", ""),
        "updated_at": doc.get("updated_at", ""),
        "metadata": doc.get("metadata", {}),
        "registry_doc_id": doc.get("metadata", {}).get("registry_doc_id"),
    }


@router.get("/documents/{doc_id}/status")
async def get_document_status(doc_id: str):
    """Статус обработки документа."""
    doc = _get_document(doc_id)
    status = doc.get("status", "unknown")

    base = {
        "document_id": doc_id,
        "user_id": doc.get("user_id", ""),
        "status": status,
        "progress_percent": 0,
        "steps": {
            "ocr": doc.get("ocr_status", "pending"),
            "layout_parsing": "pending",
            "indexing": doc.get("index_status", "pending"),
        },
        "started_at": doc.get("created_at", ""),
    }

    if status == "completed":
        base.update(
            {
                "progress_percent": 100,
                "ocr_result": {
                    "pages_total": doc.get("pages_total", 0),
                    "pages_processed": doc.get("pages_processed", 0),
                    "pages_failed": doc.get("pages_failed", 0),
                    "low_confidence_pages": [1]
                    if doc.get("pages_total", 0) > 0
                    and doc.get("extraction_confidence", 1) < 0.5
                    else [],
                    "avg_confidence": doc.get("extraction_confidence", 0.9),
                },
                "index_result": {
                    "chunks_indexed": doc.get("pages_total", 0) * 3,
                    "status": "completed",
                },
                "completed_at": doc.get("updated_at", ""),
            }
        )
        return base

    if status == "processing":
        total = doc.get("pages_total", 1) or 1
        processed = doc.get("pages_processed", 0)
        base["progress_percent"] = int((processed / total) * 100)
        base["estimated_completion"] = utcnow()
        base["started_at"] = doc.get("created_at", "")
        return base

    if status == "failed":
        base.update(
            {
                "progress_percent": 50,
                "error": {
                    "code": "OCR_FAILED",
                    "message": "Ошибка OCR-распознавания",
                    "details": {"failed_pages": doc.get("pages_failed", 0)},
                },
                "failed_at": doc.get("updated_at", ""),
            }
        )
        return base

    # queued
    return base


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
    doc = _get_document(doc_id)
    del _documents[doc_id]
    # Также удаляем из очереди
    global _queue
    _queue = [q for q in _queue if q["document_id"] != doc_id]
    return {
        "document_id": doc_id,
        "deleted_at": utcnow(),
    }


@router.post("/documents/{doc_id}/reprocess", status_code=202)
async def reprocess_document(doc_id: str, req: Optional[ReprocessRequest] = None):
    """Переобработка документа."""
    doc = _get_document(doc_id)
    mode = req.mode if req and req.mode else "full"

    # Сбрасываем статус
    doc["status"] = "queued"
    doc["ocr_status"] = "pending"
    doc["index_status"] = "pending"
    doc["updated_at"] = utcnow()

    _queue.append(
        {
            "document_id": doc_id,
            "title": doc.get("title", ""),
            "document_type": doc.get("document_type", ""),
            "status": "queued",
            "progress_percent": 0,
            "steps": {
                "ocr": "pending",
                "layout_parsing": "pending",
                "indexing": "pending",
            },
            "user_id": doc.get("user_id", ""),
            "uploaded_by": doc.get("uploaded_by", ""),
            "created_at": utcnow(),
            "started_at": None,
            "estimated_completion": None,
        }
    )

    return {
        "mode": mode,
        "document_id": doc_id,
        "user_id": doc.get("user_id", ""),
        "task_id": f"task-{new_id()}",
        "status": "queued",
        "created_at": utcnow(),
    }


@router.get("/documents/{doc_id}/errors")
async def get_document_errors(
    doc_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Ошибки обработки документа."""
    doc = _get_document(doc_id)
    items = [e for e in _document_errors if e["document_id"] == doc_id]

    paged = paginate(items, page, page_size)
    return {
        "errors": paged["items"],
        "meta": paged["meta"],
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
        "document_type": doc.get("document_type", ""),
        "parameters": params,
        "extraction_confidence": doc.get("extraction_confidence", 0.0),
        "unconfirmed_fields": doc.get("unconfirmed_fields", []),
        "updated_at": doc.get("updated_at", ""),
    }


# ===========================================================================
# Группа validate
# ===========================================================================


@router.post("/validate/compare", status_code=202)
async def validate_compare(req: ValidateCompareRequest):
    """Сравнение с эталоном (асинхронно)."""
    comparison_id = f"comp-{new_id()}"
    now = utcnow()

    new_comparison = {
        "comparison_id": comparison_id,
        "status": "processing",
        "normative_block": {
            "document_id": req.normative_fragment_id or "rd-001",
            "document_title": "ГОСТ 2.109-73",
            "page": 5,
            "requirement_text": "Толщина стенки должна быть не менее 4 мм для данного типа изделий.",
        },
        "project_block": {
            "document_id": req.project_document_id or "doc-001",
            "document_title": "Спецификация по ГОСТ 2.109",
            "page": 3,
            "parameter_text": "Толщина стенки: 5 мм",
        },
        "match_status": "match",
        "details": "Значение 5 мм соответствует требованию ≥ 4 мм.",
        "sources": [
            {"document_id": "rd-001", "page": 5},
            {"document_id": "doc-001", "page": 3},
        ],
        "disclaimer": "Результат требует инженерной верификации.",
        "processing_time_ms": random.randint(500, 3000),
    }
    _comparisons[comparison_id] = new_comparison

    return {
        "normative_query": req.normative_query or "",
        "project_document_id": req.project_document_id or "",
        "normative_fragment_id": req.normative_fragment_id or "",
        "project_fragment_id": req.project_fragment_id or "",
        "comparison_id": comparison_id,
        "status": "processing",
        "created_at": now,
    }


@router.get("/validate/compare/{comparison_id}")
async def get_comparison(comparison_id: str):
    """Результат сравнения."""
    comparison = _comparisons.get(comparison_id)
    if not comparison:
        raise HTTPException(
            status_code=404,
            detail=error_response("NOT_FOUND", "Сравнение не найдено"),
        )

    # Если статус processing, через пару вызовов станет completed
    if comparison["status"] == "processing":
        comparison["status"] = "completed"

    return comparison


@router.post("/validate/checks", status_code=200, response_model=CheckResultResponse)
async def validate_checks(req: ValidateChecksRequest):
    """Массовая проверка по НСИ (синхронно)."""
    check_run_id = f"check-{new_id()}"
    now = utcnow()

    # Генерируем mock-результаты
    mock_items = []
    statuses = ["ok", "warning", "error"]
    match_statuses = ["match", "mismatch", "partial_match"]
    ok_count = 0
    warn_count = 0
    err_count = 0

    for i in range(5):
        s = random.choices(statuses, weights=[6, 3, 1])[0]
        if s == "ok":
            ok_count += 1
        elif s == "warning":
            warn_count += 1
        else:
            err_count += 1

        mock_items.append(
            {
                "check_item_id": f"ci-{new_id()}",
                "project": "ПКБ-101",
                "section": f"Раздел {i + 1}",
                "parameter": f"Параметр {i + 1}",
                "project_value": f"Значение {i + 1}",
                "nsi_requirement": f"Требование {i + 1}",
                "nsi_document": f"ГОСТ 2.{100 + i * 10}-73",
                "status": s,
                "match_status": random.choice(match_statuses),
                "comment": "" if s == "ok" else "Требуется проверка",
                "project_source": {
                    "document_id": req.project_document_ids[0]
                    if req.project_document_ids
                    else "doc-001",
                    "page": i + 1,
                    "page_preview_url": f"/api/v1/documents/{req.project_document_ids[0] if req.project_document_ids else 'doc-001'}/pages/{i + 1}/preview",
                    "document_url": f"/api/v1/documents/{req.project_document_ids[0] if req.project_document_ids else 'doc-001'}",
                },
                "nsi_source": {
                    "document_id": req.nsi_document_ids[0]
                    if req.nsi_document_ids
                    else "rd-001",
                    "page": i + 1,
                    "page_preview_url": f"/api/v1/documents/{req.nsi_document_ids[0] if req.nsi_document_ids else 'rd-001'}/pages/{i + 1}/preview",
                    "document_url": f"/api/v1/documents/{req.nsi_document_ids[0] if req.nsi_document_ids else 'rd-001'}",
                },
            }
        )

    new_check = {
        "check_run_id": check_run_id,
        "status": "completed",
        "summary": {"ok": ok_count, "warning": warn_count, "error": err_count},
        "items": mock_items,
        "created_at": now,
        "updated_at": now,
    }
    _validation_checks[check_run_id] = new_check

    return new_check


@router.get("/validate/checks/{check_run_id}")
async def get_check_result(check_run_id: str):
    """Статус проверки."""
    check = _validation_checks.get(check_run_id)
    if not check:
        raise HTTPException(
            status_code=404,
            detail=error_response("NOT_FOUND", "Проверка не найдена"),
        )

    return {
        "check_run_id": check["check_run_id"],
        "status": check.get("status", "completed"),
        "progress_percent": 100 if check.get("status") == "completed" else 50,
        "created_at": check.get("created_at", ""),
        "updated_at": check.get("updated_at", ""),
    }


@router.get("/validate/checks/{check_run_id}/export")
async def export_check_result(
    check_run_id: str,
    format: str = Query("pdf"),
):
    """Экспорт результата проверки."""
    check = _validation_checks.get(check_run_id)
    if not check:
        raise HTTPException(
            status_code=404,
            detail=error_response("NOT_FOUND", "Проверка не найдена"),
        )

    return {
        "check_run_id": check_run_id,
        "export_url": f"/api/v1/exports/check_{check_run_id}.{format}",
        "format": format,
        "created_at": utcnow(),
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
