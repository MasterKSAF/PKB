"""
PKB Neuroassistant — Parser Service API Definitions.

Основано на: docs/api/parser_service_api.md
Обновления (19.06.2026):
- PS-5: POST /parser/process с mode=preview|full (единый эндпоинт)
- PS-6: mode, preview_not_supported в ответ
- PS-8: Код PREVIEW_NOT_SUPPORTED (422)
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "parser"
PORT = 8087
DISPLAY_NAME = "Parser Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Parser Service."""

    _warnings = []

    prepare_endpoints = [
        # PS-5: mode=preview|full
        # PS-3: обязательный draft_id
        EndpointDef("POST", f"{API_PREFIX}/parser/process", "parser",
            "Запуск обработки (prepare)",
            body={"task_id": 12345, "draft_id": 1, "version_id": "1",
                  "file_key": "test-file-key.pdf", "mode": "full"},
            extract_keys=["task_id"],
            response_schema={"task_id": int, "status": str, "mode": str},
            is_preparation=True,
            expected_status=202),
    ]

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        # PS-5: единый эндпоинт process с mode
        # PS-6: preview_not_supported в ответ
        # PS-8: PREVIEW_NOT_SUPPORTED (422)
        EndpointDef("POST", f"{API_PREFIX}/parser/process", "parser",
            "Запуск обработки (mode=preview|full)",
            body={"task_id": 12345, "draft_id": 1, "version_id": "1",
                  "file_key": "test-file-key.pdf", "mode": "full"},
            response_schema={"task_id": int, "status": str, "mode": str}),
        EndpointDef("GET", f"{API_PREFIX}/parser/process/{{task_id}}/status",
            "parser", "Статус обработки (longpoll)",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/parser/process/{{task_id}}/result",
            "parser", "Итоговый JSON обработки",
            expected_status={200, 409},
            response_schema={"status": str}),
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
        warnings=_warnings,
    )
