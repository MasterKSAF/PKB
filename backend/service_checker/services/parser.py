"""
PKB Neuroassistant — Parser Service API Definitions.

Основано на: docs/api/parser_service_api.md
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

    _warnings = [
        # Parser теперь соответствует docs: health на /api/v1/health, принимает mode и version_id,
        # file_key без .pdf тоже работает. Все старые warnings убраны (2026-06-17).
    ]

    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/parser/process", "parser",
            "Запуск обработки (prepare)",
            body={"task_id": 12345,
                  "version_id": "1",
                  "file_key": "test-file-key.pdf"},
            extract_keys=["task_id"],
            response_schema={"task_id": int, "status": str},
            is_preparation=True,
            expected_status=202),
    ]

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/parser/process", "parser",
            "Запуск обработки",
            body={"task_id": 12345,
                  "version_id": "1",
                  "file_key": "test-file-key.pdf"},
            response_schema={"task_id": int, "status": str}),
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
