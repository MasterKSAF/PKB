"""
PKB Neuroassistant — TEI (Text Embeddings Inference) API Definitions.

Основано на: docs/api/common_api.md
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
)

SERVICE_KEY = "tei"
PORT = 18092
DISPLAY_NAME = "TEI (Embeddings)"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание TEI сервиса."""

    endpoints = [
        EndpointDef("GET", "/", "health", "Health check TEI сервера"),
        EndpointDef("POST", "/embed", "embed", "Получить эмбеддинги",
            body={"inputs": "Тестовый запрос для эмбеддинга"},
            # TEI возвращает чистый массив [[float]], а не объект с ключом
            # response_schema={"embedding": list}
        ),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,
        endpoints=endpoints,
        prepare_endpoints=[],
        depends_on=[],
        base_data={},
    )
