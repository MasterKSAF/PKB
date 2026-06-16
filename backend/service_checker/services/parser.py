"""
PKB Neuroassistant — Parser Service API Definitions.

Основано на: docs/api/parser_service_api.md

Замечание: документация описывает единый POST /parser/process с полем mode,
реальная реализация разделяет на process (version_id) и preview (отдельный endpoint).
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
        "⚠️ Реальная реализация расходится с docs: process требует version_id (docs: mode+file_key).",
        "⚠️ Health Parser на /health, а не /api/v1/health — сервис не использует префикс.",
        "⚠️ Валидатор Parser проверяет расширение file_key (не принимает без .pdf). "
        "Реальные file_key — хэши без расширения, нужна проверка по MIME/содержимому.",
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
        EndpointDef("GET", "/health", "health", "Health check сервиса",
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
