"""
PKB Neuroassistant — Registry Service API Definitions.

Основано на: docs/api/registry_service_api.md
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

# ── Тестовые данные для prepare-шагов ──────────────────────────────────

_ts = str(int(time.time()))[-6:]

# Классификатор для prepare (создаётся перед CRUD-тестами)
PREPARE_CLASSIFIER = {
    "classifier_system": "MKS",
    "code": f"99.{_ts}",
    "full_name": "Тестовый классификатор API Coverage",
    "status": "active",
}

# Данные классификатора для валидации (должен существовать в БД)
VALIDATE_CLASSIFICATION = {
    "classification": {
        "mks_oks_code": "47.020",
        "okstu_code": None,
        "udk_code": "629.5.021",
    }
}

# Документ для prepare
PREPARE_DOCUMENT = {
    "title": f"Тестовый документ API Coverage {_ts}",
    "doc_code": f"ТЕСТ-{_ts}",
    "source_type": "GOST",
    "era": "RF",
    "validity_status": "active",
}

# Термин для prepare
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
            "⚠️ Checker: пути пайплайнов исправлены — добавлены слеши. API Coverage Registry 28/32 (2 failed — import/walidate без endpoints), pipeline registry_lifecycle теперь должен проходить.",
        ]

    # ── Prepare-эндпоинты (создают данные для тестов) ──────────────
    prepare_endpoints = [
        # Создать классификатор → context.classifier_code
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/", "classifiers",
            "Создать классификатор (prepare)",
            body=PREPARE_CLASSIFIER,
            extract_keys=["classifier_code"],
            response_schema={"data": dict, "data.classifier_system": str, "data.code": str, "data.full_name": str, "data.status": str},
            is_preparation=True,
            expected_status={201, 409}),
        # Создать документ → context.doc_id
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/", "documents",
            "Создать документ (prepare)",
            body=PREPARE_DOCUMENT,
            extract_keys=["doc_id"],
            response_schema={"data": dict, "data.document_id": int, "data.version_id": int},
            is_preparation=True,
            expected_status={201, 409}),
        # Создать термин → context.term_id
        EndpointDef("POST", f"{API_PREFIX}/registry/terminology/", "terminology",
            "Создать термин (prepare)",
            body=PREPARE_TERM,
            extract_keys=["term_id"],
            response_schema={"data": dict, "data.raw_term": str, "data.standard_term": str, "data.normalized_value": str, "data.term_type": str},
            is_preparation=True,
            expected_status={201, 409}),
    ]

    # ── Основные эндпоинты ──────────────────────────────────────────
    endpoints = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check",
            response_schema={"status": str}),
        # ── Classifiers CRUD ──
        # POST /classifiers/ — только в prepare_endpoints (чтобы избежать дубликата 409)
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/", "classifiers",
            "Список классификаторов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list, "meta": dict, "meta.total": int, "meta.page": int, "meta.page_size": int}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/tree", "classifiers",
            "Дерево классификаторов",
            response_schema={"data": list, "meta": dict, "meta.total": int}),
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
            # docs: data.mks_status, data.mks_display_name, data.okstu_status, data.udk_valid, data.overall_status
            response_schema={"data": dict, "data.mks_status": str, "data.udk_valid": bool, "data.overall_status": str}),
        # ── Terminology CRUD ──
        # POST /terminology/ — только в prepare_endpoints
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
            # docs: data.raw_term, data.standard_term, data.normalized_value, data.term_type, data.is_blocked
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
        # POST /documents/ — только в prepare_endpoints
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/", "documents",
            "Список документов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list, "meta": dict, "meta.total": int, "meta.page": int, "meta.page_size": int}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Получить документ",
            # docs: data.id, data.title, data.doc_code, data.status, data.source_type, data.era
            response_schema={"data": dict, "data.id": int, "data.title": str, "data.doc_code": str}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Обновить документ",
            body={"title": "Обновлённый документ"},
            response_schema={"data": dict}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/documents/{{doc_id}}/status",
            "documents", "Обновить статус",
            body={"status": "uploaded"},
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/history",
            "documents", "История статусов",
            response_schema={"data": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/succession",
            "documents", "Цепочка преемственности",
            response_schema={"data": list, "meta": dict}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Удалить документ",
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/export",
            "documents", "Экспорт документов (CSV)",
            # Возвращает CSV, а не JSON — валидация схемы не применяется
            response_schema=None),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/import",
            "documents", "Массовый импорт (file upload)",
            response_schema={"data": dict, "data.inserted": int},
            is_preparation=True,
            expected_status={422}),
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
