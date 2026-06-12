"""
Registry handlers — extracted from registry_service/main.py.
All data stores imported from mocks.common.
All paths are relative (prefix /api/v1/registry is applied at mount time in gateway.py).
"""

import copy
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mocks.common import (
    _classifiers, _terminology, _registry_docs,
    _pending_classifiers, _registry_drafts, _doc_history, _categories,
    new_id, utcnow, error_response, paginate_registry,
)

logger = logging.getLogger("registry_service")

router = APIRouter()


# ── Pydantic модели ──────────────────────────────────────────────────────────

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
    successor_doc_id: Optional[int] = None
    predecessor_doc_id: Optional[int] = None


class RegistryDocStatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None
    changed_by: Optional[str] = None


class DraftCreate(BaseModel):
    file_key: str
    document_key: str
    status: str = "uploaded"
    raw_data: Optional[dict] = None
    created_by: Optional[str] = None


class DraftStatusUpdate(BaseModel):
    status: str
    confidence: Optional[float] = None
    preview_metadata: Optional[dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    updated_by: Optional[str] = None


class CheckUniquenessRequest(BaseModel):
    title: str
    doc_code: Optional[str] = None
    era: Optional[str] = None
    source_type: Optional[str] = None
    file_size_bytes: Optional[int] = None


# ── 1. Classifiers ───────────────────────────────────────────────────────────

@router.get("/classifiers")
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


@router.get("/classifiers/tree")
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


@router.post("/classifiers/import")
async def import_classifiers(file: UploadFile = File(...)):
    content = await file.read()
    raw_data = json.loads(content)
    if isinstance(raw_data, dict):
        raw_data = raw_data.get("data") or raw_data.get("classifiers") or []
    rows = [ClassifierCreate(**r) if isinstance(r, dict) else r for r in raw_data]
    inserted = updated = 0
    errors = []
    for row in rows:
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


@router.get("/classifiers/quarantine")
async def list_quarantine(status: str = None, page: int = 1, page_size: int = 50):
    items = list(_pending_classifiers.values())
    if status:
        items = [p for p in items if p.get("status") == status]
    return paginate_registry(items, page, page_size)


@router.post("/classifiers/quarantine/{pending_id}/accept")
async def accept_quarantine(pending_id: int):
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


@router.post("/classifiers/quarantine/{pending_id}/reject")
async def reject_quarantine(pending_id: int):
    pending = _pending_classifiers.get(pending_id)
    if not pending:
        raise HTTPException(404, detail=error_response("CLASSIFIER_NOT_FOUND", "Элемент карантина не найден"))
    pending["status"] = "rejected"
    return {"data": {"id": pending_id, "status": "rejected"}}


@router.get("/classifiers/pending")
async def list_pending(status: str = None, page: int = 1, page_size: int = 50):
    logger.info("list_pending: status=%s page=%d", status, page)
    return await list_quarantine(status, page, page_size)


@router.post("/classifiers/pending/{pending_id}/accept")
async def accept_pending(pending_id: int):
    logger.info("accept_pending: id=%d", pending_id)
    return await accept_quarantine(pending_id)


@router.post("/classifiers/pending/{pending_id}/reject")
async def reject_pending(pending_id: int):
    logger.info("reject_pending: id=%d", pending_id)
    return await reject_quarantine(pending_id)


@router.post("/classifiers/validate")
async def validate_classification(req: dict):
    code = req.get("mks_oks_code", req.get("code"))
    node = _classifiers.get(code) if code else None
    valid = node is not None
    status = "CONFIRMED" if valid else "NOT_FOUND"
    return {"data": {"mks_status": status, "okstu_status": "NOT_USED", "overall_status": "valid" if valid else "pending", "udk_valid": valid}}


@router.get("/classifiers/{code}")
async def get_classifier(code: str):
    node = _classifiers.get(code)
    if not node:
        raise HTTPException(404, detail=error_response("CLASSIFIER_NOT_FOUND", "Узел классификатора не найден"))
    return {"data": node}


@router.post("/classifiers", status_code=201)
async def create_classifier(req: ClassifierCreate):
    if req.code in _classifiers:
        raise HTTPException(409, detail=error_response("DUPLICATE_CODE", "Код уже существует"))
    new_node = {"classifier_system": req.classifier_system, "code": req.code, "parent_code": req.parent_code,
                "full_name": req.full_name, "status": req.status, "effective_date": req.effective_date,
                "replaced_by": None, "created_at": utcnow(), "updated_at": utcnow()}
    _classifiers[req.code] = new_node
    return {"data": new_node}


@router.put("/classifiers/{code}")
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


@router.patch("/classifiers/{code}")
async def patch_classifier(code: str, req: ClassifierUpdate):
    return await update_classifier(code, req)


@router.delete("/classifiers/{code}")
async def delete_classifier(code: str):
    node = _classifiers.get(code)
    if not node:
        raise HTTPException(404, detail=error_response("CLASSIFIER_NOT_FOUND", "Узел не найден"))
    children = sum(1 for c in _classifiers.values() if c.get("parent_code") == code)
    if children > 0:
        raise HTTPException(409, detail=error_response("HAS_CHILDREN", "Есть дочерние узлы"))
    del _classifiers[code]
    return {"data": {"code": code, "deleted": True}}


# ── 2. Terminology ───────────────────────────────────────────────────────────

@router.get("/terminology")
async def list_terms(search: str = None, term_type: str = None, page: int = 1, page_size: int = 50):
    items = list(_terminology.values())
    if search:
        s = search.lower()
        items = [t for t in items if s in t.get("raw_term", "").lower() or s in t.get("standard_term", "").lower()]
    if term_type:
        items = [t for t in items if t.get("term_type") == term_type]
    return paginate_registry(items, page, page_size)


@router.get("/terminology/normalize")
async def normalize_term(term: str = Query(...)):
    q = term.lower()
    for t in _terminology.values():
        if t.get("normalized_value", "").lower() == q or t.get("raw_term", "").lower() == q:
            return {"data": {"raw_term": t["raw_term"], "standard_term": t["standard_term"],
                             "normalized_value": t.get("normalized_value", t["raw_term"]), "term_type": t.get("term_type"), "is_blocked": t.get("is_blocked", False)}}
    return {"data": {"raw_term": term, "standard_term": term.lower(), "normalized_value": term.lower(), "term_type": "preferred", "is_blocked": False}}


@router.post("/terminology/import")
async def import_terms(file: UploadFile = File(...)):
    content = await file.read()
    raw_data = json.loads(content)
    if isinstance(raw_data, dict):
        raw_data = raw_data.get("data") or raw_data.get("terms") or []
    rows = [TermCreate(**r) if isinstance(r, dict) else r for r in raw_data]
    inserted = updated = 0
    errors = []
    for row in rows:
        try:
            existing = next((t for t in _terminology.values() if t.get("raw_term", "").lower() == row.raw_term.lower()), None)
            if existing:
                existing.update({"standard_term": row.standard_term or existing.get("standard_term"),
                                 "normalized_value": row.normalized_value or existing.get("normalized_value"),
                                 "term_type": row.term_type, "is_case_sensitive": row.is_case_sensitive,
                                 "definition": row.definition, "synonyms": row.synonyms or [],
                                 "related_docs": row.related_docs or [], "scope": row.scope,
                                 "is_blocked": row.is_blocked, "updated_at": utcnow()})
                updated += 1
            else:
                tid = new_id()
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


@router.get("/terminology/{term_id}")
async def get_term(term_id: int):
    t = _terminology.get(term_id)
    if not t:
        raise HTTPException(404, detail=error_response("TERM_NOT_FOUND", "Термин не найден"))
    return {"data": t}


@router.post("/terminology", status_code=201)
async def create_term(req: TermCreate):
    tid = new_id()
    new_term = {"id": tid, "raw_term": req.raw_term, "standard_term": req.standard_term or req.raw_term.lower(),
                "normalized_value": req.normalized_value or req.raw_term.lower(), "term_type": req.term_type,
                "is_case_sensitive": req.is_case_sensitive, "definition": req.definition,
                "synonyms": req.synonyms or [], "related_docs": req.related_docs or [], "scope": req.scope,
                "is_blocked": req.is_blocked, "created_at": utcnow(), "updated_at": utcnow()}
    _terminology[tid] = new_term
    return {"data": new_term}


@router.put("/terminology/{term_id}")
async def update_term(term_id: int, req: TermUpdate):
    t = _terminology.get(term_id)
    if not t:
        raise HTTPException(404, detail=error_response("TERM_NOT_FOUND", "Термин не найден"))
    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            t[k] = v
    t["updated_at"] = utcnow()
    return {"data": t}


@router.delete("/terminology/{term_id}")
async def delete_term(term_id: int):
    if term_id not in _terminology:
        raise HTTPException(404, detail=error_response("TERM_NOT_FOUND", "Термин не найден"))
    del _terminology[term_id]
    return {"data": {"id": term_id, "deleted": True}}


# ── 3. Documents (registry) ──────────────────────────────────────────────────

@router.get("/documents")
async def list_registry_docs(search: str = None, status: str = None, source_type: str = None,
                             era: str = None, page: int = 1, page_size: int = 50):
    items = list(_registry_docs.values())
    if search:
        s = search.lower()
        items = [d for d in items if s in d.get("title", "").lower() or s in d.get("doc_code", "").lower()]
    if status:
        items = [d for d in items if d.get("status") == status]
    if source_type:
        items = [d for d in items if d.get("source_type") == source_type]
    if era:
        items = [d for d in items if d.get("era") == era]
    return paginate_registry(items, page, page_size)


@router.get("/documents/export")
async def export_docs(format: str = "json"):
    return {"data": {"format": format, "total": len(_registry_docs), "items": list(_registry_docs.values())}}


@router.post("/documents/import")
async def import_docs(file: UploadFile = File(...)):
    content = await file.read()
    raw_data = json.loads(content)
    if isinstance(raw_data, dict):
        raw_data = raw_data.get("data") or raw_data.get("documents") or []
    rows = [RegistryDocCreate(**r) if isinstance(r, dict) else r for r in raw_data]
    inserted = updated = 0
    errors = []
    for item in rows:
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
                doc_id = new_id()
                new_doc = {"id": doc_id, "title": item.title, "doc_code": item.doc_code, "source_type": item.source_type,
                           "status": item.status, "era": item.era, "validity_status": item.validity_status,
                           "jurisdiction": item.jurisdiction, "issuing_body": item.issuing_body,
                           "mks_oks_code": item.mks_oks_code, "okstu_code": item.okstu_code,
                           "title_hash_sha256": None, "classification_status": {}, "successor_doc_id": None,
                           "predecessor_doc_id": None, "total_versions": 1, "chunk_count": 0,
                           "created_by": "system", "updated_by": "system", "created_at": utcnow(), "updated_at": utcnow()}
                _registry_docs[doc_id] = new_doc
                _doc_history[doc_id] = [{"history_id": new_id(), "doc_id": doc_id, "previous_status": None,
                                         "new_status": item.status, "comment": "Created", "changed_by": "system", "changed_at": utcnow()}]
                inserted += 1
        except Exception as e:
            errors.append({"row": item.title, "message": str(e)})
    return {"data": {"inserted": inserted, "updated": updated, "errors": errors}}


@router.get("/documents/{doc_id}")
async def get_registry_doc(doc_id: int):
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    return {"data": doc}


@router.post("/documents", status_code=201)
async def create_registry_doc(req: RegistryDocCreate):
    doc_id = new_id()
    new_doc = {"id": doc_id, "title": req.title, "doc_code": req.doc_code, "source_type": req.source_type,
               "status": req.status, "era": req.era, "validity_status": req.validity_status,
               "jurisdiction": req.jurisdiction, "issuing_body": req.issuing_body,
               "mks_oks_code": req.mks_oks_code, "okstu_code": req.okstu_code,
               "title_hash_sha256": None, "classification_status": {}, "successor_doc_id": None,
               "predecessor_doc_id": None, "total_versions": 1, "chunk_count": 0,
               "created_by": "system", "updated_by": "system", "created_at": utcnow(), "updated_at": utcnow()}
    _registry_docs[doc_id] = new_doc
    _doc_history[doc_id] = [{"history_id": new_id(), "doc_id": doc_id, "previous_status": None,
                             "new_status": req.status, "comment": "Created", "changed_by": "system", "changed_at": utcnow()}]
    return {"data": new_doc}


@router.put("/documents/{doc_id}")
async def update_registry_doc(doc_id: int, req: RegistryDocUpdate):
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            doc[k] = v
    doc["updated_at"] = utcnow()
    return {"data": doc}


@router.patch("/documents/{doc_id}/status")
async def patch_status(doc_id: int, req: RegistryDocStatusUpdate):
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    prev = doc["status"]
    doc["status"] = req.status
    doc["updated_at"] = utcnow()
    entry = {"history_id": new_id(), "doc_id": doc_id, "previous_status": prev,
             "new_status": req.status, "comment": req.comment or "Updated", "changed_by": req.changed_by or "system",
             "changed_at": utcnow()}
    _doc_history.setdefault(doc_id, []).append(entry)
    return {"data": {"id": doc_id, "status": req.status, "previous_status": prev, "history_id": entry["history_id"], "updated_at": utcnow()}}


@router.get("/documents/{doc_id}/history")
async def doc_history(doc_id: int):
    if doc_id not in _registry_docs:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    history = _doc_history.get(doc_id, [])
    return {"data": history, "meta": {"total": len(history)}}


@router.get("/documents/{doc_id}/succession")
async def doc_succession(doc_id: int):
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
    chain = [
        *[{"id": p["id"], "title": p["title"], "doc_code": p["doc_code"], "era": p.get("era"), "relation": "predecessor", "depth": -(i + 1)} for i, p in enumerate(preds)],
        {"id": doc["id"], "title": doc["title"], "doc_code": doc["doc_code"], "era": doc.get("era"), "relation": "self", "depth": 0},
        *[{"id": s["id"], "title": s["title"], "doc_code": s["doc_code"], "era": s.get("era"), "relation": "successor", "depth": i + 1} for i, s in enumerate(succs)]
    ]
    return {"data": chain, "meta": {"total": len(chain)}}


@router.delete("/documents/{doc_id}")
async def delete_registry_doc(doc_id: int):
    if doc_id not in _registry_docs:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    del _registry_docs[doc_id]
    return {"data": {"id": doc_id, "deleted": True}}


@router.get("/documents/{doc_id}/sections")
async def get_doc_sections(doc_id: int):
    doc = _registry_docs.get(doc_id)
    if not doc:
        raise HTTPException(404, detail=error_response("DOCUMENT_NOT_FOUND", "Документ не найден"))
    return {
        "document": {
            "id": doc.get("id"),
            "doc_code": doc.get("doc_code"),
            "title": doc.get("title"),
            "era": doc.get("era"),
            "validity_status": doc.get("validity_status"),
        },
        "sections": [
            {
                "section_id": "sec-001",
                "document_id": doc_id,
                "parent_id": None,
                "clause": "1",
                "title": None,
                "level": 1,
                "path": "1",
                "page": 1,
                "type": "text",
                "content": {"text": "Mock content", "amendments": []},
            }
        ],
        "terminology": [],
        "references": [],
    }


@router.post("/documents/check-uniqueness")
async def check_uniqueness(req: CheckUniquenessRequest):
    file_hash = hashlib.sha256((str(req.file_size_bytes or "") + req.title).encode()).hexdigest() if req.file_size_bytes else None
    title_hash = hashlib.sha256(req.title.encode()).hexdigest()
    return {
        "data": {
            "is_duplicate": False,
            "is_duplicate_file": False,
            "candidates": [],
            "file_hash_sha256": file_hash,
            "title_hash_sha256": title_hash,
            "file_size_bytes": req.file_size_bytes,
            "checked_at": utcnow(),
        }
    }


# ── 4. Registry Drafts ──────────────────────────────────────────────────────

@router.post("/drafts", status_code=201)
async def create_draft(req: DraftCreate):
    draft_id = new_id()
    now = utcnow()
    draft = {
        "id": draft_id,
        "file_key": req.file_key,
        "document_key": req.document_key,
        "status": req.status,
        "confidence": None,
        "preview_metadata": None,
        "raw_data": req.raw_data,
        "error_code": None,
        "error_message": None,
        "created_by": req.created_by or "system",
        "updated_by": None,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    _registry_drafts[draft_id] = draft
    return {
        "data": {
            "id": draft_id,
            "file_key": req.file_key,
            "document_key": req.document_key,
            "status": req.status,
            "created_at": now,
        }
    }


@router.get("/drafts")
async def list_drafts(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    items = list(_registry_drafts.values())
    if status:
        items = [d for d in items if d.get("status") == status]
    items.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    result = []
    for d in items:
        entry = {
            "id": d["id"],
            "file_key": d["file_key"],
            "document_key": d["document_key"],
            "status": d["status"],
            "confidence": d.get("confidence"),
            "preview_metadata": d.get("preview_metadata"),
            "created_by": d.get("created_by"),
            "created_at": d.get("created_at"),
        }
        result.append(entry)
    return paginate_registry(result, page, page_size)


@router.get("/drafts/{draft_id}")
async def get_draft(draft_id: int):
    draft = _registry_drafts.get(draft_id)
    if not draft:
        raise HTTPException(404, detail=error_response("DRAFT_NOT_FOUND", "Черновик не найден"))
    return {"data": draft}


@router.get("/drafts/{draft_id}/preview")
async def get_draft_preview(draft_id: int):
    draft = _registry_drafts.get(draft_id)
    if not draft:
        raise HTTPException(404, detail=error_response("DRAFT_NOT_FOUND", "Черновик не найден"))
    return {
        "data": {
            "id": draft["id"],
            "file_key": draft["file_key"],
            "status": draft["status"],
            "confidence": draft.get("confidence"),
            "preview_metadata": draft.get("preview_metadata"),
            "created_at": draft.get("created_at"),
        }
    }


@router.patch("/drafts/{draft_id}/status")
async def update_draft_status(draft_id: int, req: DraftStatusUpdate):
    draft = _registry_drafts.get(draft_id)
    if not draft:
        raise HTTPException(404, detail=error_response("DRAFT_NOT_FOUND", "Черновик не найден"))
    previous_status = draft["status"]
    draft["status"] = req.status
    if req.confidence is not None:
        draft["confidence"] = req.confidence
    if req.preview_metadata is not None:
        draft["preview_metadata"] = req.preview_metadata
    if req.error_code is not None:
        draft["error_code"] = req.error_code
    if req.error_message is not None:
        draft["error_message"] = req.error_message
    if req.updated_by is not None:
        draft["updated_by"] = req.updated_by
    draft["updated_at"] = utcnow()
    return {
        "data": {
            "id": draft_id,
            "status": req.status,
            "previous_status": previous_status,
            "updated_at": draft["updated_at"],
        }
    }


@router.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: int):
    if draft_id not in _registry_drafts:
        raise HTTPException(404, detail=error_response("DRAFT_NOT_FOUND", "Черновик не найден"))
    del _registry_drafts[draft_id]
    return {"data": {"id": draft_id, "deleted_at": utcnow()}}


# ── 6. Categories ──

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


@router.get("/categories")
async def list_categories(page: int = 1, page_size: int = 50):
    items = sorted(_categories.values(), key=lambda c: c.get("name", ""))
    return paginate_registry(items, page, page_size)


@router.get("/categories/{category_id}")
async def get_category(category_id: int):
    cat = _categories.get(category_id)
    if not cat:
        raise HTTPException(404, detail=error_response("CATEGORY_NOT_FOUND", "Категория не найдена"))
    return {"data": cat}


@router.post("/categories", status_code=201)
async def create_category(req: CategoryCreate):
    # Check duplicate name
    for cat in _categories.values():
        if cat["name"].lower() == req.name.lower():
            raise HTTPException(409, detail=error_response("DUPLICATE_CATEGORY_NAME", "Категория с таким именем уже существует"))
    cat_id = new_id()
    now = utcnow()
    new_cat = {
        "id": cat_id,
        "name": req.name,
        "description": req.description or "",
        "color": req.color or "#9E9E9E",
        "document_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    _categories[cat_id] = new_cat
    return {"data": new_cat}


@router.put("/categories/{category_id}")
async def update_category(category_id: int, req: CategoryUpdate):
    cat = _categories.get(category_id)
    if not cat:
        raise HTTPException(404, detail=error_response("CATEGORY_NOT_FOUND", "Категория не найдена"))
    # Check duplicate name (exclude self)
    for cid, c in _categories.items():
        if cid != category_id and c["name"].lower() == req.name.lower():
            raise HTTPException(409, detail=error_response("DUPLICATE_CATEGORY_NAME", "Категория с таким именем уже существует"))
    cat["name"] = req.name
    if req.description is not None:
        cat["description"] = req.description
    if req.color is not None:
        cat["color"] = req.color
    cat["updated_at"] = utcnow()
    return {"data": cat}


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    cat = _categories.get(category_id)
    if not cat:
        raise HTTPException(404, detail=error_response("CATEGORY_NOT_FOUND", "Категория не найдена"))
    if cat.get("document_count", 0) > 0:
        raise HTTPException(409, detail=error_response("CATEGORY_HAS_DOCUMENTS", "Нельзя удалить категорию, к которой привязаны документы"))
    del _categories[category_id]
    return {"data": {"id": category_id, "deleted_at": utcnow(), "message": "Категория удалена"}}


# ── 5. Common ────────────────────────────────────────────────────────────────

@router.get("/common/stats")
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


@router.get("/stats")
async def stats_shortcut():
    return await stats()


@router.get("/common/enums")
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


@router.get("/enums")
async def enums_shortcut():
    return await enums()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "registry-service", "version": "1.0.0", "uptime_seconds": 86400}
