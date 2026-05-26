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


from common import (
    SEED_CLASSIFIER_PENDING,
    SEED_CLASSIFIERS,
    SEED_REGISTRY_DOCUMENTS,
    SEED_TERMINOLOGY,
    error_response,
    new_id,
    paginate_registry,
    utcnow,
)
from fastapi import APIRouter, FastAPI, HTTPException, Query
from pydantic import BaseModel

main_router = APIRouter(prefix="/api/v1")
registry_docs_router = APIRouter()
admin_router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory хранилища
# ---------------------------------------------------------------------------

_classifiers: dict[str, dict] = {}
_terminology: dict[str, dict] = {}
_registry_docs: dict[str, dict] = {}
_pending_classifiers: dict[str, dict] = {}
_doc_history: dict[str, list] = {}


def _init_data():
    global \
        _classifiers, \
        _terminology, \
        _registry_docs, \
        _pending_classifiers, \
        _doc_history
    if _classifiers and _terminology:
        return  # already initialized — preserve existing state
    _classifiers = {c["code"]: copy.deepcopy(c) for c in SEED_CLASSIFIERS}
    _terminology = {t["id"]: copy.deepcopy(t) for t in SEED_TERMINOLOGY}
    _registry_docs = {d["id"]: copy.deepcopy(d) for d in SEED_REGISTRY_DOCUMENTS}
    _pending_classifiers = {p["id"]: copy.deepcopy(p) for p in SEED_CLASSIFIER_PENDING}
    _doc_history = {}
    for d in SEED_REGISTRY_DOCUMENTS:
        _doc_history[d["id"]] = [
            {
                "history_id": f"hist-{new_id()}",
                "doc_id": d["id"],
                "previous_status": None,
                "new_status": d.get("status", "draft"),
                "comment": "Initial state",
                "changed_by": d.get("created_by", "system"),
                "changed_at": d.get("created_at", utcnow()),
            }
        ]


def _build_tree(
    nodes: dict[str, dict],
    parent_code: str | None = None,
    classifier_system: str | None = None,
    depth: int = 0,
) -> list:
    """Строит дерево классификаторов."""
    result = []
    for code, node in sorted(nodes.items()):
        if node.get("parent_code") == parent_code:
            if (
                classifier_system is not None
                and node.get("classifier_system") != classifier_system
            ):
                continue
            children = _build_tree(nodes, code, classifier_system, depth + 1)
            entry = {
                "code": node["code"],
                "classifier_system": node.get("classifier_system", "MKS"),
                "full_name": node["full_name"],
                "parent_code": node.get("parent_code"),
                "status": node.get("status", "active"),
                "effective_date": node.get("effective_date"),
                "replaced_by": node.get("replaced_by"),
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
    classifier_system: str = "MKS"
    code: str
    parent_code: str | None = None
    full_name: str
    status: str = "active"
    effective_date: str | None = None


class ClassifierUpdate(BaseModel):
    classifier_system: str | None = None
    parent_code: str | None = None
    full_name: str | None = None
    status: str | None = None
    effective_date: str | None = None
    replaced_by: str | None = None


class ClassifierImportRow(BaseModel):
    classifier_system: str = "MKS"
    code: str
    full_name: str
    parent_code: str | None = None
    status: str = "active"
    effective_date: str | None = None


class ClassifierImportRequest(BaseModel):
    items: list[ClassifierImportRow]


class TermCreate(BaseModel):
    raw_term: str
    standard_term: str | None = None
    normalized_value: str | None = None
    term_type: str = "preferred"
    is_case_sensitive: bool = False
    definition: str | None = None
    synonyms: list[str] | None = None
    related_docs: list[str] | None = None
    scope: str | None = None
    is_blocked: bool = False


class TermUpdate(BaseModel):
    raw_term: str | None = None
    standard_term: str | None = None
    normalized_value: str | None = None
    term_type: str | None = None
    is_case_sensitive: bool | None = None
    definition: str | None = None
    synonyms: list[str] | None = None
    related_docs: list[str] | None = None
    scope: str | None = None
    is_blocked: bool | None = None


class TermImportRow(BaseModel):
    raw_term: str
    standard_term: str | None = None
    normalized_value: str | None = None
    term_type: str = "preferred"
    is_case_sensitive: bool = False
    definition: str | None = None
    synonyms: list[str] | None = None
    related_docs: list[str] | None = None
    scope: str | None = None
    is_blocked: bool = False


class TermImportRequest(BaseModel):
    items: list[TermImportRow]


class RegistryDocCreate(BaseModel):
    title: str
    doc_code: str
    source_type: str = "GOST"
    status: str = "draft"
    era: str = "CURRENT"
    validity_status: str = "active"
    jurisdiction: str | None = None
    issuing_body: str | None = None
    mks_oks_code: str | None = None
    okstu_code: str | None = None


class RegistryDocUpdate(BaseModel):
    title: str | None = None
    doc_code: str | None = None
    source_type: str | None = None
    status: str | None = None
    era: str | None = None
    validity_status: str | None = None
    jurisdiction: str | None = None
    issuing_body: str | None = None
    mks_oks_code: str | None = None
    okstu_name: str | None = None
    okstu_code: str | None = None
    successor_doc_id: str | None = None
    predecessor_doc_id: str | None = None


class RegistryDocStatusUpdate(BaseModel):
    status: str
    comment: str | None = None
    changed_by: str | None = None


# ---------------------------------------------------------------------------
# Инициализация
# ---------------------------------------------------------------------------

_init_data()


# ===========================================================================
# 1. Группа classifiers (main_router)
# ===========================================================================


@main_router.get("/classifiers")
async def list_classifiers(
    search: str | None = Query(None),
    classifier_system: str | None = Query(None),
    status: str | None = Query(None),
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
    if classifier_system:
        items = [c for c in items if c.get("classifier_system") == classifier_system]
    if status:
        items = [c for c in items if c.get("status") == status]

    result = []
    for c in items:
        result.append(
            {
                "code": c["code"],
                "classifier_system": c.get("classifier_system", "MKS"),
                "parent_code": c.get("parent_code"),
                "full_name": c.get("full_name"),
                "status": c.get("status", "active"),
                "effective_date": c.get("effective_date"),
                "replaced_by": c.get("replaced_by"),
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
                node["classifier_system"] = row.classifier_system
                node["full_name"] = row.full_name
                if row.parent_code is not None:
                    node["parent_code"] = row.parent_code
                node["status"] = row.status
                node["effective_date"] = row.effective_date
                node["updated_at"] = utcnow()
                updated += 1
            else:
                now = utcnow()
                _classifiers[row.code] = {
                    "classifier_system": row.classifier_system,
                    "code": row.code,
                    "parent_code": row.parent_code,
                    "full_name": row.full_name,
                    "status": row.status,
                    "effective_date": row.effective_date,
                    "replaced_by": None,
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


# ---------------------------------------------------------------------------
# 1a. Quarantine endpoints (main_router)
# ---------------------------------------------------------------------------


@main_router.get("/classifiers/quarantine")
async def list_quarantine(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Список элементов в карантине классификаторов."""
    items = list(_pending_classifiers.values())

    if status:
        items = [p for p in items if p.get("status") == status]

    result = []
    for p in items:
        result.append(
            {
                "id": p["id"],
                "system": p.get("system"),
                "code": p.get("code"),
                "found_in_document_id": p.get("found_in_document_id"),
                "found_in_document_title": p.get("found_in_document_title"),
                "status": p.get("status"),
                "suggested_parent_code": p.get("suggested_parent_code"),
                "suggested_parent_name": p.get("suggested_parent_name"),
                "admin_comment": p.get("admin_comment"),
                "created_at": p.get("created_at"),
            }
        )

    return paginate_registry(result, page, page_size)


@main_router.post("/classifiers/quarantine/{pending_id}/accept")
async def accept_quarantine(pending_id: str):
    """Принять элемент из карантина в классификатор."""
    pending = _pending_classifiers.get(pending_id)
    if not pending:
        raise HTTPException(
            status_code=404,
            detail=error_response("PENDING_NOT_FOUND", "Элемент карантина не найден"),
        )

    # Создаём узел классификатора из pending-элемента
    now = utcnow()
    new_code = pending.get("code", f"auto-{new_id()}")
    classifier_node = {
        "classifier_system": pending.get("system", "MKS"),
        "code": new_code,
        "parent_code": pending.get("suggested_parent_code"),
        "full_name": pending.get("found_in_document_title", ""),
        "status": "active",
        "effective_date": now[:10],
        "replaced_by": None,
        "created_at": now,
        "updated_at": now,
    }
    _classifiers[new_code] = classifier_node

    # Обновляем статус pending
    pending["status"] = "accepted"
    pending["admin_comment"] = f"Accepted and moved to classifier as {new_code}"

    return {
        "data": {
            "id": pending_id,
            "status": "accepted",
            "classifier_code": new_code,
            "classifier_system": classifier_node["classifier_system"],
            "updated_at": now,
        }
    }


@main_router.post("/classifiers/quarantine/{pending_id}/reject")
async def reject_quarantine(pending_id: str):
    """Отклонить элемент из карантина."""
    pending = _pending_classifiers.get(pending_id)
    if not pending:
        raise HTTPException(
            status_code=404,
            detail=error_response("PENDING_NOT_FOUND", "Элемент карантина не найден"),
        )

    now = utcnow()
    pending["status"] = "rejected"
    pending["admin_comment"] = "Rejected by administrator"

    return {
        "data": {
            "id": pending_id,
            "status": "rejected",
            "updated_at": now,
        }
    }


@main_router.post("/classifiers/validate")
async def validate_classification(req: dict):
    """Валидация классификационного кода (мок)."""
    code = req.get("code", "")
    classifier_system = req.get("classifier_system", "MKS")

    node = _classifiers.get(code) if code else None
    system_valid = classifier_system in ["MKS", "OKSTU", "UDC", "EXTERNAL"]

    valid = node is not None and system_valid
    return {
        "data": {
            "valid": valid,
            "code": code,
            "classifier_system": classifier_system,
            "exists_in_registry": node is not None,
            "validation_status": "VALID"
            if valid
            else ("ERROR" if not system_valid else "WARNING"),
            "message": "Validation passed" if valid else "Validation failed",
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
        "classifier_system": req.classifier_system,
        "code": req.code,
        "parent_code": req.parent_code,
        "full_name": req.full_name,
        "status": req.status,
        "effective_date": req.effective_date,
        "replaced_by": None,
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
    search: str | None = Query(None),
    term_type: str | None = Query(None),
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
            if search_lower in t.get("raw_term", "").lower()
            or search_lower in t.get("standard_term", "").lower()
            or search_lower in t.get("normalized_value", "").lower()
            or any(search_lower in (s or "").lower() for s in t.get("synonyms", []))
        ]
    if term_type:
        items = [t for t in items if t.get("term_type") == term_type]

    result = []
    for t in items:
        result.append(
            {
                "id": t["id"],
                "raw_term": t.get("raw_term"),
                "standard_term": t.get("standard_term"),
                "normalized_value": t.get("normalized_value"),
                "term_type": t.get("term_type"),
                "is_case_sensitive": t.get("is_case_sensitive", False),
                "definition": t.get("definition"),
                "synonyms": t.get("synonyms", []),
                "related_docs": t.get("related_docs", []),
                "scope": t.get("scope"),
                "is_blocked": t.get("is_blocked", False),
                "created_at": t.get("created_at"),
                "updated_at": t.get("updated_at"),
            }
        )

    return paginate_registry(result, page, page_size)


@main_router.get("/terminology/normalize")
async def normalize_term(q: str = Query(..., description="Термин для нормализации")):
    """Поиск нормализованной формы термина."""
    q_lower = q.lower()
    found = None
    for t in _terminology.values():
        if t.get("normalized_value", "").lower() == q_lower:
            found = t
            break
        if t.get("raw_term", "").lower() == q_lower:
            found = t
            break
        if t.get("standard_term", "").lower() == q_lower:
            found = t
            break
        if found is None and q_lower in t.get("raw_term", "").lower():
            found = t

    if found:
        return {
            "data": {
                "raw_term": found.get("raw_term"),
                "standard_term": found.get("standard_term"),
                "normalized_value": found.get(
                    "normalized_value", found.get("raw_term")
                ),
                "term_type": found.get("term_type"),
                "is_blocked": found.get("is_blocked", False),
            }
        }

    # Если не нашли, возвращаем исходный термин как нормализованный
    return {
        "data": {
            "raw_term": q,
            "standard_term": q.lower(),
            "normalized_value": q.lower(),
            "term_type": "preferred",
            "is_blocked": False,
        }
    }


@main_router.post("/terminology/import")
async def import_terminology(req: TermImportRequest):
    """Массовый импорт терминов с проверкой дубликатов."""
    inserted = 0
    updated = 0
    errors = []

    for row in req.items:
        try:
            # Проверка дубликата по raw_term
            existing_id = None
            for tid, term in _terminology.items():
                if term.get("raw_term", "").lower() == row.raw_term.lower():
                    existing_id = tid
                    break

            now = utcnow()
            if existing_id:
                # Update existing term
                existing = _terminology[existing_id]
                existing["standard_term"] = row.standard_term or existing.get(
                    "standard_term", row.raw_term.lower()
                )
                existing["normalized_value"] = row.normalized_value or existing.get(
                    "normalized_value", row.raw_term.lower()
                )
                existing["term_type"] = row.term_type
                existing["is_case_sensitive"] = row.is_case_sensitive
                if row.definition is not None:
                    existing["definition"] = row.definition
                if row.synonyms is not None:
                    existing["synonyms"] = row.synonyms
                if row.related_docs is not None:
                    existing["related_docs"] = row.related_docs
                if row.scope is not None:
                    existing["scope"] = row.scope
                existing["is_blocked"] = row.is_blocked
                existing["updated_at"] = now
                updated += 1
            else:
                # Create new term
                term_id = f"t-{new_id()}"
                _terminology[term_id] = {
                    "id": term_id,
                    "raw_term": row.raw_term,
                    "standard_term": row.standard_term or row.raw_term.lower(),
                    "normalized_value": row.normalized_value or row.raw_term.lower(),
                    "term_type": row.term_type,
                    "is_case_sensitive": row.is_case_sensitive,
                    "definition": row.definition,
                    "synonyms": row.synonyms or [],
                    "related_docs": row.related_docs or [],
                    "scope": row.scope,
                    "is_blocked": row.is_blocked,
                    "created_at": now,
                    "updated_at": now,
                }
                inserted += 1
        except Exception as e:
            errors.append(
                {"row": row.raw_term, "code": "IMPORT_ERROR", "message": str(e)}
            )

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
    now = utcnow()
    new_term = {
        "id": term_id,
        "raw_term": req.raw_term,
        "standard_term": req.standard_term or req.raw_term.lower(),
        "normalized_value": req.normalized_value or req.raw_term.lower(),
        "term_type": req.term_type,
        "is_case_sensitive": req.is_case_sensitive,
        "definition": req.definition,
        "synonyms": req.synonyms or [],
        "related_docs": req.related_docs or [],
        "scope": req.scope,
        "is_blocked": req.is_blocked,
        "created_at": now,
        "updated_at": now,
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

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            term[key] = value
    term["updated_at"] = utcnow()

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
    return {"data": {"id": term_id, "deleted": True, "deleted_at": utcnow()}}


# ===========================================================================
# 3. Группа documents (registry_docs_router)
# ===========================================================================


@registry_docs_router.get("/documents")
async def list_registry_documents(
    search: str | None = Query(None),
    status: str | None = Query(None),
    source_type: str | None = Query(None),
    era: str | None = Query(None),
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
            or search_lower in d.get("doc_code", "").lower()
        ]
    if status:
        items = [d for d in items if d.get("status") == status]
    if source_type:
        items = [d for d in items if d.get("source_type") == source_type]
    if era:
        items = [d for d in items if d.get("era") == era]

    result = []
    for d in items:
        result.append(
            {
                "id": d["id"],
                "title": d.get("title"),
                "doc_code": d.get("doc_code"),
                "source_type": d.get("source_type"),
                "title_hash_sha256": d.get("title_hash_sha256"),
                "status": d.get("status"),
                "era": d.get("era"),
                "validity_status": d.get("validity_status"),
                "jurisdiction": d.get("jurisdiction"),
                "issuing_body": d.get("issuing_body"),
                "mks_oks_code": d.get("mks_oks_code"),
                "mks_name": d.get("mks_name"),
                "okstu_code": d.get("okstu_code"),
                "okstu_name": d.get("okstu_name"),
                "classification_status": d.get("classification_status"),
                "successor_doc_id": d.get("successor_doc_id"),
                "predecessor_doc_id": d.get("predecessor_doc_id"),
                "total_versions": d.get("total_versions"),
                "chunk_count": d.get("chunk_count"),
                "created_by": d.get("created_by"),
                "updated_by": d.get("updated_by"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
            }
        )

    return paginate_registry(result, page, page_size)


@registry_docs_router.get("/documents/export")
async def export_registry_documents(
    format: str = Query("json"),
    status: str | None = Query(None),
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
async def import_registry_documents(req: list[RegistryDocCreate]):
    """Массовый импорт документов в реестр с проверкой дубликатов по doc_code."""
    inserted = 0
    updated = 0
    errors = []

    for item in req:
        try:
            # Проверка дубликата по doc_code
            existing_id = None
            if item.doc_code:
                for did, doc in _registry_docs.items():
                    if doc.get("doc_code") == item.doc_code:
                        existing_id = did
                        break

            now = utcnow()
            if existing_id:
                # Update existing document
                existing = _registry_docs[existing_id]
                existing["title"] = item.title
                existing["source_type"] = item.source_type
                existing["status"] = item.status
                existing["era"] = item.era
                existing["validity_status"] = item.validity_status
                if item.jurisdiction is not None:
                    existing["jurisdiction"] = item.jurisdiction
                if item.issuing_body is not None:
                    existing["issuing_body"] = item.issuing_body
                if item.mks_oks_code is not None:
                    existing["mks_oks_code"] = item.mks_oks_code
                    cl = _classifiers.get(item.mks_oks_code)
                    existing["mks_name"] = cl.get("full_name", "") if cl else ""
                if item.okstu_code is not None:
                    existing["okstu_code"] = item.okstu_code
                    cl = _classifiers.get(item.okstu_code)
                    existing["okstu_name"] = cl.get("full_name", "") if cl else ""
                existing["updated_at"] = now
                _doc_history[existing_id].append(
                    {
                        "history_id": f"hist-{new_id()}",
                        "doc_id": existing_id,
                        "previous_status": existing.get("status"),
                        "new_status": item.status,
                        "comment": "Document updated via import",
                        "changed_by": "system",
                        "changed_at": now,
                    }
                )
                updated += 1
            else:
                doc_id = f"rd-{new_id()}"
                mks_name = ""
                if item.mks_oks_code:
                    cl = _classifiers.get(item.mks_oks_code)
                    if cl:
                        mks_name = cl.get("full_name", "")
                okstu_name = ""
                if item.okstu_code:
                    cl = _classifiers.get(item.okstu_code)
                    if cl:
                        okstu_name = cl.get("full_name", "")

                new_doc = {
                    "id": doc_id,
                    "title": item.title,
                    "doc_code": item.doc_code,
                    "source_type": item.source_type,
                    "title_hash_sha256": None,
                    "status": item.status,
                    "era": item.era,
                    "validity_status": item.validity_status,
                    "jurisdiction": item.jurisdiction,
                    "issuing_body": item.issuing_body,
                    "mks_oks_code": item.mks_oks_code,
                    "mks_name": mks_name,
                    "okstu_code": item.okstu_code,
                    "okstu_name": okstu_name,
                    "classification_status": {
                        "mks_status": "unknown",
                        "okstu_status": "unknown",
                    },
                    "successor_doc_id": None,
                    "predecessor_doc_id": None,
                    "total_versions": 1,
                    "chunk_count": 0,
                    "created_by": "system",
                    "updated_by": "system",
                    "created_at": now,
                    "updated_at": now,
                }
                _registry_docs[doc_id] = new_doc
                _doc_history[doc_id] = [
                    {
                        "history_id": f"hist-{new_id()}",
                        "doc_id": doc_id,
                        "previous_status": None,
                        "new_status": item.status,
                        "comment": "Document created",
                        "changed_by": "system",
                        "changed_at": now,
                    }
                ]
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

    mks_name = ""
    if req.mks_oks_code:
        cl = _classifiers.get(req.mks_oks_code)
        if cl:
            mks_name = cl.get("full_name", "")
    okstu_name = ""
    if req.okstu_code:
        cl = _classifiers.get(req.okstu_code)
        if cl:
            okstu_name = cl.get("full_name", "")

    new_doc = {
        "id": doc_id,
        "title": req.title,
        "doc_code": req.doc_code,
        "source_type": req.source_type,
        "title_hash_sha256": None,
        "status": req.status,
        "era": req.era,
        "validity_status": req.validity_status,
        "jurisdiction": req.jurisdiction,
        "issuing_body": req.issuing_body,
        "mks_oks_code": req.mks_oks_code,
        "mks_name": mks_name,
        "okstu_code": req.okstu_code,
        "okstu_name": okstu_name,
        "classification_status": {
            "mks_status": "unknown",
            "okstu_status": "unknown",
        },
        "successor_doc_id": None,
        "predecessor_doc_id": None,
        "total_versions": 1,
        "chunk_count": 0,
        "created_by": "system",
        "updated_by": "system",
        "created_at": now,
        "updated_at": now,
    }
    _registry_docs[doc_id] = new_doc
    _doc_history[doc_id] = [
        {
            "history_id": f"hist-{new_id()}",
            "doc_id": doc_id,
            "previous_status": None,
            "new_status": req.status,
            "comment": "Document created",
            "changed_by": "system",
            "changed_at": now,
        }
    ]

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

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            doc[key] = value

    # If mks_oks_code changed, update mks_name
    if "mks_oks_code" in update_data and update_data["mks_oks_code"] is not None:
        cl = _classifiers.get(update_data["mks_oks_code"])
        doc["mks_name"] = cl.get("full_name", "") if cl else ""

    # If okstu_code changed, update okstu_name
    if "okstu_code" in update_data and update_data["okstu_code"] is not None:
        cl = _classifiers.get(update_data["okstu_code"])
        doc["okstu_name"] = cl.get("full_name", "") if cl else ""

    doc["updated_at"] = utcnow()
    doc["updated_by"] = "system"

    return {"data": doc}


@registry_docs_router.patch("/documents/{doc_id}/status")
async def update_document_status(doc_id: str, req: RegistryDocStatusUpdate):
    """Обновить статус документа с комментарием."""
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )

    previous_status = doc.get("status")
    new_status = req.status
    now = utcnow()

    doc["status"] = new_status
    doc["updated_at"] = now
    doc["updated_by"] = req.changed_by or "system"

    history_entry = {
        "history_id": f"hist-{new_id()}",
        "doc_id": doc_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "comment": req.comment or "Status updated",
        "changed_by": req.changed_by or "system",
        "changed_at": now,
    }

    if doc_id not in _doc_history:
        _doc_history[doc_id] = []
    _doc_history[doc_id].append(history_entry)

    return {
        "data": {
            "id": doc_id,
            "status": new_status,
            "previous_status": previous_status,
            "history_id": history_entry["history_id"],
            "updated_at": now,
        }
    }


@registry_docs_router.get("/documents/{doc_id}/history")
async def get_document_history(doc_id: str):
    """История изменений статуса документа."""
    if doc_id not in _registry_docs:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )

    history = _doc_history.get(doc_id, [])
    return {
        "data": {
            "doc_id": doc_id,
            "history": history,
        }
    }


@registry_docs_router.get("/documents/{doc_id}/chain")
async def get_document_chain(doc_id: str):
    """Цепочка наследования документа (преемник/предшественник)."""
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )

    # Build predecessor chain (walk backwards)
    predecessor_chain = []
    current_pred_id = doc.get("predecessor_doc_id")
    while current_pred_id:
        pred_doc = _registry_docs.get(current_pred_id)
        if pred_doc:
            predecessor_chain.append(
                {
                    "id": pred_doc["id"],
                    "title": pred_doc.get("title"),
                    "doc_code": pred_doc.get("doc_code"),
                    "status": pred_doc.get("status"),
                }
            )
            current_pred_id = pred_doc.get("predecessor_doc_id")
        else:
            break

    # Build successor chain (walk forwards)
    successor_chain = []
    current_succ_id = doc.get("successor_doc_id")
    while current_succ_id:
        succ_doc = _registry_docs.get(current_succ_id)
        if succ_doc:
            successor_chain.append(
                {
                    "id": succ_doc["id"],
                    "title": succ_doc.get("title"),
                    "doc_code": succ_doc.get("doc_code"),
                    "status": succ_doc.get("status"),
                }
            )
            current_succ_id = succ_doc.get("successor_doc_id")
        else:
            break

    return {
        "data": {
            "doc_id": doc_id,
            "current": {
                "id": doc["id"],
                "title": doc.get("title"),
                "doc_code": doc.get("doc_code"),
            },
            "predecessors": predecessor_chain,
            "successors": successor_chain,
        }
    }


@registry_docs_router.delete("/documents/{doc_id}")
async def delete_registry_document(doc_id: str):
    """Удалить документ из реестра."""
    if doc_id not in _registry_docs:
        raise HTTPException(
            status_code=404,
            detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"),
        )

    del _registry_docs[doc_id]
    if doc_id in _doc_history:
        del _doc_history[doc_id]
    return {"data": {"id": doc_id, "deleted": True, "deleted_at": utcnow()}}


# ===========================================================================
# 4. Группа common (main_router)
# ===========================================================================


@main_router.get("/common/stats")
async def get_registry_stats():
    """Статистика реестра."""
    docs = list(_registry_docs.values())
    docs_by_status = {}
    docs_by_source_type = {}
    docs_by_era = {}
    for d in docs:
        status = d.get("status", "draft")
        docs_by_status[status] = docs_by_status.get(status, 0) + 1
        source_type = d.get("source_type", "unknown")
        docs_by_source_type[source_type] = docs_by_source_type.get(source_type, 0) + 1
        era = d.get("era", "CURRENT")
        docs_by_era[era] = docs_by_era.get(era, 0) + 1

    # Classifiers by system
    classifiers_by_system = {}
    for c in _classifiers.values():
        system = c.get("classifier_system", "MKS")
        classifiers_by_system[system] = classifiers_by_system.get(system, 0) + 1

    return {
        "data": {
            "classifiers_total": {
                "MKS": classifiers_by_system.get("MKS", 0),
                "OKSTU": classifiers_by_system.get("OKSTU", 0),
                "UDC": classifiers_by_system.get("UDC", 0),
                "EXTERNAL": classifiers_by_system.get("EXTERNAL", 0),
            },
            "classifiers_pending": len(_pending_classifiers),
            "terminology_total": len(_terminology),
            "documents_total": len(_registry_docs),
            "documents_by_status": {
                "draft": docs_by_status.get("draft", 0),
                "uploaded": docs_by_status.get("uploaded", 0),
                "parsing": docs_by_status.get("parsing", 0),
                "validation": docs_by_status.get("validation", 0),
                "review_required": docs_by_status.get("review_required", 0),
                "ready_for_promotion": docs_by_status.get("ready_for_promotion", 0),
                "approved": docs_by_status.get("approved", 0),
                "failed": docs_by_status.get("failed", 0),
                "archived": docs_by_status.get("archived", 0),
            },
            "documents_by_source_type": dict(docs_by_source_type),
            "documents_by_era": {
                "USSR": docs_by_era.get("USSR", 0),
                "CIS": docs_by_era.get("CIS", 0),
                "RF": docs_by_era.get("RF", 0),
                "CURRENT": docs_by_era.get("CURRENT", 0),
            },
        }
    }


@main_router.get("/common/enums")
async def get_allowed_values():
    """Допустимые значения полей."""
    return {
        "data": {
            "classifier_system": ["MKS", "OKSTU", "UDC", "EXTERNAL"],
            "classifier_status": ["active", "expired", "replaced"],
            "source_type": ["GOST", "GOST_R", "OST", "TU", "ISO", "DNV", "ASTM"],
            "document_status": [
                "draft",
                "uploaded",
                "parsing",
                "validation",
                "review_required",
                "ready_for_promotion",
                "approved",
                "failed",
                "archived",
            ],
            "era": ["USSR", "CIS", "RF", "CURRENT"],
            "validity_status": ["active", "replaced", "cancelled"],
            "term_type": ["abbreviation", "synonym", "preferred", "deprecated"],
            "classification_status_code": ["valid", "deprecated", "unknown"],
            "pending_status": ["new", "review", "accepted", "rejected"],
            "validation_status": ["VALID", "WARNING", "ERROR"],
            "chunk_type": ["text", "table", "image"],
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

app = FastAPI(title="Registry Service Mock", version="2.0.0")
app.include_router(main_router)
app.include_router(registry_docs_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8084)
