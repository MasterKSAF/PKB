"""
PKB Neuroassistant — OCR Service API Definitions.

Основано на: docs/api/ocr_service_api.md
Обновления (19.06.2026):
- OC-8: POST /ocr/process с mode=preview|full (единый эндпоинт)
- OC-9: mode, preview_not_supported в ответ
- OC-11: Код PREVIEW_NOT_SUPPORTED (422)
- OC-6: Убрать version_id из контракта
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "ocr"
PORT = 18088
DISPLAY_NAME = "OCR Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание OCR Service."""

    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/ocr/process", "ocr",
            "Запуск OCR обработки (prepare)",
            body={"task_id": "{task_id}", "draft_id": "{draft_id}",  # OC-4: обязательный draft_id
                  "file_key": "test-file-key", "mode": "preview"},
            extract_keys=["task_id"],
            response_schema={"task_id": int, "status": str, "mode": str},
            is_preparation=True,
            expected_status=202),
    ]

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        # OC-8: единый эндпоинт process с mode=preview|full (вместо /ocr/preview + /ocr/process)
        # OC-9: preview_not_supported в ответ
        # OC-11: PREVIEW_NOT_SUPPORTED (422)
        EndpointDef("POST", f"{API_PREFIX}/ocr/process", "ocr",
            "Запуск OCR обработки (mode=preview|full)",
            body={"task_id": "{task_id}", "draft_id": "{draft_id}",  # OC-4: обязательный draft_id
                  "file_key": "test-file-key", "mode": "full"},
            response_schema={"task_id": int, "status": str, "mode": str,
                             "preview_not_supported": bool}),
        EndpointDef("GET", f"{API_PREFIX}/ocr/process/{{task_id}}/status",
            "ocr", "Статус OCR обработки",
            response_schema={"task_id": int, "status": str, "progress_percent": (int, float)}),
        EndpointDef("GET", f"{API_PREFIX}/ocr/process/{{task_id}}/result",
            "ocr", "Итоговый JSON OCR",
            response_schema={"task_id": int, "status": str, "document": dict}),
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
