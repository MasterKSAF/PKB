"""
PKB Neuroassistant — Converter-Validator Service API Definitions.

Основано на: docs/api/converter_validator_service_api.md
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "converter_validator"
PORT = 8086
DISPLAY_NAME = "Converter-Validator Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Converter-Validator Service."""

    _warnings = [
        "⚠️ Converter health на /health, а не /api/v1/health — сервис без префикса.",
        "⚠️ task_id/version_id передаём как str — сервис требует str, docs API — int.",
        "⚠️ document_id/validation_id принимаем как str — сервис возвращает UUID, docs — int.",
    ]

    endpoints = [
        # ⚠️ WORKAROUND: health на /health, а не /api/v1/health (сервис не использует префикс).
        EndpointDef("GET", "/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/converter/preview/metadata", "converter",
            "Предпросмотр метаданных",
            # ⚠️ WORKAROUND: сервис ожидает task_id/version_id как str, хотя документация API — int.
            body={"task_id": "12345", "version_id": "1",
                  "raw_json": {"test": True}},
            # docs: { doc_code, title, document_type, year, revision }
            response_schema={"doc_code": str, "title": str, "document_type": str}),
        EndpointDef("POST", f"{API_PREFIX}/converter/convert", "converter",
            "Конвертация документа",
            # ⚠️ WORKAROUND: сервис ожидает str, docs — int.
            body={"task_id": "12345", "version_id": "1",
                  "raw_json": {"test": True}},
            # docs: { task_id, version_id, document_id, metadata{}, document{}, validation{} }
            # document_id теперь в registry, converter его не возвращает
            response_schema={"task_id": str, "version_id": str,
                             "validation": dict}),
        EndpointDef("POST", f"{API_PREFIX}/validate/document", "validate",
            "Валидация документа",
            # ⚠️ WORKAROUND: сервис ожидает str, docs — int.
            body={"task_id": "12345", "version_id": "1",
                  "raw_json": {"test": True}},
            # docs: { validation_id, document_id, structure_valid, classification{}, status }
            # document_id теперь в registry
            response_schema={"validation_id": str,
                             "structure_valid": bool, "status": str}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,
        endpoints=endpoints,
        prepare_endpoints=[],
        depends_on=["registry"],
        base_data={},
        warnings=_warnings,
    )
