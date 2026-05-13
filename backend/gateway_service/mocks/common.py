"""
Общие модели данных, утилиты и in-memory хранилища
для mock-сервисов PKB Neuroassistant.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar

# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

T = TypeVar("T")


def new_id(prefix: str = "") -> str:
    """Генерация уникального ID."""
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}{uid}" if prefix else uid


def utcnow() -> str:
    """Текущее время в ISO 8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def paginate(
    items: list,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Обёртка пагинации."""
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
    """Пагинация для Registry Service (wrapped-формат)."""
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
# In-memory хранилища (синглтоны)
# ---------------------------------------------------------------------------


class InMemoryStore(dict):
    """Dict-подобное хранилище с автогенерацией ID."""

    pass


# ---------------------------------------------------------------------------
# Seed-данные для Auth Service
# ---------------------------------------------------------------------------

SEED_USERS: List[Dict[str, Any]] = [
    {
        "user_id": "u-001",
        "email": "ivanov@example.com",
        "full_name": "Иванов Сергей Петрович",
        "position": "Инженер-конструктор",
        "password": "secret123",
        "roles": ["engineer"],
        "role": "engineer",
        "role_title": "Инженер",
        "is_active": True,
        "available_tabs": ["chat", "search", "checks", "history"],
        "permissions": {
            "can_upload_documents": False,
            "can_run_ocr": False,
            "can_manage_users": False,
            "can_manage_classifiers": False,
            "can_manage_terminology": False,
            "can_manage_registry": False,
        },
        "last_login_at": "2026-05-01T08:20:00Z",
        "created_at": "2025-12-01T08:00:00Z",
        "updated_at": "2026-04-27T10:00:00Z",
    },
    {
        "user_id": "u-002",
        "email": "petrova@example.com",
        "full_name": "Петрова Анна Викторовна",
        "position": "Администратор НСИ",
        "password": "secret456",
        "roles": ["knowledge_admin"],
        "role": "knowledge_admin",
        "role_title": "Администратор НСИ",
        "is_active": True,
        "available_tabs": [
            "chat",
            "search",
            "checks",
            "history",
            "registry",
            "documents",
        ],
        "permissions": {
            "can_upload_documents": True,
            "can_run_ocr": True,
            "can_manage_users": False,
            "can_manage_classifiers": True,
            "can_manage_terminology": True,
            "can_manage_registry": True,
        },
        "last_login_at": "2026-05-01T09:15:00Z",
        "created_at": "2025-11-15T10:00:00Z",
        "updated_at": "2026-03-20T12:00:00Z",
    },
    {
        "user_id": "u-003",
        "email": "admin@example.com",
        "full_name": "Сидоров Павел Алексеевич",
        "position": "Системный администратор",
        "password": "admin123",
        "roles": ["system_admin"],
        "role": "system_admin",
        "role_title": "Системный администратор",
        "is_active": True,
        "available_tabs": [
            "chat",
            "search",
            "checks",
            "history",
            "registry",
            "documents",
            "admin",
            "monitor",
        ],
        "permissions": {
            "can_upload_documents": True,
            "can_run_ocr": True,
            "can_manage_users": True,
            "can_manage_classifiers": True,
            "can_manage_terminology": True,
            "can_manage_registry": True,
        },
        "last_login_at": "2026-05-01T10:00:00Z",
        "created_at": "2025-10-01T08:00:00Z",
        "updated_at": "2026-04-30T16:00:00Z",
    },
    {
        "user_id": "u-004",
        "email": "kuznetsov@example.com",
        "full_name": "Кузнецов Дмитрий Олегович",
        "position": "Инженер-технолог",
        "password": "secret789",
        "roles": ["engineer"],
        "role": "engineer",
        "role_title": "Инженер",
        "is_active": True,
        "available_tabs": ["chat", "search", "checks", "history"],
        "permissions": {
            "can_upload_documents": False,
            "can_run_ocr": False,
            "can_manage_users": False,
            "can_manage_classifiers": False,
            "can_manage_terminology": False,
            "can_manage_registry": False,
        },
        "last_login_at": "2026-04-30T14:00:00Z",
        "created_at": "2026-01-10T09:00:00Z",
        "updated_at": "2026-01-10T09:00:00Z",
    },
    {
        "user_id": "u-005",
        "email": "smirnova@example.com",
        "full_name": "Смирнова Елена Игоревна",
        "position": "Ведущий инженер",
        "password": "secret000",
        "roles": ["engineer"],
        "role": "engineer",
        "role_title": "Инженер",
        "is_active": False,
        "available_tabs": ["chat", "search", "checks", "history"],
        "permissions": {
            "can_upload_documents": True,
            "can_run_ocr": True,
            "can_manage_users": False,
            "can_manage_classifiers": False,
            "can_manage_terminology": False,
            "can_manage_registry": False,
        },
        "last_login_at": "2026-03-15T11:30:00Z",
        "created_at": "2025-12-20T08:00:00Z",
        "updated_at": "2026-03-15T11:30:00Z",
    },
]

SEED_ROLES: List[Dict[str, Any]] = [
    {
        "role_id": "r-engineer",
        "name": "Инженер",
        "permissions": ["documents:read", "search", "chat:basic", "validate:compare"],
        "created_at": "2025-12-01T08:00:00Z",
    },
    {
        "role_id": "r-knowledge-admin",
        "name": "Администратор НСИ",
        "permissions": [
            "documents:read",
            "documents:write",
            "search",
            "chat:basic",
            "validate:compare",
            "validate:checks",
            "classifiers:manage",
            "terminology:manage",
            "registry:manage",
            "monitor:metrics",
        ],
        "created_at": "2025-12-01T08:00:00Z",
    },
    {
        "role_id": "r-system-admin",
        "name": "Системный администратор",
        "permissions": [
            "documents:read",
            "documents:write",
            "documents:delete",
            "search",
            "chat:basic",
            "validate:compare",
            "validate:checks",
            "classifiers:manage",
            "terminology:manage",
            "registry:manage",
            "users:manage",
            "roles:manage",
            "audit:read",
            "monitor:metrics",
            "monitor:logs",
        ],
        "created_at": "2025-12-01T08:00:00Z",
    },
]

SEED_AUDIT: List[Dict[str, Any]] = [
    {
        "event_id": "evt-001",
        "user_id": "u-001",
        "action": "document.upload",
        "resource_type": "document",
        "resource_id": "doc-001",
        "details": {"filename": "spec_ГОСТ_2.109.pdf", "size": 2048576},
        "ip_address": "192.168.1.25",
        "timestamp": "2026-04-27T09:30:00Z",
    },
    {
        "event_id": "evt-002",
        "user_id": "u-002",
        "action": "role.change",
        "resource_type": "user",
        "resource_id": "u-004",
        "details": {"from_role": "engineer", "to_role": "knowledge_admin"},
        "ip_address": "192.168.1.30",
        "timestamp": "2026-04-27T10:00:00Z",
    },
    {
        "event_id": "evt-003",
        "user_id": "u-003",
        "action": "user.create",
        "resource_type": "user",
        "resource_id": "u-005",
        "details": {"email": "smirnova@example.com"},
        "ip_address": "192.168.1.10",
        "timestamp": "2026-04-26T14:00:00Z",
    },
    {
        "event_id": "evt-004",
        "user_id": "u-003",
        "action": "document.delete",
        "resource_type": "document",
        "resource_id": "doc-003",
        "details": {"document_title": "Чертеж_детали_101.pdf"},
        "ip_address": "192.168.1.10",
        "timestamp": "2026-04-25T11:00:00Z",
    },
    {
        "event_id": "evt-005",
        "user_id": "u-001",
        "action": "search",
        "resource_type": "search",
        "resource_id": "",
        "details": {"query": "ГОСТ 2.109 толщина стенки", "results_count": 12},
        "ip_address": "192.168.1.25",
        "timestamp": "2026-04-27T12:00:00Z",
    },
]

# ---------------------------------------------------------------------------
# Seed-данные для Registry Service
# ---------------------------------------------------------------------------

SEED_CLASSIFIERS: List[Dict[str, Any]] = [
    {
        "code": "01",
        "parent_code": None,
        "full_name": "Общие положения и стандарты",
        "doc_type": "normative",
        "jurisdiction": "GOST",
        "language": "ru",
        "oks_code": "01.040.01",
        "is_thematic": False,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        "code": "01.010",
        "parent_code": "01",
        "full_name": "Стандарты оформления документации",
        "doc_type": "normative",
        "jurisdiction": "GOST",
        "language": "ru",
        "oks_code": "01.040.01",
        "is_thematic": False,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        "code": "01.010.001",
        "parent_code": "01.010",
        "full_name": "ГОСТ 2.109-73 — Основные требования к чертежам",
        "doc_type": "normative",
        "jurisdiction": "GOST",
        "language": "ru",
        "oks_code": "01.100.01",
        "is_thematic": False,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        "code": "02",
        "parent_code": None,
        "full_name": "Конструкторская документация",
        "doc_type": "normative",
        "jurisdiction": "GOST",
        "language": "ru",
        "oks_code": "01.110",
        "is_thematic": False,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        "code": "02.001",
        "parent_code": "02",
        "full_name": "ЕСКД. Общие правила выполнения чертежей",
        "doc_type": "normative",
        "jurisdiction": "GOST",
        "language": "ru",
        "oks_code": "01.110",
        "is_thematic": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        "code": "03",
        "parent_code": None,
        "full_name": "Отраслевые стандарты (ОСТ)",
        "doc_type": "normative",
        "jurisdiction": "OST",
        "language": "ru",
        "oks_code": "01.040.25",
        "is_thematic": False,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    },
]

SEED_TERMINOLOGY: List[Dict[str, Any]] = [
    {
        "term_id": "t-001",
        "term": "Толщина стенки",
        "normalized_term": "толщина стенки",
        "context": "ГОСТ 2.109-73, раздел 3",
        "source": "ГОСТ 2.109-73",
        "created_at": "2025-06-01T00:00:00Z",
    },
    {
        "term_id": "t-002",
        "term": "Номинальный размер",
        "normalized_term": "номинальный размер",
        "context": "ГОСТ 2.307-2011",
        "source": "ГОСТ 2.307-2011",
        "created_at": "2025-06-01T00:00:00Z",
    },
    {
        "term_id": "t-003",
        "term": "Предельное отклонение",
        "normalized_term": "предельное отклонение",
        "context": "ГОСТ 2.307-2011, п. 4.2",
        "source": "ГОСТ 2.307-2011",
        "created_at": "2025-06-01T00:00:00Z",
    },
    {
        "term_id": "t-004",
        "term": "Шероховатость поверхности",
        "normalized_term": "шероховатость поверхности",
        "context": "ГОСТ 2.309-73",
        "source": "ГОСТ 2.309-73",
        "created_at": "2025-06-01T00:00:00Z",
    },
    {
        "term_id": "t-005",
        "term": "Допуск формы",
        "normalized_term": "допуск формы",
        "context": "ГОСТ 2.308-2011",
        "source": "ГОСТ 2.308-2011",
        "created_at": "2025-07-01T00:00:00Z",
    },
    {
        "term_id": "t-006",
        "term": "Основная надпись",
        "normalized_term": "основная надпись",
        "context": "ГОСТ 2.104-2006",
        "source": "ГОСТ 2.104-2006",
        "created_at": "2025-07-01T00:00:00Z",
    },
]

SEED_REGISTRY_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "doc_id": "rd-001",
        "title": "ГОСТ 2.109-73 — Основные требования к чертежам",
        "doc_number": "ГОСТ 2.109-73",
        "classifier_code": "01.010.001",
        "classifier_name": "ГОСТ 2.109-73 — Основные требования к чертежам",
        "status": "active",
        "source": "Фонд НСИ",
        "notes": "Действующий стандарт",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-06-01T00:00:00Z",
    },
    {
        "doc_id": "rd-002",
        "title": "ГОСТ 2.307-2011 — Нанесение размеров и предельных отклонений",
        "doc_number": "ГОСТ 2.307-2011",
        "classifier_code": "02.001",
        "classifier_name": "ЕСКД. Общие правила выполнения чертежей",
        "status": "active",
        "source": "Фонд НСИ",
        "notes": "Взамен ГОСТ 2.307-68",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-06-01T00:00:00Z",
    },
    {
        "doc_id": "rd-003",
        "title": "ОСТ 1.00000-80 — Общие требования",
        "doc_number": "ОСТ 1.00000-80",
        "classifier_code": "03",
        "classifier_name": "Отраслевые стандарты (ОСТ)",
        "status": "active",
        "source": "Отраслевой архив",
        "notes": "",
        "created_at": "2025-02-01T00:00:00Z",
        "updated_at": "2025-02-01T00:00:00Z",
    },
    {
        "doc_id": "rd-004",
        "title": "ГОСТ 2.104-2006 — Основные надписи",
        "doc_number": "ГОСТ 2.104-2006",
        "classifier_code": "01.010",
        "classifier_name": "Стандарты оформления документации",
        "status": "active",
        "source": "Фонд НСИ",
        "notes": "",
        "created_at": "2025-03-01T00:00:00Z",
        "updated_at": "2025-03-01T00:00:00Z",
    },
    {
        "doc_id": "rd-005",
        "title": "ГОСТ 2.309-73 — Обозначения шероховатости поверхностей",
        "doc_number": "ГОСТ 2.309-73",
        "classifier_code": "02.001",
        "classifier_name": "ЕСКД. Общие правила выполнения чертежей",
        "status": "draft",
        "source": "Фонд НСИ",
        "notes": "Планируется обновление",
        "created_at": "2025-04-01T00:00:00Z",
        "updated_at": "2025-04-01T00:00:00Z",
    },
]

# ---------------------------------------------------------------------------
# Seed-данные для Orchestrator Service
# ---------------------------------------------------------------------------

SEED_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "document_id": "doc-001",
        "filename": "spec_ГОСТ_2.109.pdf",
        "title": "Спецификация по ГОСТ 2.109",
        "document_type": "specification",
        "source": "upload",
        "version": 1,
        "status": "completed",
        "file_size": 2048576,
        "pages_total": 15,
        "pages_processed": 15,
        "pages_failed": 0,
        "ocr_status": "completed",
        "index_status": "completed",
        "user_id": "u-001",
        "uploaded_by": "Иванов С.П.",
        "metadata": {
            "project": "ПКБ-101",
            "author": "Иванов С.П.",
            "registry_doc_id": "rd-001",
        },
        "pages": [
            {
                "page": 1,
                "width": 2480,
                "height": 3508,
                "ocr_status": "completed",
                "confidence": 0.95,
                "has_text_layer": True,
            },
            {
                "page": 2,
                "width": 2480,
                "height": 3508,
                "ocr_status": "completed",
                "confidence": 0.92,
                "has_text_layer": True,
            },
            {
                "page": 3,
                "width": 2480,
                "height": 3508,
                "ocr_status": "completed",
                "confidence": 0.88,
                "has_text_layer": True,
            },
        ],
        "parameters": {
            "designation": "ПКБ.101.001.СБ",
            "title": "Спецификация сборочная",
            "materials": ["Сталь 45", "Алюминий Д16Т"],
            "dimensions": "500x300x200",
            "references": ["ГОСТ 2.109-73", "ГОСТ 2.307-2011"],
            "specification_items": [
                {
                    "position": 1,
                    "name": "Корпус",
                    "quantity": 1,
                    "dimensions": "300x200x150",
                    "weight": 2.5,
                    "material": "Сталь 45",
                    "note": "",
                },
                {
                    "position": 2,
                    "name": "Крышка",
                    "quantity": 1,
                    "dimensions": "300x200x20",
                    "weight": 0.8,
                    "material": "Алюминий Д16Т",
                    "note": "",
                },
                {
                    "position": 3,
                    "name": "Болт М8x30",
                    "quantity": 8,
                    "dimensions": "М8x30",
                    "weight": 0.02,
                    "material": "Сталь 40Х",
                    "note": "ГОСТ 7798-70",
                },
            ],
        },
        "extraction_confidence": 0.87,
        "unconfirmed_fields": ["materials", "note"],
        "created_at": "2026-04-27T09:30:00Z",
        "updated_at": "2026-04-27T10:30:00Z",
    },
    {
        "document_id": "doc-002",
        "filename": "Чертеж_детали_101.pdf",
        "title": "Чертеж детали 101",
        "document_type": "drawing",
        "source": "upload",
        "version": 2,
        "status": "completed",
        "file_size": 1523000,
        "pages_total": 1,
        "pages_processed": 1,
        "pages_failed": 0,
        "ocr_status": "completed",
        "index_status": "completed",
        "user_id": "u-001",
        "uploaded_by": "Иванов С.П.",
        "metadata": {
            "project": "ПКБ-101",
            "author": "Иванов С.П.",
            "registry_doc_id": "rd-002",
        },
        "pages": [
            {
                "page": 1,
                "width": 3508,
                "height": 2480,
                "ocr_status": "completed",
                "confidence": 0.97,
                "has_text_layer": True,
            },
        ],
        "parameters": {
            "designation": "ПКБ.101.002",
            "title": "Деталь 101",
            "materials": ["Сталь 45"],
            "dimensions": "150x80x25",
            "references": ["ГОСТ 2.109-73"],
            "specification_items": [],
        },
        "extraction_confidence": 0.94,
        "unconfirmed_fields": [],
        "created_at": "2026-04-26T14:00:00Z",
        "updated_at": "2026-04-26T15:00:00Z",
    },
    {
        "document_id": "doc-003",
        "filename": "archive_scan_1985.pdf",
        "title": "Архивная копия альбома чертежей 1985",
        "document_type": "archival_scan",
        "source": "upload",
        "version": 1,
        "status": "processing",
        "file_size": 35800000,
        "pages_total": 45,
        "pages_processed": 23,
        "pages_failed": 1,
        "ocr_status": "processing",
        "index_status": "pending",
        "user_id": "u-002",
        "uploaded_by": "Петрова А.В.",
        "metadata": {
            "project": "Архив-2025",
            "author": "Архив ПКБ",
            "registry_doc_id": "rd-003",
        },
        "pages": [
            {
                "page": 1,
                "width": 2480,
                "height": 3508,
                "ocr_status": "completed",
                "confidence": 0.45,
                "has_text_layer": False,
            },
            {
                "page": 2,
                "width": 2480,
                "height": 3508,
                "ocr_status": "completed",
                "confidence": 0.72,
                "has_text_layer": False,
            },
        ],
        "parameters": {},
        "extraction_confidence": 0.0,
        "unconfirmed_fields": [],
        "created_at": "2026-04-27T12:00:00Z",
        "updated_at": "2026-04-27T12:30:00Z",
    },
    {
        "document_id": "doc-004",
        "filename": "ГОСТ_2.109_полный.pdf",
        "title": "ГОСТ 2.109-73 полный текст",
        "document_type": "normative",
        "source": "upload",
        "version": 1,
        "status": "completed",
        "file_size": 512000,
        "pages_total": 10,
        "pages_processed": 10,
        "pages_failed": 0,
        "ocr_status": "completed",
        "index_status": "completed",
        "user_id": "u-003",
        "uploaded_by": "Сидоров П.А.",
        "metadata": {
            "project": "НСИ",
            "author": "Госстандарт",
            "registry_doc_id": "rd-004",
        },
        "pages": [
            {
                "page": 1,
                "width": 2480,
                "height": 3508,
                "ocr_status": "completed",
                "confidence": 0.99,
                "has_text_layer": True,
            },
        ],
        "parameters": {},
        "extraction_confidence": 0.0,
        "unconfirmed_fields": [],
        "created_at": "2026-04-25T09:00:00Z",
        "updated_at": "2026-04-25T10:00:00Z",
    },
    {
        "document_id": "doc-005",
        "filename": "нормоконтроль_проверка.pdf",
        "title": "Нормоконтроль — проверка спецификации",
        "document_type": "specification",
        "source": "upload",
        "version": 1,
        "status": "failed",
        "file_size": 1024000,
        "pages_total": 5,
        "pages_processed": 3,
        "pages_failed": 2,
        "ocr_status": "failed",
        "index_status": "failed",
        "user_id": "u-001",
        "uploaded_by": "Иванов С.П.",
        "metadata": {
            "project": "ПКБ-102",
            "author": "Иванов С.П.",
            "registry_doc_id": None,
        },
        "pages": [],
        "parameters": {},
        "extraction_confidence": 0.0,
        "unconfirmed_fields": [],
        "created_at": "2026-04-24T08:00:00Z",
        "updated_at": "2026-04-24T08:30:00Z",
    },
]

SEED_DOCUMENT_ERRORS: List[Dict[str, Any]] = [
    {
        "error_id": "err-001",
        "document_id": "doc-005",
        "page": 4,
        "stage": "ocr",
        "error_code": "OCR_FAILED",
        "error_message": "Не удалось распознать текст на странице: низкое качество изображения",
        "severity": "error",
        "retry_attempt": 1,
        "timestamp": "2026-04-24T08:25:00Z",
    },
    {
        "error_id": "err-002",
        "document_id": "doc-005",
        "page": 5,
        "stage": "ocr",
        "error_code": "OCR_FAILED",
        "error_message": "Повреждённый файл: неверный формат страницы",
        "severity": "error",
        "retry_attempt": 1,
        "timestamp": "2026-04-24T08:25:00Z",
    },
    {
        "error_id": "err-003",
        "document_id": "doc-003",
        "page": 12,
        "stage": "ocr",
        "error_code": "OCR_LOW_CONFIDENCE",
        "error_message": "Низкое качество распознавания (confidence: 0.35)",
        "severity": "warning",
        "retry_attempt": 2,
        "timestamp": "2026-04-27T12:20:00Z",
    },
]

SEED_QUEUE: List[Dict[str, Any]] = [
    {
        "document_id": "doc-003",
        "title": "Архивная копия альбома чертежей 1985",
        "document_type": "archival_scan",
        "status": "processing",
        "progress_percent": 51,
        "steps": {
            "ocr": "processing",
            "layout_parsing": "pending",
            "indexing": "pending",
        },
        "user_id": "u-002",
        "uploaded_by": "Петрова А.В.",
        "created_at": "2026-04-27T12:00:00Z",
        "started_at": "2026-04-27T12:05:00Z",
        "estimated_completion": "2026-04-27T13:00:00Z",
    },
]

SEED_VALIDATION_CHECKS: List[Dict[str, Any]] = [
    {
        "check_run_id": "check-001",
        "status": "completed",
        "summary": {"ok": 8, "warning": 2, "error": 1},
        "items": [
            {
                "check_item_id": "ci-001",
                "project": "ПКБ-101",
                "section": "Общие требования",
                "parameter": "Толщина стенки",
                "project_value": "5 мм",
                "nsi_requirement": "≥ 4 мм",
                "nsi_document": "ГОСТ 2.109-73",
                "status": "ok",
                "match_status": "match",
                "comment": "",
                "project_source": {
                    "document_id": "doc-001",
                    "page": 3,
                    "page_preview_url": "/api/v1/documents/doc-001/pages/3/preview",
                    "document_url": "/api/v1/documents/doc-001",
                },
                "nsi_source": {
                    "document_id": "rd-001",
                    "page": 5,
                    "page_preview_url": "/api/v1/documents/rd-001/pages/5/preview",
                    "document_url": "/api/v1/documents/rd-001",
                },
            },
            {
                "check_item_id": "ci-002",
                "project": "ПКБ-101",
                "section": "Размеры",
                "parameter": "Допуск отверстия",
                "project_value": "H12",
                "nsi_requirement": "H11",
                "nsi_document": "ГОСТ 2.307-2011",
                "status": "warning",
                "match_status": "partial_match",
                "comment": "Рекомендуется уточнить допуск",
                "project_source": {
                    "document_id": "doc-001",
                    "page": 5,
                    "page_preview_url": "/api/v1/documents/doc-001/pages/5/preview",
                    "document_url": "/api/v1/documents/doc-001",
                },
                "nsi_source": {
                    "document_id": "rd-002",
                    "page": 3,
                    "page_preview_url": "/api/v1/documents/rd-002/pages/3/preview",
                    "document_url": "/api/v1/documents/rd-002",
                },
            },
            {
                "check_item_id": "ci-003",
                "project": "ПКБ-101",
                "section": "Материалы",
                "parameter": "Марка стали",
                "project_value": "Сталь 20",
                "nsi_requirement": "Сталь 45",
                "nsi_document": "ГОСТ 2.109-73",
                "status": "error",
                "match_status": "mismatch",
                "comment": "Несоответствие марки материала",
                "project_source": {
                    "document_id": "doc-001",
                    "page": 7,
                    "page_preview_url": "/api/v1/documents/doc-001/pages/7/preview",
                    "document_url": "/api/v1/documents/doc-001",
                },
                "nsi_source": {
                    "document_id": "rd-001",
                    "page": 8,
                    "page_preview_url": "/api/v1/documents/rd-001/pages/8/preview",
                    "document_url": "/api/v1/documents/rd-001",
                },
            },
        ],
        "created_at": "2026-04-27T11:00:00Z",
        "updated_at": "2026-04-27T11:05:00Z",
    },
]

SEED_COMPARISONS: List[Dict[str, Any]] = [
    {
        "comparison_id": "comp-001",
        "status": "completed",
        "normative_block": {
            "document_id": "rd-001",
            "document_title": "ГОСТ 2.109-73",
            "page": 5,
            "requirement_text": "Толщина стенки должна быть не менее 4 мм для данного типа изделий.",
        },
        "project_block": {
            "document_id": "doc-001",
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
        "processing_time_ms": 1234,
    },
]

SEED_METRICS: Dict[str, Any] = {
    "control_metrics": {
        "ocr_quality": 0.87,
        "retrieval_quality": 0.92,
        "answers_with_sources": 0.95,
        "avg_latency_ms": 2450,
    },
    "answer_metrics": {
        "useful_rate": 0.78,
        "rated_answers": 342,
        "flagged_for_review": 12,
        "open_questions": 5,
    },
    "logs": [
        {
            "time": "2026-04-27T10:00:00Z",
            "type": "rag_search",
            "text": "Поиск по запросу 'толщина стенки'",
            "level": "INFO",
        },
        {
            "time": "2026-04-27T10:00:01Z",
            "type": "rag_answer",
            "text": "Сгенерирован ответ на запрос",
            "level": "INFO",
        },
        {
            "time": "2026-04-27T09:55:00Z",
            "type": "ocr_process",
            "text": "Завершён OCR документа doc-001",
            "level": "INFO",
        },
        {
            "time": "2026-04-27T09:30:00Z",
            "type": "system",
            "text": "Загрузка документа doc-003: низкое качество скана",
            "level": "WARN",
        },
        {
            "time": "2026-04-27T08:00:00Z",
            "type": "error",
            "text": "Ошибка индексации документа doc-005",
            "level": "ERROR",
        },
    ],
}

# ---------------------------------------------------------------------------
# Seed-данные для Query Service
# ---------------------------------------------------------------------------

SEED_SESSIONS: List[Dict[str, Any]] = [
    {
        "session_id": "sess-001",
        "title": "Анализ спецификации ПКБ-101",
        "user_id": "u-001",
        "document_ids": ["doc-001", "doc-002"],
        "options": {
            "model": "gpt-4",
            "temperature": 0.3,
            "max_context_messages": 10,
        },
        "message_count": 5,
        "messages": [
            {
                "message_id": "msg-001",
                "role": "user",
                "content": "Проверь толщину стенки корпуса по спецификации ПКБ-101",
                "timestamp": "2026-04-27T10:00:00Z",
                "status": "completed",
            },
            {
                "message_id": "msg-002",
                "role": "assistant",
                "content": "Толщина стенки корпуса в спецификации ПКБ-101 составляет 5 мм. Это соответствует требованию ГОСТ 2.109-73 (не менее 4 мм).",
                "timestamp": "2026-04-27T10:00:05Z",
                "status": "completed",
                "sources": [
                    {
                        "document_id": "doc-001",
                        "document_title": "Спецификация по ГОСТ 2.109",
                        "page_number": 3,
                        "fragment_id": "frag-001",
                        "text": "Толщина стенки: 5 мм",
                        "score": 0.95,
                    },
                    {
                        "document_id": "rd-001",
                        "document_title": "ГОСТ 2.109-73",
                        "page_number": 5,
                        "fragment_id": "frag-002",
                        "text": "Толщина стенки не менее 4 мм",
                        "score": 0.92,
                    },
                ],
                "model_used": "gpt-4",
                "processing_time_ms": 2340,
                "feedback": {"rating": 5, "comment": "Отличный ответ"},
            },
        ],
        "has_more": False,
        "last_message_preview": "Толщина стенки корпуса...",
        "created_at": "2026-04-27T09:55:00Z",
        "updated_at": "2026-04-27T10:00:05Z",
    },
    {
        "session_id": "sess-002",
        "title": "Верификация чертежа 101",
        "user_id": "u-001",
        "document_ids": ["doc-002"],
        "options": {
            "model": "gpt-4",
            "temperature": 0.2,
            "max_context_messages": 10,
        },
        "message_count": 2,
        "messages": [
            {
                "message_id": "msg-003",
                "role": "user",
                "content": "Какие размеры на чертеже детали 101?",
                "timestamp": "2026-04-27T11:00:00Z",
                "status": "completed",
            },
            {
                "message_id": "msg-004",
                "role": "assistant",
                "content": "На чертеже детали 101 указаны размеры: 150x80x25 мм. Материал: Сталь 45.",
                "timestamp": "2026-04-27T11:00:03Z",
                "status": "completed",
                "sources": [
                    {
                        "document_id": "doc-002",
                        "document_title": "Чертеж детали 101",
                        "page_number": 1,
                        "fragment_id": "frag-003",
                        "text": "150x80x25",
                        "score": 0.98,
                    },
                ],
                "model_used": "gpt-4",
                "processing_time_ms": 1800,
            },
        ],
        "has_more": False,
        "last_message_preview": "На чертеже детали 101...",
        "created_at": "2026-04-27T10:58:00Z",
        "updated_at": "2026-04-27T11:00:03Z",
    },
]

SEED_HISTORY: List[Dict[str, Any]] = [
    {
        "history_id": "hist-001",
        "session_id": "sess-001",
        "created_at": "2026-04-27T10:00:00Z",
        "user_id": "u-001",
        "user_name": "Иванов С.П.",
        "question": "Проверь толщину стенки корпуса по спецификации ПКБ-101",
        "answer_preview": "Толщина стенки корпуса в спецификации ПКБ-101 составляет 5 мм...",
        "status": "completed",
        "source_count": 2,
        "answer_id": "ans-001",
    },
    {
        "history_id": "hist-002",
        "session_id": "sess-002",
        "created_at": "2026-04-27T11:00:00Z",
        "user_id": "u-001",
        "user_name": "Иванов С.П.",
        "question": "Какие размеры на чертеже детали 101?",
        "answer_preview": "На чертеже детали 101 указаны размеры: 150x80x25 мм...",
        "status": "completed",
        "source_count": 1,
        "answer_id": "ans-002",
    },
    {
        "history_id": "hist-003",
        "session_id": "sess-001",
        "created_at": "2026-04-27T09:58:00Z",
        "user_id": "u-001",
        "user_name": "Иванов С.П.",
        "question": "Какие материалы указаны в спецификации?",
        "answer_preview": "В спецификации указаны материалы: Сталь 45, Алюминий Д16Т...",
        "status": "completed",
        "source_count": 1,
        "answer_id": "ans-003",
    },
]
