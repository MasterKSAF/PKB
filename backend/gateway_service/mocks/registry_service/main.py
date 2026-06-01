"""
Registry Service — автономный сервис реестра НСИ (in-memory).
Запуск: python main.py (порт REGISTRY_SERVICE_PORT, по умолчанию 8084)
"""

import copy
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Registry Service", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
        "VALIDATION_ERROR": 400,
        "NOT_FOUND": 404, "CLASSIFIER_NOT_FOUND": 404, "TERM_NOT_FOUND": 404, "DOCUMENT_NOT_FOUND": 404,
        "DUPLICATE_CODE": 409, "DUPLICATE_DOCUMENT": 409, "DUPLICATE_TERM": 409,
        "HAS_CHILDREN": 409, "HAS_DOCUMENTS": 409, "CROSS_SYSTEM_PARENT": 409,
        "INTERNAL_ERROR": 500,
    }
    http_code = status_map.get(code, 400)
    return JSONResponse(status_code=http_code, content={"error": {"code": code, "message": message, "details": details or {}}})

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    if isinstance(exc.detail, JSONResponse):
        return exc.detail
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return error_response("VALIDATION_ERROR", "Некорректные входные данные", {"errors": exc.errors()})

def paginate_registry(items: list, page: int, page_size: int) -> dict:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {"data": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}}

# ── сиды ──────────────────────────────────────────────────────────────────
SEED_CLASSIFIERS = [
    {"classifier_system": "MKS", "code": "47", "parent_code": None, "full_name": "Судостроение", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "MKS", "code": "47.020", "parent_code": "47", "full_name": "Конструкция корпуса", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "OKSTU", "code": "05.010", "parent_code": "05", "full_name": "Документы конструкторские", "status": "active", "effective_date": "1980-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
]
SEED_TERMINOLOGY = [
    {"id": "t-001", "raw_term": "ГОСТ", "standard_term": "ГОСТ", "normalized_value": "гост", "term_type": "standard_code", "is_case_sensitive": False, "definition": "Государственный стандарт", "synonyms": ["GOST", "gost"], "related_docs": [], "scope": "Стандартизация", "is_blocked": False, "created_at": "2025-12-01T08:00:00Z", "updated_at": "2026-01-15T12:00:00Z"},
    {"id": "t-002", "raw_term": "DNV", "standard_term": "DNV", "normalized_value": "dnv", "term_type": "acronym", "is_case_sensitive": True, "definition": "Det Norske Veritas", "synonyms": ["DNV GL"], "related_docs": [], "scope": "Судостроение", "is_blocked": False, "created_at": "2026-01-20T14:00:00Z", "updated_at": "2026-01-20T14:00:00Z"},
]
SEED_REGISTRY_DOCUMENTS = [
    {"id": "b3a8f1c2-4d5e-6f7a-8b9c-0d1e2f3a4b5c", "title": "Стойки установочные", "doc_code": "20868-81", "source_type": "GOST", "title_hash_sha256": None, "status": "approved", "era": "USSR", "validity_status": "active", "jurisdiction": "RU", "issuing_body": "Госстандарт СССР", "mks_oks_code": "31.240", "mks_name": "Электроника", "okstu_code": None, "okstu_name": None, "classification_status": {"mks_status": "CONFIRMED", "okstu_status": "NOT_USED"}, "successor_doc_id": None, "predecessor_doc_id": None, "total_versions": 2, "chunk_count": 34, "created_by": "system", "updated_by": "ivanov_ai", "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T14:00:00Z"}
]
SEED_CLASSIFIER_PENDING = [
    {"id": "p-001", "system": "MKS", "code": "47.020.99", "found_in_document_id": "b3a8f1c2-...", "found_in_document_title": "Стойки установочные", "status": "new", "suggested_parent_code": "47.020", "suggested_parent_name": "Конструкция корпуса", "admin_comment": None, "created_at": "2026-05-15T10:01:00Z"}
]

# ── in‑memory хранилища ───────────────────────────────────────────────────
_classifiers: Dict[str, dict] = {}
_terminology: Dict[str, dict] = {}
_registry_docs: Dict[str, dict] = {}
_pending_classifiers: Dict[str, dict] = {}
_doc_history: Dict[str, list] = {}

def init_data():
    global _classifiers, _terminology, _registry_docs, _pending_classifiers, _doc_history
    _classifiers = {c["code"]: copy.deepcopy(c) for c in SEED_CLASSIFIERS}
    _terminology = {t["id"]: copy.deepcopy(t) for t in SEED_TERMINOLOGY}
    _registry_docs = {d["id"]: copy.deepcopy(d) for d in SEED_REGISTRY_DOCUMENTS}
    _pending_classifiers = {p["id"]: copy.deepcopy(p) for p in SEED_CLASSIFIER_PENDING}
    _doc_history = {}
    for d in SEED_REGISTRY_DOCUMENTS:
        _doc_history[d["id"]] = [
            {"history_id": f"hist-{new_id()}", "doc_id": d["id"], "previous_status": None,
             "new_status": d.get("status", "draft"), "comment": "Initial state",
             "changed_by": d.get("created_by", "system"), "changed_at": d.get("created_at", utcnow())}
        ]

init_data()

# ── Pydantic модели ───────────────────────────────────────────────────────
class ClassifierCreate(BaseModel):
    classifier_system: str = "MKS"
    code: str
    parent_code: Optional[str] = None
    full_name: str
    status: str = "active"
    effective_date: Optional[str] = None

class ClassifierUpdate(BaseModel):
    classifier_system: Optional[str] = None
    parent_code: Optional[str] = None
    full_name: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[str] = None

class TermCreate(BaseModel):
    raw_term: str
    standard_term: Optional[str] = None
    normalized_value: Optional[str] = None
    term_type: str = "preferred"
    is_case_sensitive: bool = False
    definition: Optional[str] = None
    synonyms: Optional[List[str]] = None
    related_docs: Optional[List[str]] = None
    scope: Optional[str] = None
    is_blocked: bool = False

class TermUpdate(BaseModel):
    raw_term: Optional[str] = None
    standard_term: Optional[str] = None
    normalized_value: Optional[str] = None
    term_type: Optional[str] = None
    is_case_sensitive: Optional[bool] = None
    definition: Optional[str] = None
    synonyms: Optional[List[str]] = None
    related_docs: Optional[List[str]] = None
    scope: Optional[str] = None
    is_blocked: Optional[bool] = None

class RegistryDocCreate(BaseModel):
    title: str
    doc_code: str
    source_type: str = "GOST"
    status: str = "draft"
    era: str = "CURRENT"
    validity_status: str = "active"
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    mks_oks_code: Optional[str] = None
    okstu_code: Optional[str] = None

class RegistryDocUpdate(BaseModel):
    title: Optional[str] = None
    doc_code: Optional[str] = None
    source_type: Optional[str] = None
    status: Optional[str] = None
    era: Optional[str] = None
    validity_status: Optional[str] = None
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    mks_oks_code: Optional[str] = None
    okstu_code: Optional[str] = None
    successor_doc_id: Optional[str] = None
    predecessor_doc_id: Optional[str] = None

class RegistryDocStatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None
    changed_by: Optional[str] = None

# ── эндпоинты ─────────────────────────────────────────────────────────────

# 1. classifiers
@app.get("/api/v1/classifiers")
async def list_classifiers(search: str = None, classifier_system: str = None,
                           status: str = None, page: int = 1, page_size: int = 50):
    items = list(_classifiers.values())
    if search:
        s = search.lower()
        items = [c for c in items if s in c.get("full_name", "").lower() or s in c.get("code", "").lower()]
    if classifier_system:
        items = [c for c in items if c.get("classifier_system") == classifier_system]
    if status:
        items = [c for c in items if c.get("status") == status]
    result = [{"code": c["code"], "classifier_system": c.get("classifier_system"), "parent_code": c.get("parent_code"),
               "full_name": c["full_name"], "status": c.get("status"), "effective_date": c.get("effective_date"),
               "replaced_by": c.get("replaced_by"), "created_at": c.get("created_at"), "updated_at": c.get("updated_at")}
              for c in items]
    return paginate_registry(result, page, page_size)

@app.get("/api/v1/classifiers/tree")
async def get_tree():
    def build(nodes, parent_code=None, system=None):
        tree = []
        for code, node in sorted(nodes.items()):
            if node.get("parent_code") == parent_code and (system is None or node.get("classifier_system") == system):
                children = build(nodes, code, system)
                entry = {"code": node["code"], "classifier_system": node.get("classifier_system"),
                         "full_name": node["full_name"], "parent_code": node.get("parent_code"),
                         "status": node.get("status"), "effective_date": node.get("effective_date"),
                         "replaced_by": node.get("replaced_by")}
                if children:
                    entry["children"] = children
                tree.append(entry)
        return tree
    return {"data": build(_classifiers), "meta": {"total": len(_classifiers), "max_depth_reached": 5}}

@app.post("/api/v1/classifiers/import")
async def import_classifiers(req: List[ClassifierCreate]):
    inserted = updated = 0
    errors = []
    for row in req:
        try:
            if row.code in _classifiers:
                node = _classifiers[row.code]
                node.update({"classifier_system": row.classifier_system, "full_name": row.full_name,
                             "status": row.status, "effective_date": row.effective_date,
                             "parent_code": row.parent_code, "updated_at": utcnow()})
                updated += 1
            else:
                _classifiers[row.code] = {"classifier_system": row.classifier_system, "code": row.code,
                                         "parent_code": row.parent_code, "full_name": row.full_name,
                                         "status": row.status, "effective_date": row.effective_date,
                                         "replaced_by": None, "created_at": utcnow(), "updated_at": utcnow()}
                inserted += 1
        except Exception as e:
            errors.append({"row": row.code, "message": str(e)})
    return {"data": {"inserted": inserted, "updated": updated, "errors": errors}}

@app.get("/api/v1/classifiers/quarantine")
async def list_quarantine(status: str = None, page: int = 1, page_size: int = 50):
    items = list(_pending_classifiers.values())
    if status:
        items = [p for p in items if p.get("status") == status]
    return paginate_registry(items, page, page_size)

@app.post("/api/v1/classifiers/quarantine/{pending_id}/accept")
async def accept_quarantine(pending_id: str):
    pending = _pending_classifiers.get(pending_id)
    if not pending:
        raise HTTPException(404, detail=error_response("CLASSIFIER_NOT_FOUND", "Элемент карантина не найден"))
    code = pending.get("code", f"auto-{new_id()}")
    _classifiers[code] = {"classifier_system": pending.get("system", "MKS"), "code": code,
                          "parent_code": pending.get("suggested_parent_code"), "full_name": pending.get("found_in_document_title", ""),
                          "status": "active", "effective_date": utcnow()[:10], "replaced_by": None,
                          "created_at": utcnow(), "updated_at": utcnow()}
    pending["status"] = "accepted"
    return {"data": {"id": pending_id, "status": "accepted", "classifier_code": code}}

@app.post("/api/v1/classifiers/quarantine/{pending_id}/reject")
async def reject_quarantine(pending_id: str):
    pending = _pending_classifiers.get(pending_id)
    if not pending:
        raise HTTPException(404, detail=error_response("CLASSIFIER_NOT_FOUND", "Элемент карантина не найден"))
    pending["status"] = "rejected"
    return {"data": {"id": pending_id, "status": "rejected"}}

@app.post("/api/v1/classifiers/validate")
async def validate_classification(req: dict):
    code = req.get("mks_oks_code", req.get("code"))
    node = _classifiers.get(code) if code else None
    valid = node is not None
    status = "CONFIRMED" if valid else "NOT_FOUND"
    return {"data": {"mks_status": status, "okstu_status": "NOT_USED", "overall_status": "valid" if valid else "pending"}}

@app.get("/api/v1/classifiers/{code}")
async def get_classifier(code: str):
    node = _classifiers.get(code)
    if not node:
        raise HTTPException(404, detail=error_response("CLASSIFIER_NOT_FOUND", "Узел классификатора не найден"))
    return {"data": node}

@app.post("/api/v1/classifiers", status_code=201)
async def create_classifier(req: ClassifierCreate):
    if req.code in _classifiers:
        raise HTTPException(409, detail=error_response("DUPLICATE_CODE", "Код уже существует"))
    new_node = {"classifier_system": req.classifier_system, "code": req.code, "parent_code": req.parent_code,
                "full_name": req.full_name, "status": req.status, "effective_date": req.effective_date,
                "replaced_by": None, "created_at": utcnow(), "updated_at": utcnow()}
    _classifiers[req.code] = new_node
    return {"data": new_node}

@app.put("/api/v1/classifiers/{code}")
async def update_classifier(code: str, req: ClassifierUpdate):
    node = _classifiers.get(code)
    if not node:
        raise HTTPException(404, detail=error_response("CLASSIFIER_NOT_FOUND", "Узел не найден"))
    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            node[k] = v
    node["updated_at"] = utcnow()
    return {"data": node}

@app.patch("/api/v1/classifiers/{code}")
async def patch_classifier(code: str, req: ClassifierUpdate):
    return await update_classifier(code, req)

@app.delete("/api/v1/classifiers/{code}")
async def delete_classifier(code: str):
    node = _classifiers.get(code)
    if not node:
        raise HTTPException(404, detail=error_response("CLASSIFIER_NOT_FOUND", "Узел не найден"))
    children = sum(1 for c in _classifiers.values() if c.get("parent_code") == code)
    if children > 0:
        raise HTTPException(409, detail=error_response("HAS_CHILDREN", "Есть дочерние узлы"))
    del _classifiers[code]
    return {"data": {"code": code, "deleted": True}}

# 2. terminology
@app.get("/api/v1/terminology")
async def list_terms(search: str = None, term_type: str = None, page: int = 1, page_size: int = 50):
    items = list(_terminology.values())
    if search:
        s = search.lower()
        items = [t for t in items if s in t.get("raw_term","").lower() or s in t.get("standard_term","").lower()]
    if term_type:
        items = [t for t in items if t.get("term_type") == term_type]
    return paginate_registry(items, page, page_size)

@app.get("/api/v1/terminology/normalize")
async def normalize_term(term: str = Query(...)):
    q = term.lower()
    for t in _terminology.values():
        if t.get("normalized_value","").lower() == q or t.get("raw_term","").lower() == q:
            return {"data": {"raw_term": t["raw_term"], "standard_term": t["standard_term"],
                             "normalized_value": t.get("normalized_value", t["raw_term"]), "term_type": t.get("term_type"), "is_blocked": t.get("is_blocked", False)}}
    return {"data": {"raw_term": term, "standard_term": term.lower(), "normalized_value": term.lower(), "term_type": "preferred", "is_blocked": False}}

@app.post("/api/v1/terminology/import")
async def import_terms(req: List[TermCreate]):
    inserted = updated = 0
    errors = []
    for row in req:
        try:
            existing = next((t for t in _terminology.values() if t.get("raw_term","").lower() == row.raw_term.lower()), None)
            if existing:
                existing.update({"standard_term": row.standard_term or existing.get("standard_term"),
                                 "normalized_value": row.normalized_value or existing.get("normalized_value"),
                                 "term_type": row.term_type, "is_case_sensitive": row.is_case_sensitive,
                                 "definition": row.definition, "synonyms": row.synonyms or [],
                                 "related_docs": row.related_docs or [], "scope": row.scope,
                                 "is_blocked": row.is_blocked, "updated_at": utcnow()})
                updated += 1
            else:
                tid = f"t-{new_id()}"
                _terminology[tid] = {"id": tid, "raw_term": row.raw_term,
                                     "standard_term": row.standard_term or row.raw_term.lower(),
                                     "normalized_value": row.normalized_value or row.raw_term.lower(),
                                     "term_type": row.term_type, "is_case_sensitive": row.is_case_sensitive,
                                     "definition": row.definition, "synonyms": row.synonyms or [],
                                     "related_docs": row.related_docs or [], "scope": row.scope,
                                     "is_blocked": row.is_blocked, "created_at": utcnow(), "updated_at": utcnow()}
                inserted += 1
        except Exception as e:
            errors.append({"row": row.raw_term, "message": str(e)})
    return {"data": {"inserted": inserted, "updated": updated, "errors": errors}}

@app.get("/api/v1/terminology/{term_id}")
async def get_term(term_id: str):
    t = _terminology.get(term_id)
    if not t:
        raise HTTPException(404, detail=error_response("TERM_NOT_FOUND", "Термин не найден"))
    return {"data": t}

@app.post("/api/v1/terminology", status_code=201)
async def create_term(req: TermCreate):
    tid = f"t-{new_id()}"
    new_term = {"id": tid, "raw_term": req.raw_term, "standard_term": req.standard_term or req.raw_term.lower(),
                "normalized_value": req.normalized_value or req.raw_term.lower(), "term_type": req.term_type,
                "is_case_sensitive": req.is_case_sensitive, "definition": req.definition,
                "synonyms": req.synonyms or [], "related_docs": req.related_docs or [], "scope": req.scope,
                "is_blocked": req.is_blocked, "created_at": utcnow(), "updated_at": utcnow()}
    _terminology[tid] = new_term
    return {"data": new_term}

@app.put("/api/v1/terminology/{term_id}")
async def update_term(term_id: str, req: TermUpdate):
    t = _terminology.get(term_id)
    if not t:
        raise HTTPException(404, detail=error_response("TERM_NOT_FOUND", "Термин не найден"))
    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            t[k] = v
    t["updated_at"] = utcnow()
    return {"data": t}

@app.delete("/api/v1/terminology/{term_id}")
async def delete_term(term_id: str):
    if term_id not in _terminology:
        raise HTTPException(404, detail=error_response("TERM_NOT_FOUND", "Термин не найден"))
    del _terminology[term_id]
    return {"data": {"id": term_id, "deleted": True}}

# 3. documents (registry)
@app.get("/api/v1/documents")
async def list_registry_docs(search: str = None, status: str = None, source_type: str = None,
                             era: str = None, page: int = 1, page_size: int = 50):
    items = list(_registry_docs.values())
    if search:
        s = search.lower()
        items = [d for d in items if s in d.get("title","").lower() or s in d.get("doc_code","").lower()]
    if status:
        items = [d for d in items if d.get("status") == status]
    if source_type:
        items = [d for d in items if d.get("source_type") == source_type]
    if era:
        items = [d for d in items if d.get("era") == era]
    return paginate_registry(items, page, page_size)

@app.get("/api/v1/documents/export")
async def export_docs(format: str = "json"):
    return {"data": {"format": format, "total": len(_registry_docs), "items": list(_registry_docs.values())}}

@app.post("/api/v1/documents/import")
async def import_docs(req: List[RegistryDocCreate]):
    inserted = updated = 0
    errors = []
    for item in req:
        try:
            existing = next((d for d in _registry_docs.values() if d.get("doc_code") == item.doc_code), None)
            if existing:
                existing.update({"title": item.title, "source_type": item.source_type, "status": item.status,
                                 "era": item.era, "validity_status": item.validity_status,
                                 "jurisdiction": item.jurisdiction, "issuing_body": item.issuing_body,
                                 "mks_oks_code": item.mks_oks_code, "okstu_code": item.okstu_code,
                                 "updated_at": utcnow()})
                updated += 1
            else:
                doc_id = f"rd-{new_id()}"
                new_doc = {"id": doc_id, "title": item.title, "doc_code": item.doc_code, "source_type": item.source_type,
                           "status": item.status, "era": item.era, "validity_status": item.validity_status,
                           "jurisdiction": item.jurisdiction, "issuing_body": item.issuing_body,
                           "mks_oks_code": item.mks_oks_code, "okstu_code": item.okstu_code,
                           "title_hash_sha256": None, "classification_status": {}, "successor_doc_id": None,
                           "predecessor_doc_id": None, "total_versions": 1, "chunk_count": 0,
                           "created_by": "system", "updated_by": "system", "created_at": utcnow(), "updated_at": utcnow()}
                _registry_docs[doc_id] = new_doc
                _doc_history[doc_id] = [{"history_id": f"hist-{new_id()}", "doc_id": doc_id, "previous_status": None,
                                        "new_status": item.status, "comment": "Created", "changed_by": "system", "changed_at": utcnow()}]
                inserted += 1
        except Exception as e:
            errors.append({"row": item.title, "message": str(e)})
    return {"data": {"inserted": inserted, "updated": updated, "errors": errors}}

@app.get("/api/v1/documents/{doc_id}")
async def get_registry_doc(doc_id: str):
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    return {"data": doc}

@app.post("/api/v1/documents", status_code=201)
async def create_registry_doc(req: RegistryDocCreate):
    doc_id = f"rd-{new_id()}"
    new_doc = {"id": doc_id, "title": req.title, "doc_code": req.doc_code, "source_type": req.source_type,
               "status": req.status, "era": req.era, "validity_status": req.validity_status,
               "jurisdiction": req.jurisdiction, "issuing_body": req.issuing_body,
               "mks_oks_code": req.mks_oks_code, "okstu_code": req.okstu_code,
               "title_hash_sha256": None, "classification_status": {}, "successor_doc_id": None,
               "predecessor_doc_id": None, "total_versions": 1, "chunk_count": 0,
               "created_by": "system", "updated_by": "system", "created_at": utcnow(), "updated_at": utcnow()}
    _registry_docs[doc_id] = new_doc
    _doc_history[doc_id] = [{"history_id": f"hist-{new_id()}", "doc_id": doc_id, "previous_status": None,
                             "new_status": req.status, "comment": "Created", "changed_by": "system", "changed_at": utcnow()}]
    return {"data": new_doc}

@app.put("/api/v1/documents/{doc_id}")
async def update_registry_doc(doc_id: str, req: RegistryDocUpdate):
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            doc[k] = v
    doc["updated_at"] = utcnow()
    return {"data": doc}

@app.patch("/api/v1/documents/{doc_id}/status")
async def patch_status(doc_id: str, req: RegistryDocStatusUpdate):
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    prev = doc["status"]
    doc["status"] = req.status
    doc["updated_at"] = utcnow()
    entry = {"history_id": f"hist-{new_id()}", "doc_id": doc_id, "previous_status": prev,
             "new_status": req.status, "comment": req.comment or "Updated", "changed_by": req.changed_by or "system",
             "changed_at": utcnow()}
    _doc_history.setdefault(doc_id, []).append(entry)
    return {"data": {"id": doc_id, "status": req.status, "previous_status": prev, "history_id": entry["history_id"], "updated_at": utcnow()}}

@app.get("/api/v1/documents/{doc_id}/history")
async def doc_history(doc_id: str):
    if doc_id not in _registry_docs:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    return {"data": {"doc_id": doc_id, "history": _doc_history.get(doc_id, [])}}

@app.get("/api/v1/documents/{doc_id}/succession")
async def doc_succession(doc_id: str):
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    preds = []
    cur = doc.get("predecessor_doc_id")
    while cur:
        p = _registry_docs.get(cur)
        if p:
            preds.append({"id": p["id"], "title": p["title"], "doc_code": p["doc_code"], "era": p["era"]})
            cur = p.get("predecessor_doc_id")
        else:
            break
    succs = []
    cur = doc.get("successor_doc_id")
    while cur:
        s = _registry_docs.get(cur)
        if s:
            succs.append({"id": s["id"], "title": s["title"], "doc_code": s["doc_code"], "era": s["era"]})
            cur = s.get("successor_doc_id")
        else:
            break
    return {"data": {"document_id": doc_id, "chain": [
        *[{"id": p["id"], "title": p["title"], "doc_code": p["doc_code"], "era": p.get("era"), "relation": "predecessor", "depth": -(i+1)} for i, p in enumerate(preds)],
        {"id": doc["id"], "title": doc["title"], "doc_code": doc["doc_code"], "era": doc.get("era"), "relation": "self", "depth": 0},
        *[{"id": s["id"], "title": s["title"], "doc_code": s["doc_code"], "era": s.get("era"), "relation": "successor", "depth": i+1} for i, s in enumerate(succs)]
    ]}}

@app.delete("/api/v1/documents/{doc_id}")
async def delete_registry_doc(doc_id: str):
    if doc_id not in _registry_docs:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    del _registry_docs[doc_id]
    return {"data": {"id": doc_id, "deleted": True}}

# 4. common
@app.get("/api/v1/stats")
async def stats():
    docs_by_status = {}
    docs_by_source = {}
    docs_by_era = {}
    for d in _registry_docs.values():
        docs_by_status[d.get("status")] = docs_by_status.get(d.get("status"), 0) + 1
        docs_by_source[d.get("source_type")] = docs_by_source.get(d.get("source_type"), 0) + 1
        docs_by_era[d.get("era")] = docs_by_era.get(d.get("era"), 0) + 1
    class_by_sys = {}
    for c in _classifiers.values():
        class_by_sys[c.get("classifier_system")] = class_by_sys.get(c.get("classifier_system"), 0) + 1
    return {"data": {
        "classifiers_total": {"MKS": class_by_sys.get("MKS", 0), "OKSTU": class_by_sys.get("OKSTU", 0),
                              "UDC": class_by_sys.get("UDC", 0), "EXTERNAL": class_by_sys.get("EXTERNAL", 0)},
        "classifiers_pending": len(_pending_classifiers),
        "terminology_total": len(_terminology),
        "documents_total": len(_registry_docs),
        "documents_by_status": docs_by_status,
        "documents_by_source_type": docs_by_source,
        "documents_by_era": docs_by_era
    }}

@app.get("/api/v1/enums")
async def enums():
    return {"data": {
        "classifier_system": ["MKS", "OKSTU", "UDC", "EXTERNAL"],
        "classifier_status": ["active", "deprecated", "archived"],
        "source_type": ["GOST", "GOST_R", "OST", "RD", "TU", "ISO", "DNV", "ASTM", "OTHER"],
        "document_status": ["draft", "uploaded", "parsing", "validation", "review_required", "ready_for_promotion", "approved", "failed", "archived"],
        "era": ["USSR", "CIS", "RF", "CURRENT"],
        "validity_status": ["active", "superseded", "cancelled", "historical", "draft"],
        "jurisdiction": ["RU", "EU", "US", "NO", "INTL"],
        "term_type": ["acronym", "foreign_term", "standard_code", "avatar", "symbol"],
        "classification_status_code": ["CONFIRMED", "PENDING_REVIEW", "NOT_FOUND", "NOT_USED", "UNASSIGNED"],
        "pending_status": ["new", "mapped", "rejected"],
        "validation_status": ["pending", "valid", "invalid"],
        "chunk_type": ["text", "table", "image", "formula"]
    }}

@app.get("/api/v1/system/health")
async def health():
    return {"status": "ok", "service": "registry-service", "timestamp": utcnow()}

if __name__ == "__main__":
    import os
    port = int(os.getenv("REGISTRY_SERVICE_PORT", "8084"))
    uvicorn.run(app, host="0.0.0.0", port=port)