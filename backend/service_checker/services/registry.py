"""
PKB Neuroassistant — Registry Service API Definitions.

Основано на: docs/api/registry_service_api.md
Обновления (19.06.2026):
- RG-2: current_version_id в ответе
- RG-6/RG-7: valid_from/valid_until поля, ?valid_at фильтр
- RG-8: GET /registry/search?q=... (BM25)
- RG-9: source_draft_id, возвращать version_id
- RG-10: preview_snapshot (JSONB)
- RG-11: document_id назначается Registry
- DB-1: title_hash_sha256, DB-28: title_key
"""

from __future__ import annotations

import time

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "registry"
PORT = 8084
DISPLAY_NAME = "Registry Service"

_ts = str(int(time.time()))[-6:]

PREPARE_CLASSIFIER = {
    "classifier_system": "MKS",
    "code": f"99.{_ts}",
    "full_name": "Тестовый классификатор API Coverage",
    "status": "active",
}

VALIDATE_CLASSIFICATION = {
    "classification": {
        "mks_oks_code": "47.020",
        "okstu_code": None,
        "udk_code": "629.5.021",
    }
}

# RG-9: source_draft_id в POST /documents + возвращает version_id
# DB-1/DB-28: title_hash_sha256 и title_key (вычисляет Converter/Validate)
PREPARE_DOCUMENT = {
    "title": f"Тестовый документ API Coverage {_ts}",
    "doc_code": f"ТЕСТ-{_ts}",
    "source_type": "GOST",
    "era": "RF",
    "validity_status": "active",
    "mks_oks_code": f"98.{_ts}",
    "okstu_code": f"88.{_ts}",
    "title_key": f"GOST|RF|ТЕСТ-{_ts}|{_ts}",  # DB-28
}

PREPARE_TERM = {
    "raw_term": f"API Coverage тест {_ts}",
    "standard_term": f"API Coverage тест {_ts}",
    "normalized_value": f"api coverage тест {_ts}",
    "term_type": "abbreviation",
    "definition": "Тестовый термин для API Coverage",
}


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Registry Service."""

    _warnings = [
            "⚠️ Registry требует trailing slash на всех эндпоинтах /classifiers/, /documents/, /terminology/ (в т.ч. параметризованные). Документация — без /.",
        ]

    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/", "classifiers",
            "Создать классификатор (prepare)",
            body=PREPARE_CLASSIFIER,
            extract_keys=["classifier_code"],
            response_schema={"data": dict, "data.classifier_system": str, "data.code": str, "data.full_name": str, "data.status": str},
            is_preparation=True,
            expected_status={201, 409}),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/", "documents",
            "Создать документ (prepare)",
            body=PREPARE_DOCUMENT,
            extract_keys=["doc_id", "version_id"],
            response_schema={"data": dict, "data.document_id": int, "data.version_id": int,
                             "data.current_version_id": int},  # RG-2
            is_preparation=True,
            expected_status={201, 409}),
        EndpointDef("POST", f"{API_PREFIX}/registry/terminology/", "terminology",
            "Создать термин (prepare)",
            body=PREPARE_TERM,
            extract_keys=["term_id"],
            response_schema={"data": dict, "data.raw_term": str, "data.standard_term": str, "data.normalized_value": str, "data.term_type": str},
            is_preparation=True,
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/pending/", "classifiers",
            "Получить pending_id (prepare)",
            params={"page": 1, "page_size": 10},
            extract_keys=["pending_id"],
            is_preparation=True),
    ]

    endpoints = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check",
            response_schema={"status": str}),
        # ── Classifiers CRUD ──
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/", "classifiers",
            "Список классификаторов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list, "meta": dict, "meta.total": int, "meta.page": int, "meta.page_size": int}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/tree/", "classifiers",
            "Дерево классификаторов",
            params={"classifier_system": "MKS"},
            response_schema={"data": list}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/{{classifier_code}}",
            "classifiers", "Получить классификатор",
            params={"classifier_system": "MKS"},
            response_schema={"data": dict, "data.classifier_system": str, "data.code": str, "data.full_name": str}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/classifiers/{{classifier_code}}",
            "classifiers", "Обновить классификатор",
            params={"classifier_system": "MKS"},
            body={"full_name": "Обновлённый тестовый классификатор"},
            response_schema={"data": dict, "data.classifier_system": str, "data.code": str, "data.full_name": str}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/classifiers/{{classifier_code}}",
            "classifiers", "Частичное обновление",
            params={"classifier_system": "MKS"},
            body={"status": "inactive"},
            response_schema={"data": dict, "data.classifier_system": str, "data.code": str, "data.status": str}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/classifiers/{{classifier_code}}",
            "classifiers", "Удалить классификатор",
            params={"classifier_system": "MKS"},
            response_schema={"data": dict}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/import",
            "classifiers", "Импорт классификаторов (file upload)",
            response_schema={"data": dict, "data.classifier_system": str, "data.inserted": int},
            is_preparation=True,
            expected_status={422}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/pending",
            "classifiers", "Карантин",
            response_schema={"data": list}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/pending/{{pending_id}}/accept",
            "classifiers", "Принять из карантина",
            body={"parent_code": "01.040", "full_name": "Принятый термин"},
            response_schema={"data": dict, "data.status": str}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/pending/{{pending_id}}/reject",
            "classifiers", "Отклонить из карантина",
            body={"admin_comment": "Отклонено тестом"},
            response_schema={"data": dict, "data.status": str}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/validate",
            "classifiers", "Валидация классификации",
            body=VALIDATE_CLASSIFICATION,
            response_schema={"data": dict, "data.mks_status": str, "data.udk_valid": bool, "data.overall_status": str}),
        # ── Terminology CRUD ──
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology/", "terminology",
            "Список терминов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology/{{term_id}}",
            "terminology", "Получить термин",
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology/normalize/",
                    "terminology", "Нормализовать термин",
            params={"term": "API Coverage тест"},
            response_schema={"data": dict, "data.raw_term": str, "data.normalized_value": str}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/terminology/{{term_id}}",
            "terminology", "Обновить термин",
            body={"definition": "Обновлённое определение"},
            response_schema={"data": dict, "data.raw_term": str, "data.id": int}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/terminology/{{term_id}}",
            "terminology", "Удалить термин",
            response_schema={"data": dict}),
        EndpointDef("POST", f"{API_PREFIX}/registry/terminology/import",
            "terminology", "Импорт терминов (file upload)",
            response_schema={"data": dict, "data.inserted": int},
            is_preparation=True,
            expected_status={422}),
        # ── Documents CRUD ──
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/", "documents",
            "Список документов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list, "meta": dict, "meta.total": int, "meta.page": int, "meta.page_size": int}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Получить документ",
            # RG-2: current_version_id, RG-10: preview_snapshot
            response_schema={"data": dict, "data.id": int, "data.title": str, "data.doc_code": str,
                             "data.current_version_id": int}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Обновить документ",
            body={"title": "Обновлённый документ"},
            response_schema={"data": dict}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/documents/{{doc_id}}/status",
            "documents", "Обновить статус (internal)",
            body={"status": "uploaded"},
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/history",
            "documents", "История статусов",
            response_schema={"data": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/succession/",
            "documents", "Цепочка преемственности",
            response_schema={"data": dict, "data.document_id": int, "data.chain": list}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Удалить документ",
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/export",
            "documents", "Экспорт документов (CSV)",
            response_schema=None),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/import",
            "documents", "Массовый импорт (file upload)",
            response_schema={"data": dict, "data.inserted": int},
            is_preparation=True,
            expected_status={422}),
        # ── Documents: Search (BM25) ──
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/search/",
            "documents", "Полнотекстовый поиск (BM25)",
            params={"q": "тест", "limit": 10},
            response_schema={"data": list, "meta": dict}),
        # ── Documents: Sections ──
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/sections/",
            "documents", "Секции документа (для RAG Builder)",
            response_schema={"document": dict, "sections": list}),
        # ── Documents: Check Uniqueness ──
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/check-uniqueness/",
            "documents", "Проверить уникальность",
            body={"title": "Тестовый документ", "doc_code": "TEST-001",
                  "era": "RF", "source_type": "GOST"},
            response_schema={"data": dict, "data.is_duplicate": bool}),
        # ── Documents: Partial Update ──
        EndpointDef("PATCH", f"{API_PREFIX}/registry/documents/{{doc_id}}/",
            "documents", "Частичное обновление",
            body={"metadata": {"tags": ["обновлено"]}, "validity_status": "superseded"},
            response_schema={"data": dict, "data.updated_fields": list}),
        # ── Categories CRUD ──
        EndpointDef("GET", f"{API_PREFIX}/registry/categories/", "categories",
            "Список категорий",
            response_schema={"data": list, "meta": dict}),
        EndpointDef("POST", f"{API_PREFIX}/registry/categories/", "categories",
            "Создать категорию",
            body={"name": "Тестовая категория", "slug": "test-category"},
            extract_keys=["category_id"],
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/registry/categories/{{category_id}}",
            "categories", "Получить категорию",
            response_schema={"data": dict}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/categories/{{category_id}}",
            "categories", "Обновить категорию",
            body={"name": "Обновлённая категория", "color": "#4CAF50"},
            response_schema={"data": dict}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/categories/{{category_id}}",
            "categories", "Удалить категорию",
            response_schema={"data": dict}),
        # ── Drafts CRUD (internal, для Orchestrator) ──
        EndpointDef("POST", f"{API_PREFIX}/registry/drafts/", "drafts",
            "Создать запись черновика",
            body={"document_id": "{doc_id}", "title": "Тестовый черновик"},
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/registry/drafts/", "drafts",
            "Список черновиков",
            response_schema={"data": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/drafts/{{draft_id}}",
            "drafts", "Полная информация о черновике",
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/drafts/{{draft_id}}/preview/",
            "drafts", "Preview-метаданные",
            response_schema={"data": dict}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/drafts/{{draft_id}}/status",
            "drafts", "Обновить статус",
            body={"status": "processing"},
            response_schema={"data": dict}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/drafts/{{draft_id}}",
            "drafts", "Удалить запись черновика",
            response_schema={"data": dict}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/drafts/{{draft_id}}/metadata",
            "drafts", "Обновить метаданные черновика (internal)",
            body={"preview_metadata": {"doc_code": "311-05-1950ц-ИЗМ1",
                  "title": "ЦИРКУЛЯРНОЕ ПИСЬМО № 311-05-1950ц (изм.1)",
                  "title_hash_sha256": "<новый-хеш>",
                  "title_key": "<новая-строка>"},
                  "metadata_overrides": {"valid_from": "2026-01-01", "valid_until": None},
                  "updated_by": "orchestrator"},
            response_schema={"data": dict, "data.id": int, "data.status": str,
                             "data.preview_metadata": dict, "data.updated_at": str}),
        # ── RG-8: Search (BM25) ──
        EndpointDef("GET", f"{API_PREFIX}/registry/search", "search",
            "Поиск по реестру (BM25, pg_trgm + tsvector)",
            params={"q": "тест", "valid_at": "2026-06-19"},
            response_schema={"data": list, "meta": dict}),
        # Common
        EndpointDef("GET", f"{API_PREFIX}/registry/stats", "common",
            "Статистика", response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/enums", "common",
            "Допустимые значения", response_schema={"data": dict}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=True,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=[],
        base_data={},
        warnings=_warnings,
    )
