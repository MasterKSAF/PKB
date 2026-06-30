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

MOCK_PORT = 8099  # Порт mock-gateway (единая точка для всех скриптов)

# ---------------------------------------------------------------------------
# Permission → tab mapping (mirrors auth_service logic)
# ---------------------------------------------------------------------------

_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "engineer":        ["documents:read", "search", "history:read"],
    "knowledge_admin": ["documents:read", "documents:write", "search", "history:read", "audit:read"],
    "system_admin":    ["documents:read", "documents:write", "search", "history:read",
                        "users:manage", "roles:manage", "audit:read"],
}

_PERMISSION_TO_TABS: dict[str, list[str]] = {
    "documents:read": ["chat"],
    "search":         ["search"],
    "history:read":   ["history"],
    "documents:write":["registry", "documents"],
    "users:manage":   ["admin"],
    "roles:manage":   ["admin"],
    "audit:read":     ["monitor"],
}

_TAB_ORDER = ["chat", "search", "history", "registry", "documents", "admin", "monitor"]


def compute_available_tabs(role_names_list: list) -> list:
    perms: set = set()
    for role_name in role_names_list:
        perms.update(_ROLE_PERMISSIONS.get(role_name, []))
    tabs: set = set()
    for perm, tab_list in _PERMISSION_TO_TABS.items():
        if perm in perms:
            tabs.update(tab_list)
    return [t for t in _TAB_ORDER if t in tabs]


def compute_permissions(role_names_list: list) -> dict:
    perms: set = set()
    for role_name in role_names_list:
        perms.update(_ROLE_PERMISSIONS.get(role_name, []))
    return {
        "can_upload_documents":   "documents:write" in perms,
        "can_run_ocr":            False,
        "can_manage_users":       "users:manage" in perms,
        "can_manage_classifiers": "roles:manage" in perms,
        "can_manage_terminology": False,
        "can_manage_registry":    "documents:write" in perms,
    }


T = TypeVar("T")
_id_counter = 10


def new_id(prefix: str = "") -> int:
    """Генерация ID — возрастающий счётчик (старт 10, чтобы не пересекаться со статикой seed-данных)."""
    global _id_counter
    _id_counter += 1
    return _id_counter


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
# DB-1: 6-польная формула title_hash_sha256
# Формула: era|source_type|mks_oks_code||doc_code|title → SHA-256
# ---------------------------------------------------------------------------


def compute_title_hash_sha256(doc: dict) -> str:
    """Вычисляет title_hash_sha256 по 6-польной формуле.

    Поля (разделитель |):
      1. era        — эпоха (USSR, RF, CURRENT, ...)
      2. source_type — тип документа (GOST, RD, ...)
      3. mks_oks_code — код МКС (может быть пустым)
      4. (пустое поле-резерв)
      5. doc_code    — обозначение документа
      6. title       — наименование
    Если doc_code отсутствует — используется пустая строка.
    """
    era = doc.get("era", "") or ""
    source_type = doc.get("source_type", "") or ""
    mks = doc.get("mks_oks_code", "") or ""
    doc_code = doc.get("doc_code", "") or ""
    title = doc.get("title", "") or ""
    formula = f"{era}|{source_type}|{mks}||{doc_code}|{title}"
    return hashlib.sha256(formula.encode("utf-8")).hexdigest().upper()


# ---------------------------------------------------------------------------
# Seed-данные
# ---------------------------------------------------------------------------

SEED_USERS: List[Dict[str, Any]] = [
    {"user_id":1,"email":"ivanov@example.com","full_name":"Иванов Иван Иванович","password":"secret123","position":"Инженер-конструктор","roles":["engineer"],"role":"engineer","role_title":"Инженер","is_active":True,"available_tabs":["chat","search","history"],"permissions":{"can_upload_documents":False,"can_run_ocr":False,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2025-12-01T08:00:00Z"},
    {"user_id":2,"email":"petrova@example.com","full_name":"Петрова Анна Викторовна","password":"secret456","position":"Администратор НСИ","roles":["knowledge_admin"],"role":"knowledge_admin","role_title":"Администратор НСИ","is_active":True,"available_tabs":["chat","search","history","registry","documents","monitor"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":False,"can_manage_classifiers":True,"can_manage_terminology":True,"can_manage_registry":True},"last_login_at":"","created_at":"2025-11-15T10:00:00Z"},
    {"user_id":3,"email":"admin@example.com","full_name":"Сидоров Павел Алексеевич","password":"admin123","position":"Системный администратор","roles":["system_admin"],"role":"system_admin","role_title":"Системный администратор","is_active":True,"available_tabs":["chat","search","history","registry","documents","admin","monitor"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":True,"can_manage_classifiers":True,"can_manage_terminology":True,"can_manage_registry":True},"last_login_at":"","created_at":"2025-10-01T08:00:00Z"},
    {"user_id":4,"email":"kuznetsov@example.com","full_name":"Кузнецов Дмитрий Олегович","password":"secret789","position":"Инженер-технолог","roles":["engineer"],"role":"engineer","role_title":"Инженер","is_active":True,"available_tabs":["chat","search","history"],"permissions":{"can_upload_documents":False,"can_run_ocr":False,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2026-01-10T09:00:00Z"},
    {"user_id":5,"email":"smirnova@example.com","full_name":"Смирнова Елена Игоревна","password":"secret000","position":"Ведущий инженер","roles":["engineer"],"role":"engineer","role_title":"Инженер","is_active":False,"available_tabs":["chat","search","history"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2025-12-20T08:00:00Z"},
]

SEED_ROLES = [
    {"role_id":1,"name":"Инженер","permissions":["documents:read","search"],"created_at":"2025-12-01T08:00:00Z"},
    {"role_id":2,"name":"Администратор НСИ","permissions":["documents:read","documents:write","search","classifiers:manage","terminology:manage","registry:manage"],"created_at":"2025-12-01T08:00:00Z"},
    {"role_id":3,"name":"Системный администратор","permissions":["documents:read","documents:write","documents:delete","search","classifiers:manage","terminology:manage","registry:manage","users:manage","roles:manage","audit:read"],"created_at":"2025-12-01T08:00:00Z"},
]

SEED_AUDIT = [
    {"event_id":1,"user_id":1,"action":"document.upload","resource_type":"document","resource_id":1,"details":{"filename":"spec_ГОСТ_2.109.pdf"},"ip_address":"192.168.1.25","timestamp":"2026-04-27T09:30:00Z"},
    {"event_id":2,"user_id":2,"action":"classifier.update","resource_type":"classifier","resource_id":1,"details":{"code":"47.020","system":"MKS"},"ip_address":"192.168.1.30","timestamp":"2026-05-10T11:00:00Z"},
    {"event_id":3,"user_id":3,"action":"user.create","resource_type":"user","resource_id":5,"details":{"email":"smirnova@example.com"},"ip_address":"192.168.1.10","timestamp":"2026-05-15T14:00:00Z"},
    {"event_id":4,"user_id":2,"action":"terminology.create","resource_type":"terminology","resource_id":3,"details":{"term":"ISO"},"ip_address":"192.168.1.30","timestamp":"2026-06-01T09:15:00Z"},
]

SEED_CLASSIFIERS = [
    {"classifier_system": "MKS", "code": "47", "parent_code": None, "full_name": "Судостроение", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "MKS", "code": "47.020", "parent_code": "47", "full_name": "Конструкция корпуса", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "MKS", "code": "47.020.10", "parent_code": "47.020", "full_name": "Корпусные конструкции и набор корпуса", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "MKS", "code": "47.020.30", "parent_code": "47.020", "full_name": "Судовые системы", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "MKS", "code": "31.240", "parent_code": "31", "full_name": "Электроника", "status": "active", "effective_date": "2020-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "OKSTU", "code": "05.010", "parent_code": "05", "full_name": "Документы конструкторские", "status": "active", "effective_date": "1980-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "OKSTU", "code": "05.020", "parent_code": "05", "full_name": "Документы технологические", "status": "active", "effective_date": "1980-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
    {"classifier_system": "OKSTU", "code": "12.000", "parent_code": "12", "full_name": "Машиностроение", "status": "active", "effective_date": "1980-01-01", "replaced_by": None, "created_at": "2025-11-15T10:30:00Z", "updated_at": "2025-11-15T10:30:00Z"},
]

SEED_TERMINOLOGY = [
    {"id": 1, "raw_term": "ГОСТ", "standard_term": "ГОСТ", "normalized_value": "гост", "term_type": "standard_code", "is_case_sensitive": False, "definition": "Государственный стандарт", "synonyms": ["GOST", "gost"], "related_docs": [], "scope": ["Стандартизация"], "is_blocked": False, "created_at": "2025-12-01T08:00:00Z", "updated_at": "2026-01-15T12:00:00Z"},
    {"id": 2, "raw_term": "DNV", "standard_term": "DNV", "normalized_value": "dnv", "term_type": "acronym", "is_case_sensitive": True, "definition": "Det Norske Veritas", "synonyms": ["DNV GL"], "related_docs": [], "scope": ["Судостроение"], "is_blocked": False, "created_at": "2026-01-20T14:00:00Z", "updated_at": "2026-01-20T14:00:00Z"},
    {"id": 3, "raw_term": "ISO", "standard_term": "ISO", "normalized_value": "iso", "term_type": "standard_code", "is_case_sensitive": True, "definition": "International Organization for Standardization", "synonyms": ["ISO", "ИСО"], "related_docs": [], "scope": ["Стандартизация"], "is_blocked": False, "created_at": "2026-02-10T10:00:00Z", "updated_at": "2026-02-10T10:00:00Z"},
    {"id": 4, "raw_term": "ТУ", "standard_term": "ТУ", "normalized_value": "ту", "term_type": "standard_code", "is_case_sensitive": False, "definition": "Технические условия", "synonyms": ["TU", "техусловия"], "related_docs": [], "scope": ["Стандартизация"], "is_blocked": False, "created_at": "2025-12-15T12:00:00Z", "updated_at": "2026-01-10T14:00:00Z"},
    {"id": 5, "raw_term": "H11/h11", "standard_term": "H11/h11", "normalized_value": "h11/h11", "term_type": "symbol", "is_case_sensitive": True, "definition": "Поле допуска по системе отверстия/вала 11-го квалитета", "synonyms": [], "related_docs": [1], "scope": ["Машиностроение"], "is_blocked": False, "created_at": "2026-03-01T08:00:00Z", "updated_at": "2026-03-01T08:00:00Z"},
]

SEED_REGISTRY_DOCUMENTS = [
    {"id": 1, "title": "Стойки установочные", "doc_code": "20868-81", "source_type": "GOST", "title_hash_sha256": None, "title_key": "USSR|gost|31.240||20868-81|Стойки установочные", "status": "approved", "era": "USSR", "validity_status": "active", "jurisdiction": "RU", "issuing_body": "Госстандарт СССР", "group": "ПО4", "mks_oks_code": "31.240", "mks_name": "Электроника. Монтажные изделия", "okstu_code": None, "okstu_name": None, "classification_status": {"mks": ["31.240"], "okstu": [], "udk": [], "subject_area": ["Электроника", "Монтажные изделия"]}, "successor_doc_id": None, "predecessor_doc_id": None, "total_versions": 2, "chunk_count": 34, "created_by": "system", "updated_by": "ivanov_ai", "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T14:00:00Z", "valid_from": "1981-07-01", "valid_until": "9999-12-31", "current_version_id": 2, "preview_snapshot": None, "draft_id": None},
    {"id": 2, "title": "Правила классификации и постройки морских судов", "doc_code": "РД 31.11.21-96", "source_type": "RD", "title_hash_sha256": None, "title_key": "RF|rd|47.020||РД 31.11.21-96|Правила классификации и постройки морских судов", "status": "approved", "era": "RF", "validity_status": "active", "jurisdiction": "RU", "issuing_body": "Российский морской регистр судоходства", "group": "К4", "mks_oks_code": "47.020", "mks_name": "Конструкция корпуса", "okstu_code": "05.020", "okstu_name": "Документы технологические", "classification_status": {"mks": ["47.020"], "okstu": ["05.020"], "udk": [], "subject_area": ["Судостроение", "Корпусные конструкции"]}, "successor_doc_id": None, "predecessor_doc_id": None, "total_versions": 3, "chunk_count": 128, "created_by": "petrova_ai", "updated_by": "petrova_ai", "created_at": "2026-05-10T08:00:00Z", "updated_at": "2026-06-01T16:00:00Z", "valid_from": "1996-01-01", "valid_until": "9999-12-31", "current_version_id": 3, "preview_snapshot": None, "draft_id": None},
    {"id": 3, "title": "Трубы стальные бесшовные горячедеформированные", "doc_code": "ГОСТ 8732-78", "source_type": "GOST", "title_hash_sha256": None, "title_key": "USSR|gost|47.020.30||ГОСТ 8732-78|Трубы стальные бесшовные горячедеформированные", "status": "draft", "era": "USSR", "validity_status": "active", "jurisdiction": "RU", "issuing_body": "Госстандарт СССР", "group": "М1", "mks_oks_code": "47.020.30", "mks_name": "Судовые системы", "okstu_code": "12.000", "okstu_name": "Машиностроение", "classification_status": {"mks": ["47.020.30"], "okstu": ["12.000"], "udk": [], "subject_area": ["Судовые системы", "Машиностроение"]}, "successor_doc_id": None, "predecessor_doc_id": None, "total_versions": 1, "chunk_count": 56, "created_by": "system", "updated_by": "system", "created_at": "2026-06-10T09:00:00Z", "updated_at": "2026-06-11T11:00:00Z", "valid_from": "1978-01-01", "valid_until": "9999-12-31", "current_version_id": 1, "preview_snapshot": None, "draft_id": None},
]

SEED_CLASSIFIER_PENDING = [
    {"id": 1, "system": "MKS", "code": "47.020.99", "found_in_document_id": 1, "found_in_document_title": "Стойки установочные", "status": "new", "suggested_parent_code": "47.020", "suggested_parent_name": "Конструкция корпуса", "admin_comment": None, "created_at": "2026-05-15T10:01:00Z"}
]

SEED_CATEGORIES = [
    {"id": 1, "name": "Корпусные конструкции", "description": "Документы по корпусу, набору, обшивке, палубам", "color": "#4CAF50", "document_count": 12, "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-06-10T14:00:00Z"},
    {"id": 2, "name": "Электрооборудование", "description": "Схемы, кабели, распределительные устройства", "color": "#2196F3", "document_count": 8, "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-06-10T14:00:00Z"},
    {"id": 3, "name": "Материалы", "description": "Спецификации материалов, сертификаты", "color": "#FF9800", "document_count": 5, "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-06-10T14:00:00Z"},
    {"id": 4, "name": "Сварка", "description": "Документы по сварочным работам, аттестации и контролю", "color": "#9C27B0", "document_count": 3, "created_at": "2026-05-01T10:00:00Z", "updated_at": "2026-06-10T14:00:00Z"},
    {"id": 5, "name": "Контроль качества", "description": "Методы контроля, испытания, дефектоскопия", "color": "#F44336", "document_count": 7, "created_at": "2026-05-01T10:00:00Z", "updated_at": "2026-06-10T14:00:00Z"},
]

SEED_DOCUMENTS = [
    {"document_id": 1, "title": "Спецификация по ГОСТ 2.109", "doc_code": "2.109-73",
     "source_type": "GOST", "era": "CURRENT", "validity_status": "active",
     "jurisdiction": "RU", "issuing_body": "Госстандарт",
     "group": "ПО4",
     "mks_oks_code": "31.240", "okstu_code": None,
     "classification_status": {"mks": ["31.240"], "okstu": [], "udk": [], "subject_area": ["Электроника", "Монтажные изделия"]},
     "successor_doc_id": None, "predecessor_doc_id": None, "chunk_container_id": None,
     "status": "completed", "file_size": 1024000, "pages_total": 12, "pages_processed": 12,
     "pages_failed": 0, "ocr_status": "completed", "index_status": "completed",
     "user_id": 1, "created_by": "Иванов И.И.",
     "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T14:00:00Z",
     "chunk_count": 34, "chunk_validation": None,
     "metadata": {"year": 1981, "udk_code": "629.5.021", "tags": ["судостроение"]},
     "total_versions": 1,
    },
    {"document_id": 2, "title": "Правила классификации морских судов", "doc_code": "РД 31.11.21-96",
     "source_type": "RD", "era": "RF", "validity_status": "active",
     "jurisdiction": "RU", "issuing_body": "Российский морской регистр",
     "group": "К4",
     "mks_oks_code": "47.020", "okstu_code": "05.020",
     "classification_status": {"mks": ["47.020"], "okstu": ["05.020"], "udk": [], "subject_area": ["Судостроение", "Корпусные конструкции"]},
     "successor_doc_id": None, "predecessor_doc_id": None, "chunk_container_id": None,
     "status": "review_required", "file_size": 2048000, "pages_total": 45, "pages_processed": 44,
     "pages_failed": 1, "ocr_status": "completed", "index_status": "pending",
     "user_id": 2, "created_by": "Петрова А.В.",
     "created_at": "2026-05-10T08:00:00Z", "updated_at": "2026-05-12T16:30:00Z",
     "chunk_count": 128, "chunk_validation": None,
     "metadata": {"year": 1996, "udk_code": "629.5.011", "tags": ["классификация", "морские суда"]},
     "total_versions": 2,
    },
    {"document_id": 3, "title": "Трубы стальные бесшовные. Технические условия", "doc_code": "ГОСТ 8732-78",
     "source_type": "GOST", "era": "USSR", "validity_status": "active",
     "jurisdiction": "RU", "issuing_body": "Госстандарт СССР",
     "group": "М1",
     "mks_oks_code": "47.020.30", "okstu_code": "12.000",
     "classification_status": {"mks": ["47.020.30"], "okstu": ["12.000"], "udk": [], "subject_area": ["Судовые системы", "Машиностроение"]},
     "successor_doc_id": None, "predecessor_doc_id": None, "chunk_container_id": None,
     "status": "failed", "file_size": 512000, "pages_total": 8, "pages_processed": 3,
     "pages_failed": 5, "ocr_status": "failed", "index_status": "pending",
     "user_id": 1, "created_by": "Иванов И.И.",
     "created_at": "2026-06-01T09:00:00Z", "updated_at": "2026-06-01T09:15:00Z",
     "chunk_count": 0, "chunk_validation": {"status": "error", "message": "OCR failed on pages 4-8"},
     "metadata": {"year": 1978, "udk_code": "621.774.2", "tags": ["трубы", "сталь"]},
     "total_versions": 1,
    },
]

SEED_DOCUMENT_ERRORS = [
    {"error_id": 1, "document_id": 1, "stage": "ocr", "page": 5,
     "error_code": "LOW_CONFIDENCE", "error_message": "Качество распознавания ниже порога",
     "severity": "warning", "timestamp": "2026-04-27T10:01:00Z"},
    {"error_id": 2, "document_id": 2, "stage": "validation", "page": 44,
     "error_code": "VALIDATION_FAILED", "error_message": "Несоответствие формата поля doc_code",
     "severity": "error", "timestamp": "2026-05-12T16:00:00Z"},
    {"error_id": 3, "document_id": 3, "stage": "ocr", "page": 4,
     "error_code": "OCR_FAILED", "error_message": "Ошибка распознавания: повреждённый PDF",
     "severity": "error", "timestamp": "2026-06-01T09:10:00Z"},
    {"error_id": 4, "document_id": 3, "stage": "ocr", "page": 5,
     "error_code": "OCR_FAILED", "error_message": "Ошибка распознавания: повреждённый PDF",
     "severity": "error", "timestamp": "2026-06-01T09:10:05Z"},
]

SEED_METRICS = {
    "control_metrics": {"ocr_quality": 0.984, "retrieval_quality": 0.91, "answers_with_sources": 0.96, "avg_latency_ms": 1420},
    "answer_metrics": {"useful_rate": 0.84, "rated_answers": 43, "flagged_for_review": 5, "open_questions": 3},
    "logs": [{"time": "12:34:02", "type": "search", "text": "Поиск 'ледовый класс'", "level": "info"}],
}

SEED_SESSIONS = [
    {"session_id": 1, "title": "Тестовая сессия", "user_id": 1, "project_id": 1,
     "document_ids": [1], "options": {},
     "message_count": 2, "messages": [
         {"message_id": 1, "role":"user","content":"Привет","timestamp":"2026-04-27T10:00:00Z","status":"completed"},
         {"message_id": 2, "role":"assistant","status":"completed",
          "content":"Здравствуйте! Чем могу помочь?","sources":[],"model_used":"gpt-4","processing_time_ms":500,
          "timestamp":"2026-04-27T10:00:01Z","feedback":None}
     ], "has_more": False, "last_message_preview": "Здравствуйте!",
     "created_at": "2026-04-27T10:00:00Z", "updated_at": "2026-04-27T10:00:01Z"},
    {"session_id": 2, "title": "Анализ корпусных конструкций", "user_id": 1, "project_id": 2,
     "document_ids": [1, 2], "options": {"model": "gpt-4", "temperature": 0.2},
     "message_count": 4, "messages": [
         {"message_id": 3, "role":"user","content":"Какая толщина стенки корпуса?","timestamp":"2026-05-15T14:00:00Z","status":"completed"},
         {"message_id": 4, "role":"assistant","status":"completed",
          "content":"Согласно спецификации по ГОСТ 2.109, толщина стенки корпуса составляет 5 мм. Материал: Сталь 45.","sources":[{"document_id":1,"page":3,"excerpt":"Толщина стенки корпуса: 5 мм"}],
          "model_used":"gpt-4","processing_time_ms":1200,
          "timestamp":"2026-05-15T14:00:02Z","feedback":None},
         {"message_id": 5, "role":"user","content":"А какие допуски применяются?","timestamp":"2026-05-15T14:01:00Z","status":"completed"},
         {"message_id": 6, "role":"assistant","status":"completed",
          "content":"Предельные отклонения по H11/h11. Рекомендуется проверить допуски на отверстие Ø12H12.","sources":[{"document_id":1,"page":5,"excerpt":"Отверстие Ø12H12"},{"document_id":2,"page":3,"excerpt":"H11/h11"}],
          "model_used":"gpt-4","processing_time_ms":900,
          "timestamp":"2026-05-15T14:01:03Z","feedback":None}
     ], "has_more": False, "last_message_preview": "Предельные отклонения по H11/h11.",
     "created_at": "2026-05-15T14:00:00Z", "updated_at": "2026-05-15T14:01:03Z"},
    {"session_id": 3, "title": "Поиск материалов для сварки", "user_id": 2,
     "document_ids": [3], "options": {},
     "message_count": 1, "messages": [
         {"message_id": 7, "role":"user","content":"Какие требования к сварке корпусных конструкций?","timestamp":"2026-06-10T09:30:00Z","status":"completed"},
     ], "has_more": False, "last_message_preview": "Какие требования к сварке корпусных конструкций?",
     "created_at": "2026-06-10T09:30:00Z", "updated_at": "2026-06-10T09:30:00Z"},
]

SEED_HISTORY = [
    {"history_id": 1, "session_id": 1, "created_at":"2026-04-27T10:00:01Z",
     "user_id": 1, "user_name":"Иванов И.И.","question":"Привет","answer_preview":"Здравствуйте!",
     "status":"completed","source_count":0,"answer_id": 1},
    {"history_id": 2, "session_id": 2, "created_at":"2026-05-15T14:00:02Z",
     "user_id": 1, "user_name":"Иванов И.И.","question":"Какая толщина стенки корпуса?",
     "answer_preview":"Согласно спецификации по ГОСТ 2.109, толщина стенки корпуса составляет 5 мм.",
     "status":"completed","source_count":1,"answer_id": 2},
    {"history_id": 3, "session_id": 2, "created_at":"2026-05-15T14:01:03Z",
     "user_id": 1, "user_name":"Иванов И.И.","question":"А какие допуски применяются?",
     "answer_preview":"Предельные отклонения по H11/h11. Рекомендуется проверить допуски на отверстие Ø12H12.",
     "status":"completed","source_count":2,"answer_id": 3},
    {"history_id": 4, "session_id": 3, "created_at":"2026-06-10T09:30:00Z",
     "user_id": 2, "user_name":"Петрова А.В.","question":"Какие требования к сварке корпусных конструкций?",
     "answer_preview":"",
     "status":"awaiting","source_count":0,"answer_id": None},
]

SEED_PROJECTS = [
    {"project_id": 1, "code": "PRJ-2026-001", "name": "Ледокол 'Арктика'",
     "description": "Проект строительства ледокола нового поколения",
     "status": "active", "created_at": "2026-01-15T08:00:00Z", "updated_at": "2026-06-01T10:00:00Z"},
    {"project_id": 2, "code": "PRJ-2026-002", "name": "Танкер 'Восток'",
     "description": "Разработка документации для танкера усиленного ледового класса",
     "status": "active", "created_at": "2026-02-01T09:00:00Z", "updated_at": "2026-05-20T14:00:00Z"},
    {"project_id": 3, "code": "PRJ-2025-015", "name": "Модернизация СРЗ",
     "description": "Модернизация судоремонтного завода (завершённый проект)",
     "status": "archived", "created_at": "2025-06-01T08:00:00Z", "updated_at": "2026-01-10T12:00:00Z"},
]

SEED_REGISTRY_DRAFTS = [
    {"id": 1, "file_key": "f-upload_001", "document_key": "sha256:abc123",
     "status": "previewing", "confidence": None, "preview_metadata": None,
     "raw_data": None, "error_code": None, "error_message": None,
     "created_by": "system", "updated_by": None, "created_at": "2026-06-11T10:00:00Z",
     "updated_at": "2026-06-11T10:00:00Z", "deleted_at": None},
    {"id": 2, "file_key": "f-upload_002", "document_key": "sha256:def456",
     "status": "ready_for_approve", "confidence": 0.94,
     "preview_metadata": {"doc_code": "ГОСТ 12345-78", "title": "Балки стальные", "year": 1978},
     "raw_data": None, "error_code": None, "error_message": None,
     "created_by": "petrova_ai", "updated_by": "system",
     "created_at": "2026-06-10T14:00:00Z", "updated_at": "2026-06-11T09:00:00Z", "deleted_at": None},
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
_feedback_store: list = []
_export_store: Dict[int, dict] = {}

# Registry
_classifiers: Dict[str, dict] = {}
_terminology: Dict[int, dict] = {}
_registry_docs: Dict[int, dict] = {}
_pending_classifiers: Dict[int, dict] = {}
_registry_drafts: Dict[int, dict] = {}
_doc_history: Dict[int, list] = {}
_categories: Dict[int, dict] = {}


def init_all_data():
    """Инициализация всех seed-данных."""
    global _users, _roles, _audit, _tokens, _tokens_meta, _password_hashes, _rate_limits, _access_token_map
    global _documents, _document_errors, _versions, _chunks, _history, _approvals, _metrics
    global _sessions, _chat_history, _projects
    global _classifiers, _terminology, _registry_docs, _pending_classifiers, _registry_drafts, _doc_history, _categories

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
            # DB-25: revision, source_filename, file_path, updated_at
            _versions[doc_id].append({
                "version_id": new_id(), "version_number": v+1, "document_id": doc_id,
                "title": doc.get("title",""), "file_size": doc.get("file_size",0),
                "revision": f"{v+1}.0",
                "source_filename": f"doc_{doc_id}_v{v+1}.pdf",
                "file_path": f"/storage/documents/{doc_id}/v{v+1}/source.pdf",
                "content_hash_sha256": hashlib.sha256(f"{doc_id}-v{v+1}".encode()).hexdigest(),
                "title_hash_sha256": compute_title_hash_sha256(doc),
                "status": "completed",
                "created_at": doc.get("created_at", utcnow()),
                "updated_at": doc.get("updated_at", utcnow()),
                "created_by": doc.get("created_by","")
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
    _projects = {p["project_id"]: copy.deepcopy(p) for p in SEED_PROJECTS}
    _feedback_store = []
    _export_store = {}

    # Registry
    _classifiers = {c["code"]: copy.deepcopy(c) for c in SEED_CLASSIFIERS}
    _terminology = {t["id"]: copy.deepcopy(t) for t in SEED_TERMINOLOGY}
    _registry_docs = {}
    for d in SEED_REGISTRY_DOCUMENTS:
        doc = copy.deepcopy(d)
        # DB-1: вычисляем title_hash_sha256
        doc["title_hash_sha256"] = compute_title_hash_sha256(doc)
        _registry_docs[d["id"]] = doc
    _pending_classifiers = {p["id"]: copy.deepcopy(p) for p in SEED_CLASSIFIER_PENDING}
    _doc_history = {}
    for d in SEED_REGISTRY_DOCUMENTS:
        _doc_history[d["id"]] = [
            {"history_id": new_id(), "doc_id": d["id"], "previous_status": None,
             "new_status": d.get("status", "draft"), "comment": "Initial state",
             "changed_by": d.get("created_by", "system"), "changed_at": d.get("created_at", utcnow())}
        ]

    _categories = {c["id"]: copy.deepcopy(c) for c in SEED_CATEGORIES}
    _registry_drafts = {d["id"]: copy.deepcopy(d) for d in SEED_REGISTRY_DRAFTS}


init_all_data()
