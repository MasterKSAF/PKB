"""
Registry Service Mock
Сервис реестра НСИ (нормативно-справочной информации) — in-memory.
Порт: 8084
Формат ответа: wrapped-формат с полем 'data' (согласно common.md).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
from typing import Any, Dict, List, Optional

from common import (
    SEED_CLASSIFIERS,
    SEED_REGISTRY_DOCUMENTS,
    SEED_TERMINOLOGY,
    error_response,
    new_id,
    paginate_registry,
    utcnow,
)
from fastapi import APIRouter, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

main_router = APIRouter(prefix="/api/v1")
registry_docs_router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory хранилища
# ---------------------------------------------------------------------------

_classifiers: Dict[str, dict] = {}
_terminology: Dict[str, dict] = {}
_registry_docs: Dict[str, dict] = {}


def _init_data():
    global _classifiers, _terminology, _registry_docs
    _classifiers = {c["code"]: copy.deepcopy(c) for c in SEED_CLASSIFIERS}
    _terminology = {t["term_id"]: copy.deepcopy(t) for t in SEED_TERMINOLOGY}
    _registry_docs = {d["doc_id"]: copy.deepcopy(d) for d in SEED_REGISTRY_DOCUMENTS}


def _build_tree(
    nodes: Dict[str, dict], parent_code: Optional[str] = None, depth: int = 0
) -> list:
    """Строит дерево классификаторов."""
    result = []
    for code, node in sorted(nodes.items()):
        if node.get("parent_code") == parent_code:
            children = _build_tree(nodes, code, depth + 1)
            entry = {
                "code": node["code"],
                "full_name": node["full_name"],
                "doc_type": node["doc_type"],
                "oks_code": node.get("oks_code", ""),
                "is_thematic": node.get("is_thematic", False),
            }
            if children:
                entry["children"] = children
            result.append(entry)
    return result


def _count_children(code: str) -> int:
    """Считает количество прямых потомков."""
    return sum(1 for c in _classifiers.values() if c.get("parent_code") == code)


# ---------------------------------------------------------------------------
# Модели
# ---------------------------------------------------------------------------


class ClassifierCreate(BaseModel):
    code: str
    parent_code: Optional[str] = None
    full_name: str
    doc_type: str = "normative"
    jurisdiction: Optional[str] = None
    language: Optional[str] = None
    oks_code: Optional[str] = None
    is_thematic: bool = False


class ClassifierUpdate(BaseModel):
    full_name: Optional[str] = None
    parent_code: Optional[str] = None
    doc_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    language: Optional[str] = None
    oks_code: Optional[str] = None
    is_thematic: Optional[bool] = None


class TermCreate(BaseModel):
    term: str
    normalized_term: Optional[str] = None
    context: Optional[str] = None
    source: Optional[str] = None


class TermUpdate(BaseModel):
    term: Optional[str] = None
    normalized_term: Optional[str] = None
    context: Optional[str] = None
    source: Optional[str] = None


class RegistryDocCreate(BaseModel):
    title: str
    doc_number: str
    classifier_code: str
    status: str = "draft"
    source: Optional[str] = None
    notes: Optional[str] = None


class RegistryDocUpdate(BaseModel):
    title: Optional[str] = None
    doc_number: Optional[str] = None
    classifier_code: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class RegistryDocStatusUpdate(BaseModel):
    status: str


class ClassifierImportRow(BaseModel):
    code: str
    full_name: str
    parent_code: Optional[str] = None
    doc_type: str = "normative"
    oks_code: Optional[str] = None


class ClassifierImportRequest(BaseModel):
    items: List[ClassifierImportRow]


class TermImportRow(BaseModel):
    term: str
    normalized_term: Optional[str] = None
    context: Optional[str] = None
    source: Optional[str] = None


class TermImportRequest(BaseModel):
    items: List[TermImportRow]


# ---------------------------------------------------------------------------
# Инициализация
# ---------------------------------------------------------------------------

_init_data()


# ===========================================================================
# 1. Группа classifiers (main_router)
# ===========================================================================


@main_router.get("/classifiers")
async def list_classifiers(
    search: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Плоский список узлов классификатора."""
    items = list(_classifiers.values())

    if search:
        search_lower = search.lower()
        items = [
            c
            for c in items
            if search_lower in c.get("full_name", "").lower()
            or search_lower in c.get("code", "").lower()
        ]
    if doc_type:
        items = [c for c in items if c.get("doc_type") == doc_type]

    result = []
    for c in items:
        result.append(
            {
                "code": c["code"],
                "parent_code": c.get("parent_code"),
                "full_name": c.get("full_name"),
                "doc_type": c.get("doc_type"),
                "jurisdiction": c.get("jurisdiction"),
                "language": c.get("language"),
                "oks_code": c.get("oks_code"),
                "is_thematic": c.get("is_thematic", False),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at"),
            }
        )

    return paginate_registry(result, page, page_size)


@main_router.get("/classifiers/tree")
async def get_classifier_tree():
    """Иерархическое дерево классификаторов."""
    tree = _build_tree(_classifiers)
    return {
        "data": tree,
        "meta": {
            "total": len(_classifiers),
            "max_depth_reached": 5,
        },
    }


@main_router.post("/classifiers/import")
async def import_classifiers(req: ClassifierImportRequest):
    """Импорт узлов классификатора."""
    inserted = 0
    updated = 0
    errors = []

    for row in req.items:
        try:
            if row.code in _classifiers:
                node = _classifiers[row.code]
                node["full_name"] = row.full_name
                if row.parent_code is not None:
                    node["parent_code"] = row.parent_code
                if row.doc_type:
                    node["doc_type"] = row.doc_type
                if row.oks_code:
                    node["oks_code"] = row.oks_code
                node["updated_at"] = utcnow()
                updated += 1
            else:
                now = utcnow()
                _classifiers[row.code] = {
                    "code": row.code,
                    "parent_code": row.parent_code,
                    "full_name": row.full_name,
                    "doc_type": row.doc_type,
                    "jurisdiction": None,
                    "language": None,
                    "oks_code": row.oks_code,
                    "is_thematic": False,
                    "created_at": now,
                    "updated_at": now,
                }
                inserted += 1
        except Exception as e:
            errors.append({"row": row.code, "code": "IMPORT_ERROR", "message": str(e)})

    return {
        "data": {
            "inserted": inserted,
            "updated": updated,
            "errors": errors,
        }
    }


@main_router.get("/classifiers/{code}")
async def get_classifier_node(code: str):
    """Один узел классификатора."""
    node = _classifiers.get(code)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "CLASSIFIER_NOT_FOUND", "Узел классификатора не найден"
            ),
        )
    return {"data": node}


@main_router.post("/classifiers", status_code=201)
async def create_classifier(req: ClassifierCreate):
    """Создать узел классификатора."""
    if req.code in _classifiers:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "DUPLICATE_CODE", "Код классификатора уже существует"
            ),
        )

    now = utcnow()
    new_node = {
        "code": req.code,
        "parent_code": req.parent_code,
        "full_name": req.full_name,
        "doc_type": req.doc_type,
        "jurisdiction": req.jurisdiction,
        "language": req.language,
        "oks_code": req.oks_code,
        "is_thematic": req.is_thematic,
        "created_at": now,
        "updated_at": now,
    }
    _classifiers[req.code] = new_node
    return {"data": new_node}


@main_router.put("/classifiers/{code}")
async def update_classifier(code: str, req: ClassifierUpdate):
    """Обновить узел классификатора."""
    node = _classifiers.get(code)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "CLASSIFIER_NOT_FOUND", "Узел классификатора не найден"
            ),
        )

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            node[key] = value
    node["updated_at"] = utcnow()

    return {"data": node}


@main_router.patch("/classifiers/{code}")
async def patch_classifier(code: str, req: ClassifierUpdate):
    """Частичное обновление узла классификатора."""
    node = _classifiers.get(code)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "CLASSIFIER_NOT_FOUND", "Узел классификатора не найден"
            ),
        )

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            node[key] = value
    node["updated_at"] = utcnow()

    return {"data": node}


@main_router.delete("/classifiers/{code}")
async def delete_classifier(code: str):
    """Удалить узел классификатора."""
    if code not in _classifiers:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "CLASSIFIER_NOT_FOUND", "Узел классификатора не найден"
            ),
        )

    if _count_children(code) > 0:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "HAS_CHILDREN", "Нельзя удалить узел с дочерними элементами"
            ),
        )

    del _classifiers[code]
    return {"data": {"code": code, "deleted": True, "deleted_at": utcnow()}}


# ===========================================================================
# 2. Группа terminology (main_router)
# ===========================================================================


@main_router.get("/terminology")
async def list_terminology(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Список терминов."""
    items = list(_terminology.values())

    if search:
        search_lower = search.lower()
        items = [
            t
            for t in items
            if search_lower in t.get("term", "").lower()
            or search_lower in t.get("normalized_term", "").lower()
            or search_lower in t.get("context", "").lower()
        ]

    result = []
    for t in items:
        result.append(
            {
                "term_id": t["term_id"],
                "term": t.get("term"),
                "normalized_term": t.get("normalized_term"),
                "context": t.get("context"),
                "source": t.get("source"),
                "created_at": t.get("created_at"),
            }
        )

    return paginate_registry(result, page, page_size)


@main_router.get("/terminology/normalize")
async def normalize_term(q: str = Query(..., description="Термин для нормализации")):
    """Поиск нормализованной формы термина."""
    q_lower = q.lower()
    found = None
    for t in _terminology.values():
        if t.get("normalized_term", "").lower() == q_lower:
            found = t
            break
        if t.get("term", "").lower() == q_lower:
            found = t
            break
        if found is None and q_lower in t.get("term", "").lower():
            found = t

    if found:
        return {
            "data": {
                "original": q,
                "normalized": found.get("normalized_term", found["term"]),
                "term_id": found["term_id"],
                "context": found.get("context"),
            }
        }

    # Если не нашли, возвращаем исходный термин как нормализованный
    return {
        "data": {
            "original": q,
            "normalized": q.lower(),
            "term_id": None,
            "context": None,
        }
    }


@main_router.post("/terminology/import")
async def import_terminology(req: TermImportRequest):
    """Массовый импорт терминов."""
    inserted = 0
    updated = 0
    errors = []

    for row in req.items:
        try:
            term_id = f"t-{new_id()}"
            _terminology[term_id] = {
                "term_id": term_id,
                "term": row.term,
                "normalized_term": row.normalized_term or row.term.lower(),
                "context": row.context,
                "source": row.source,
                "created_at": utcnow(),
            }
            inserted += 1
        except Exception as e:
            errors.append({"row": row.term, "code": "IMPORT_ERROR", "message": str(e)})

    return {
        "data": {
            "inserted": inserted,
            "updated": updated,
            "errors": errors,
        }
    }


@main_router.get("/terminology/{term_id}")
async def get_term(term_id: str):
    """Один термин."""
    term = _terminology.get(term_id)
    if not term:
        raise HTTPException(
            status_code=404,
            detail=error_response("TERM_NOT_FOUND", "Термин не найден"),
        )
    return {"data": term}


@main_router.post("/terminology", status_code=201)
async def create_term(req: TermCreate):
    """Создать термин."""
    term_id = f"t-{new_id()}"
    new_term = {
        "term_id": term_id,
        "term": req.term,
        "normalized_term": req.normalized_term or req.term.lower(),
        "context": req.context,
        "source": req.source,
        "created_at": utcnow(),
    }
    _terminology[term_id] = new_term
    return {"data": new_term}


@main_router.put("/terminology/{term_id}")
async def update_term(term_id: str, req: TermUpdate):
    """Обновить термин."""
    term = _terminology.get(term_id)
    if not term:
        raise HTTPException(
            status_code=404,
            detail=error_response("TERM_NOT_FOUND", "Термин не найден"),
        )

    if req.term is not None:
        term["term"] = req.term
    if req.normalized_term is not None:
        term["normalized_term"] = req.normalized_term
    if req.context is not None:
        term["context"] = req.context
    if req.source is not None:
        term["source"] = req.source

    return {"data": term}


@main_router.delete("/terminology/{term_id}")
async def delete_term(term_id: str):
    """Удалить термин."""
    if term_id not in _terminology:
        raise HTTPException(
            status_code=404,
            detail=error_response("TERM_NOT_FOUND", "Термин не найден"),
        )
    del _terminology[term_id]
    return {"data": {"term_id": term_id, "deleted": True, "deleted_at": utcnow()}}


# ===========================================================================
# 3. Группа documents (registry_docs_router)
# ===========================================================================


@registry_docs_router.get("/documents")
async def list_registry_documents(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    classifier_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Список документов реестра НСИ."""
    items = list(_registry_docs.values())

    if search:
        search_lower = search.lower()
        items = [
            d
            for d in items
            if search_lower in d.get("title", "").lower()
            or search_lower in d.get("doc_number", "").lower()
        ]
    if status:
        items = [d for d in items if d.get("status") == status]
    if classifier_code:
        items = [d for d in items if d.get("classifier_code") == classifier_code]

    result = []
    for d in items:
        result.append(
            {
                "doc_id": d["doc_id"],
                "title": d.get("title"),
                "doc_number": d.get("doc_number"),
                "classifier_code": d.get("classifier_code"),
                "classifier_name": d.get("classifier_name"),
                "status": d.get("status"),
                "source": d.get("source"),
                "notes": d.get("notes"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
            }
        )

    return paginate_registry(result, page, page_size)


@registry_docs_router.get("/documents/export")
async def export_registry_documents(
    format: str = Query("json"),
    status: Optional[str] = Query(None),
):
    """Экспорт документов реестра."""
    items = list(_registry_docs.values())
    if status:
        items = [d for d in items if d.get("status") == status]

    return {
        "data": {
            "format": format,
            "total": len(items),
            "items": items,
            "exported_at": utcnow(),
        }
    }


@registry_docs_router.post("/documents/import")
async def import_registry_documents(req: List[RegistryDocCreate]):
    """Массовый импорт документов в реестр."""
    inserted = 0
    updated = 0
    errors = []

    for item in req:
        try:
            doc_id = f"rd-{new_id()}"
            now = utcnow()
            new_doc = {
                "doc_id": doc_id,
                "title": item.title,
                "doc_number": item.doc_number,
                "classifier_code": item.classifier_code,
                "classifier_name": _classifiers.get(item.classifier_code, {}).get(
                    "full_name", ""
                ),
                "status": item.status,
                "source": item.source,
                "notes": item.notes,
                "created_at": now,
                "updated_at": now,
            }
            _registry_docs[doc_id] = new_doc
            inserted += 1
        except Exception as e:
            errors.append(
                {"row": item.title, "code": "IMPORT_ERROR", "message": str(e)}
            )

    return {
        "data": {
            "inserted": inserted,
            "updated": updated,
            "errors": errors,
        }
    }


@registry_docs_router.get("/documents/{doc_id}")
async def get_registry_document(doc_id: str):
    """Один документ реестра."""
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )
    return {"data": doc}


@registry_docs_router.post("/documents", status_code=201)
async def create_registry_document(req: RegistryDocCreate):
    """Создать документ в реестре."""
    doc_id = f"rd-{new_id()}"
    now = utcnow()
    new_doc = {
        "doc_id": doc_id,
        "title": req.title,
        "doc_number": req.doc_number,
        "classifier_code": req.classifier_code,
        "classifier_name": _classifiers.get(req.classifier_code, {}).get(
            "full_name", ""
        ),
        "status": req.status,
        "source": req.source,
        "notes": req.notes,
        "created_at": now,
        "updated_at": now,
    }
    _registry_docs[doc_id] = new_doc
    return {"data": new_doc}


@registry_docs_router.put("/documents/{doc_id}")
async def update_registry_document(doc_id: str, req: RegistryDocUpdate):
    """Обновить документ реестра."""
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )

    if req.title is not None:
        doc["title"] = req.title
    if req.doc_number is not None:
        doc["doc_number"] = req.doc_number
    if req.classifier_code is not None:
        doc["classifier_code"] = req.classifier_code
        doc["classifier_name"] = _classifiers.get(req.classifier_code, {}).get(
            "full_name", ""
        )
    if req.source is not None:
        doc["source"] = req.source
    if req.notes is not None:
        doc["notes"] = req.notes
    doc["updated_at"] = utcnow()

    return {"data": doc}


@registry_docs_router.patch("/documents/{doc_id}/status")
async def update_document_status(doc_id: str, req: RegistryDocStatusUpdate):
    """Обновить статус документа."""
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )

    doc["status"] = req.status
    doc["updated_at"] = utcnow()

    return {"data": doc}


@registry_docs_router.delete("/documents/{doc_id}")
async def delete_registry_document(doc_id: str):
    """Удалить документ из реестра."""
    if doc_id not in _registry_docs:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )

    del _registry_docs[doc_id]
    return {"data": {"doc_id": doc_id, "deleted": True, "deleted_at": utcnow()}}


# ===========================================================================
# 4. Группа common (main_router)
# ===========================================================================


@main_router.get("/common/stats")
async def get_registry_stats():
    """Статистика реестра."""
    docs = list(_registry_docs.values())
    docs_by_status = {}
    for d in docs:
        status = d.get("status", "draft")
        docs_by_status[status] = docs_by_status.get(status, 0) + 1

    return {
        "data": {
            "classifiers_total": len(_classifiers),
            "terminology_total": len(_terminology),
            "documents_total": len(_registry_docs),
            "documents_by_status": {
                "draft": docs_by_status.get("draft", 0),
                "active": docs_by_status.get("active", 0),
                "obsolete": docs_by_status.get("obsolete", 0),
                "need_to_buy": docs_by_status.get("need_to_buy", 0),
                "searching": docs_by_status.get("searching", 0),
            },
        }
    }


@main_router.get("/common/enums")
async def get_allowed_values():
    """Допустимые значения полей."""
    return {
        "data": {
            "doc_type": ["normative", "archival_scan", "drawing", "specification"],
            "jurisdiction": ["GOST", "OST", "TU", "STO", "ISO", "IEC"],
            "language": ["ru", "en", "de", "fr"],
            "document_status": [
                "draft",
                "active",
                "obsolete",
                "need_to_buy",
                "searching",
            ],
            "context": [
                "ГОСТ 2.109-73, раздел 3",
                "ГОСТ 2.307-2011, п. 4.2",
                "ГОСТ 2.309-73",
                "ГОСТ 2.308-2011",
                "ГОСТ 2.104-2006",
            ],
            "file_document_type": [
                "normative",
                "archival_scan",
                "drawing",
                "specification",
            ],
            "file_document_status": [
                "queued",
                "processing",
                "completed",
                "failed",
                "pending",
            ],
            "check_result_status": ["ok", "warning", "error"],
            "match_status": ["match", "mismatch", "partial_match"],
            "ocr_engine": ["tesseract", "easyocr", "azure_read"],
            "chat_status": [
                "idle",
                "processing",
                "completed",
                "failed",
                "needs_review",
            ],
        }
    }


# ===========================================================================
# Health check (main_router)
# ===========================================================================


@main_router.get("/system/health")
async def health():
    return {
        "status": "ok",
        "service": "registry-service",
        "timestamp": utcnow(),
    }


# ===========================================================================
# Запуск
# ===========================================================================

app = FastAPI(title="Registry Service Mock", version="1.0.0")
app.include_router(main_router)
app.include_router(registry_docs_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8084)
