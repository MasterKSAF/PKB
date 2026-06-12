"""
Общие модели данных, утилиты, in-memory хранилища и seed-данные
для mock-сервисов PKB Neuroassistant.

Всё в одном месте — никакого разделения на сервисы.
"""

import copy
import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TypeVar

# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

T = TypeVar("T")
_counter = 0


def new_id(prefix: str = "") -> str:
    """Генерация уникального ID (int для bigint, str с префиксом если нужно)."""
    global _counter
    _counter += 1
    return _counter


def new_str_id(prefix: str = "") -> str:
    import uuid
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}{uid}" if prefix else uid


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def paginate(items: list, page: int = 1, page_size: int = 50) -> dict:
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


def paginate_registry(items: list, page: int = 1, page_size: int = 50) -> dict:
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": items[start:end],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


def error_response(code: str, message: str, details: Optional[dict] = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


# ---------------------------------------------------------------------------
# Seed-данные
# ---------------------------------------------------------------------------

SEED_USERS: List[Dict[str, Any]] = [
    {"user_id":1,"email":"ivanov@example.com","full_name":"Иванов Иван Иванович","password":"secret123","position":"Инженер-конструктор","roles":["engineer"],"role":"engineer","role_title":"Инженер","is_active":True,"available_tabs":["chat","search","checks","history"],"permissions":{"can_upload_documents":False,"can_run_ocr":False,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2025-12-01T08:00:00Z"},
    {"user_id":2,"email":"petrova@example.com","full_name":"Петрова Анна Викторовна","password":"secret456","position":"Администратор НСИ","roles":["knowledge_admin"],"role":"knowledge_admin","role_title":"Администратор НСИ","is_active":True,"available_tabs":["chat","search","checks","history","registry","documents"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":False,"can_manage_classifiers":True,"can_manage_terminology":True,"can_manage_registry":True},"last_login_at":"","created_at":"2025-11-15T10:00:00Z"},
    {"user_id":3,"email":"admin@example.com","full_name":"Сидоров Павел Алексеевич","password":"admin123","position":"Системный администратор","roles":["system_admin"],"role":"system_admin","role_title":"Системный администратор","is_active":True,"available_tabs":["chat","search","checks","history","registry","documents","admin","monitor"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":True,"can_manage_classifiers":True,"can_manage_terminology":True,"can_manage_registry":True},"last_login_at":"","created_at":"2025-10-01T08:00:00Z"},
    {"user_id":4,"email":"kuznetsov@example.com","full_name":"Кузнецов Дмитрий Олегович","password":"secret789","position":"Инженер-технолог","roles":["engineer"],"role":"engineer","role_title":"Инженер","is_active":True,"available_tabs":["chat","search","checks","history"],"permissions":{"can_upload_documents":False,"can_run_ocr":False,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2026-01-10T09:00:00Z"},
    {"user_id":5,"email":"smirnova@example.com","full_name":"Смирнова Елена Игоревна","password":"secret000","position":"Ведущий инженер","roles":["engineer"],"role":"engineer","role_title":"Инженер","is_active":False,"available_tabs":["chat","search","checks","history"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2025-12-20T08:00:00Z"},
]

SEED_ROLES = [
    {"role_id":1,"name":"Инженер","permissions":["documents:read","search"],"created_at":"2025-12-01T08:00:00Z"},
    {"role_id":2,"name":"Администратор НСИ","permissions":["documents:read","documents:write","search","classifiers:manage","terminology:manage","registry:manage"],"created_at":"2025-12-01T08:00:00Z"},
    {"role_id":3,"name":"Системный администратор","permissions":["documents:read","documents:write","documents:delete","search","classifiers:manage","terminology:manage","registry:manage","users:manage","roles:manage","audit:read"],"created_at":"2025-12-01T08:00:00Z"},
]

SEED_AUDIT = [
    {"event_id":1,"user_id":1,"action":"document.upload","resource_type":"document","resource_id":1,"details":{"filename":"spec_ГОСТ_2.109.pdf"},"ip_address":"192.168.1.25","timestamp":"2026-04-27T09:30:00Z"},
]

SEED_CLASSIFIERS = [
    {"classifier_system": "MKS", "code": "47", "parent_code": None, "full_name": "Судостроение", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "MKS", "code": "47.020", "parent_code": "47", "full_name": "Конструкция корпуса", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "OKSTU", "code": "05.010", "parent_code": "05", "full_name": "Документы конструкторские", "status": "active", "effective_date": "1980-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
]

SEED_TERMINOLOGY = [
    {"id": 1, "raw_term": "ГОСТ", "standard_term": "ГОСТ", "normalized_value": "гост", "term_type": "standard_code", "is_case_sensitive": False, "definition": "Государственный стандарт", "synonyms": ["GOST", "gost"], "related_docs": [], "scope": "Стандартизация", "is_blocked": False, "created_at": "2025-12-01T08:00:00Z", "updated_at": "2026-01-15T12:00:00Z"},
    {"id": 2, "raw_term": "DNV", "standard_term": "DNV", "normalized_value": "dnv", "term_type": "acronym", "is_case_sensitive": True, "definition": "Det Norske Veritas", "synonyms": ["DNV GL"], "related_docs": [], "scope": "Судостроение", "is_blocked": False, "created_at": "2026-01-20T14:00:00Z", "updated_at": "2026-01-20T14:00:00Z"},
]

SEED_REGISTRY_DOCUMENTS = [
    {"id": 1, "title": "Стойки установочные", "doc_code": "20868-81", "source_type": "GOST", "title_hash_sha256": None, "status": "approved", "era": "USSR", "validity_status": "active", "jurisdiction": "RU", "issuing_body": "Госстандарт СССР", "mks_oks_code": "31.240", "mks_name": "Электроника", "okstu_code": None, "okstu_name": None, "classification_status": {"mks_status": "CONFIRMED", "okstu_status": "NOT_USED"}, "successor_doc_id": None, "predecessor_doc_id": None, "total_versions": 2, "chunk_count": 34, "created_by": "system", "updated_by": "ivanov_ai", "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T14:00:00Z"}
]

SEED_CLASSIFIER_PENDING = [
    {"id": 1, "system": "MKS", "code": "47.020.99", "found_in_document_id": 1, "found_in_document_title": "Стойки установочные", "status": "new", "suggested_parent_code": "47.020", "suggested_parent_name": "Конструкция корпуса", "admin_comment": None, "created_at": "2026-05-15T10:01:00Z"}
]

SEED_DOCUMENTS = [
    {"document_id": 1, "title": "Спецификация по ГОСТ 2.109", "doc_code": "2.109-73",
     "source_type": "GOST", "era": "CURRENT", "validity_status": "active",
     "jurisdiction": "RU", "issuing_body": "Госстандарт",
     "mks_oks_code": "01.100", "okstu_code": None,
     "classification_status": {"mks_status": "CONFIRMED", "okstu_status": "NOT_USED"},
     "successor_doc_id": None, "predecessor_doc_id": None, "chunk_container_id": None,
     "status": "completed", "file_size": 1024000, "pages_total": 12, "pages_processed": 12,
     "pages_failed": 0, "ocr_status": "completed", "index_status": "completed",
     "user_id": 1, "uploaded_by": "Иванов И.И.",
     "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T14:00:00Z",
     "chunk_count": 34, "chunk_validation": None,
     "metadata": {"year": 1981, "udc": "629.5.021", "tags": ["судостроение"]},
     "total_versions": 1,
    }
]

SEED_DOCUMENT_ERRORS = [
    {"error_id": 1, "document_id": 1, "stage": "ocr", "page": 5,
     "error_code": "LOW_CONFIDENCE", "error_message": "Качество распознавания ниже порога",
     "severity": "warning", "timestamp": "2026-04-27T10:01:00Z"}
]

SEED_METRICS = {
    "control_metrics": {"ocr_quality": 0.984, "retrieval_quality": 0.91, "answers_with_sources": 0.96, "avg_latency_ms": 1420},
    "answer_metrics": {"useful_rate": 0.84, "rated_answers": 43, "flagged_for_review": 5, "open_questions": 3},
    "logs": [{"time": "12:34:02", "type": "search", "text": "Поиск 'ледовый класс'", "level": "info"}],
}

SEED_SESSIONS = [
    {"session_id": 1, "title": "Тестовая сессия", "user_id": 1,
     "document_ids": [1], "options": {},
     "message_count": 2, "messages": [
         {"message_id": 1, "role":"user","content":"Привет","timestamp":"2026-04-27T10:00:00Z","status":"completed"},
         {"message_id": 2, "role":"assistant","status":"completed",
          "content":"Здравствуйте! Чем могу помочь?","sources":[],"model_used":"gpt-4","processing_time_ms":500,
          "timestamp":"2026-04-27T10:00:01Z","feedback":None}
     ], "has_more": False, "last_message_preview": "Здравствуйте!",
     "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T10:00:01Z"}
]

SEED_HISTORY = [
    {"history_id": 1, "session_id": 1, "created_at":"2026-04-27T10:00:01Z",
     "user_id": 1, "user_name":"Иванов И.И.","question":"Привет","answer_preview":"Здравствуйте!",
     "status":"completed","source_count":0,"answer_id": 1}
]

# ---------------------------------------------------------------------------
# In-memory хранилища (все в одном namespace, никакого разделения)
# ---------------------------------------------------------------------------

# Auth
_users: Dict[int, dict] = {}
_roles: Dict[int, dict] = {}
_audit: list = []
_tokens: Dict[str, int] = {}
_tokens_meta: Dict[str, dict] = {}
_access_token_map: Dict[str, int] = {}
_blacklist: Dict[str, str] = {}
_password_hashes: Dict[int, str] = {}
_rate_limits: Dict[str, dict] = {}

# Orchestrator / Documents
_documents: Dict[int, dict] = {}
_document_errors: list = []
_versions: Dict[int, list] = {}
_chunks: Dict[int, list] = {}
_history: Dict[int, list] = {}
_approvals: Dict[int, dict] = {}
_metrics: dict = {}
_drafts: Dict[int, dict] = {}
_tasks: Dict[int, dict] = {}

# Query
_sessions: Dict[int, dict] = {}
_chat_history: list = []
_projects: Dict[int, dict] = {}
_projects_id_seq: int = 0
_feedback_store: list = []
_export_store: Dict[int, dict] = {}

# Registry
_classifiers: Dict[str, dict] = {}
_terminology: Dict[int, dict] = {}
_registry_docs: Dict[int, dict] = {}
_pending_classifiers: Dict[int, dict] = {}
_registry_drafts: Dict[int, dict] = {}
_doc_history: Dict[int, list] = {}


def init_all_data():
    """Инициализация всех seed-данных."""
    global _users, _roles, _audit, _tokens, _tokens_meta, _password_hashes, _rate_limits, _access_token_map
    global _documents, _document_errors, _versions, _chunks, _history, _approvals, _metrics
    global _sessions, _chat_history
    global _classifiers, _terminology, _registry_docs, _pending_classifiers, _doc_history

    # Auth
    _users = {u["user_id"]: copy.deepcopy(u) for u in SEED_USERS}
    _roles = {r["role_id"]: copy.deepcopy(r) for r in SEED_ROLES}
    _audit = copy.deepcopy(SEED_AUDIT)
    _rate_limits = {}
    _access_token_map = {}
    for u in SEED_USERS:
        _password_hashes[u["user_id"]] = hashlib.sha256(u["password"].encode()).hexdigest()
    now = utcnow()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    for uid in _users:
        rt = f"rt-mock-{uid}"
        _tokens[rt] = uid
        _tokens_meta[rt] = {"user_id": uid, "expires_at": expires_at, "created_at": now}

    # Orchestrator
    _documents = {d["document_id"]: copy.deepcopy(d) for d in SEED_DOCUMENTS}
    _document_errors = copy.deepcopy(SEED_DOCUMENT_ERRORS)
    _metrics = copy.deepcopy(SEED_METRICS)
    for doc_id, doc in _documents.items():
        ver = doc.get("total_versions", 1)
        _versions[doc_id] = []
        for v in range(ver):
            _versions[doc_id].append({
                "version_id": new_id(), "version_number": v+1, "document_id": doc_id,
                "title": doc.get("title",""), "file_size": doc.get("file_size",0),
                "content_hash_sha256": hashlib.sha256(f"{doc_id}-v{v+1}".encode()).hexdigest(),
                "title_hash_sha256": hashlib.sha256(doc.get("title","").encode()).hexdigest(),
                "status": "completed", "created_at": doc.get("created_at", utcnow()),
                "uploaded_by": doc.get("uploaded_by","")
            })
        _versions[doc_id].reverse()
        _history[doc_id] = [
            {"event_id": new_id(), "document_id": doc_id, "from_status": None,
             "to_status": doc.get("status","uploaded"), "timestamp": doc.get("created_at", utcnow()),
             "user_id": doc.get("user_id", 1), "comment": "Документ создан"},
            {"event_id": new_id(), "document_id": doc_id, "from_status": "uploaded",
             "to_status": doc.get("status","completed"), "timestamp": doc.get("updated_at", utcnow()),
             "user_id": doc.get("user_id", 1), "comment": "Обработка завершена"}
        ]
        cnt = doc.get("chunk_count", 0)
        _chunks[doc_id] = [
            {"chunk_id": new_id(), "chunk_number": i+1, "document_id": doc_id,
             "content": f"Фрагмент {i+1} документа {doc.get('title','')}",
             "page": (i % max(doc.get("pages_total",1),1)) + 1,
             "score": round(random.uniform(0.7, 0.99), 2),
             "is_indexed": doc.get("status") == "completed",
             "created_at": doc.get("created_at", utcnow())}
            for i in range(cnt)
        ]

    # Query
    _sessions = {s["session_id"]: copy.deepcopy(s) for s in SEED_SESSIONS}
    _chat_history = copy.deepcopy(SEED_HISTORY)

    # Registry
    _classifiers = {c["code"]: copy.deepcopy(c) for c in SEED_CLASSIFIERS}
    _terminology = {t["id"]: copy.deepcopy(t) for t in SEED_TERMINOLOGY}
    _registry_docs = {d["id"]: copy.deepcopy(d) for d in SEED_REGISTRY_DOCUMENTS}
    _pending_classifiers = {p["id"]: copy.deepcopy(p) for p in SEED_CLASSIFIER_PENDING}
    _doc_history = {}
    for d in SEED_REGISTRY_DOCUMENTS:
        _doc_history[d["id"]] = [
            {"history_id": new_id(), "doc_id": d["id"], "previous_status": None,
             "new_status": d.get("status", "draft"), "comment": "Initial state",
             "changed_by": d.get("created_by", "system"), "changed_at": d.get("created_at", utcnow())}
        ]


init_all_data()
