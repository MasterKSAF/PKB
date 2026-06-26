"""
PKB Neuroassistant — Converter-Validator Service API Definitions.

Основано на: docs/api/converter_validator_service_api.md
Обновления (19.06.2026):
- CV-3: POST /converter/preview/metadata → POST /converter/preview (без бизнес-ключа)
- CV-3a: POST /validate/metadata — единая точка вычисления бизнес-ключа
- CV-8: Убрать document_id из ответов convert/validate
- CV-9: Убрать version_id из ответа convert
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "converter_validator"
PORT = 18086
DISPLAY_NAME = "Converter-Validator Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Converter-Validator Service."""

    _warnings: list = []

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        # CV-3: POST /converter/preview (вместо /converter/preview/metadata)
        # Без title_hash_sha256/title_key в ответе (14 полей, без бизнес-ключа)
        # CV-4: проверка 8+ полей preview_metadata
        EndpointDef("POST", f"{API_PREFIX}/converter/preview", "converter",
            "Предпросмотр метаданных",
            body={"task_id": 12345,
                  "version_id": "1",
                  "raw_json": {
                      "metadata": {"schema": "raw_ocr_v4"},
                      "document": {
                          "source": {"file_name": "test.pdf", "title": "Тестовый документ"},
                          "pages": [{"page": 1, "width": 210, "height": 297}],
                          "block": [{"number": 1, "type": "paragraph", "page": 1,
                                      "content": "Тестовый документ ГОСТ 20868-81"}]
                      }
                  }},
            response_schema={
                "doc_code": str,
                "title": str,
                "document_type": str,
                "source_type": str,
                "era": str,
                "validity_status": str,
                "mks_oks_code": (str, type(None)),
                "okstu_code": (str, type(None)),
                "udk_code": (str, type(None)),
                "jurisdiction": (str, type(None)),
                "issuing_body": (str, type(None)),
                "language": (str, type(None)),
            }),
        # CV-3a: POST /validate/metadata — единая точка вычисления бизнес-ключа
        # DB-1/DB-28: title_hash_sha256, title_key в ответе
        EndpointDef("POST", f"{API_PREFIX}/validate/metadata", "validate",
            "Валидация метаданных (вычисление бизнес-ключа)",
            body={"title": "Тестовый документ", "doc_code": "TEST-001",
                  "source_type": "GOST", "era": "RF", "year": 2026},
            response_schema={"title_hash_sha256": str, "title_key": str,
                             "normalized_title": str, "source_type_normalized": str,
                             "era_normalized": str}),
        # CV-8/CV-9: convert без document_id и version_id
        EndpointDef("POST", f"{API_PREFIX}/converter/convert", "converter",
            "Конвертация документа",
            body={"task_id": 12345,
                  "version_id": "1",
                  "raw_json": {
                      "metadata": {"schema": "raw_ocr_v4"},
                      "document": {
                          "source": {"file_name": "test.pdf", "title": "Тестовый документ"},
                          "pages": [{"page": 1, "width": 210, "height": 297}],
                          "block": [{"number": 1, "type": "paragraph", "page": 1,
                                      "content": "Тестовый документ ГОСТ 20868-81"}]
                      }
                  }},
            response_schema={"task_id": str, "validation": dict}),
        # validate/document — без document_id
        EndpointDef("POST", f"{API_PREFIX}/validate/document", "validate",
            "Валидация документа",
            body={"task_id": 12345,
                  "version_id": "1",
                  "raw_json": {
                      "metadata": {"schema": "raw_ocr_v4"},
                      "document": {
                          "source": {"file_name": "test.pdf", "title": "Тестовый документ"},
                          "pages": [{"page": 1, "width": 210, "height": 297}],
                          "block": [{"number": 1, "type": "paragraph", "page": 1,
                                      "content": "Тестовый документ ГОСТ 20868-81"}]
                      }
                  }},
            response_schema={"validation_id": str, "structure_valid": bool, "status": str}),
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
