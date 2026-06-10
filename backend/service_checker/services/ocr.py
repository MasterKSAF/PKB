"""
PKB Neuroassistant — OCR Service API Definitions.

Основано на: docs/api/ocr_service_api.md
"""

from __future__ import annotations

from services.base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "ocr"
PORT = 8088
DISPLAY_NAME = "OCR Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание OCR Service."""

    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/ocr/process", "ocr",
            "Запуск OCR обработки (prepare)",
            body={"task_id": "test-task", "version_id": "test-version",
                  "file_key": "test-file-key"},
            extract_keys=["task_id"],
            # docs: { task_id, status, mode, estimated_completion }
            response_schema={"task_id": (int, str), "status": str},
            is_preparation=True,
            expected_status=202),
    ]

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/ocr/process", "ocr",
            "Запуск OCR обработки",
            body={"task_id": "test-task", "version_id": "test-version",
                  "file_key": "test-file-key"},
            # docs: { task_id, status, mode, estimated_completion }
            response_schema={"task_id": (int, str), "status": str}),
        EndpointDef("POST", f"{API_PREFIX}/ocr/preview", "ocr",
            "Быстрый OCR предпросмотр",
            body={"task_id": "test-task", "version_id": "test-version",
                  "file_key": "test-file-key", "max_pages": 1},
            # docs: { task_id, status, mode, estimated_completion }
            response_schema={"task_id": (int, str), "status": str}),
        EndpointDef("GET", f"{API_PREFIX}/ocr/process/{{task_id}}/status",
            "ocr", "Статус OCR обработки",
            # docs: { task_id, status, progress_percent, pages_processed, pages_total, avg_confidence, step }
            response_schema={"task_id": (int, str), "status": str, "progress_percent": (int, float)}),
        EndpointDef("GET", f"{API_PREFIX}/ocr/process/{{task_id}}/result",
            "ocr", "Итоговый JSON OCR",
            # docs: { task_id, metadata{}, document{}, quality{}, status }
            response_schema={"task_id": (int, str), "status": str, "document": dict}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=[],
        base_data={},
    )
