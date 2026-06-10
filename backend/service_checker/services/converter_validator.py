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

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/converter/preview/metadata", "converter",
            "Предпросмотр метаданных",
            body={"task_id": 12345, "version_id": 1,
                  "raw_json": {"test": True}},
            # docs: { doc_code, title, document_type, year, revision }
            response_schema={"doc_code": str, "title": str, "document_type": str}),
        EndpointDef("POST", f"{API_PREFIX}/converter/convert", "converter",
            "Конвертация документа",
            body={"task_id": 12345, "version_id": 1,
                  "raw_json": {"test": True}},
            # docs: { task_id, version_id, document_id, metadata{}, document{}, validation{} }
            response_schema={"task_id": int, "version_id": int,
                             "document_id": int, "validation": dict}),
        EndpointDef("POST", f"{API_PREFIX}/validate/document", "validate",
            "Валидация документа",
            body={"task_id": 12345, "version_id": 1,
                  "raw_json": {"test": True}},
            # docs: { validation_id, document_id, structure_valid, classification{}, status }
            response_schema={"validation_id": int, "document_id": int,
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
    )
