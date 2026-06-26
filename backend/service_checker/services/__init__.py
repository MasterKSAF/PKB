"""
PKB Neuroassistant — API Service Definitions.

Пакет содержит описание эндпоинтов и prepare-шагов для каждого сервиса.
Каждый модуль экспортирует:

- get_service_def() — возвращает ServiceDef с эндпоинтами и prepare-шагами
- SERVICE_KEY, PORT, DISPLAY_NAME — основные константы

Реестр SERVICE_REGISTRY: service_key → get_service_def()
"""

from __future__ import annotations

from typing import Dict, Any, Callable

from .base import ServiceDef
from . import (
    auth,
    registry,
    orchestrator,
    query,
    parser,
    ocr,
    converter_validator,
    rag_builder,
    rag_search,
    tei,
    gateway,
)

# Все ключи сервисов (для MODE_PORTS и т.д.)
SERVICE_KEYS = {
    "gateway",
    "auth",
    "orchestrator",
    "query",
    "registry",
    "converter_validator",
    "parser",
    "ocr",
    "rag_builder",
    "rag_search",
    "tei",
}

# Порты сервисов (единый источник)
MODE_PORTS: Dict[str, int] = {
    "gateway": 18080,
    "orchestrator": 18081,
    "auth": 18082,
    "query": 18083,
    "registry": 18084,
    "converter_validator": 18086,
    "parser": 18087,
    "ocr": 18088,
    "rag_builder": 18090,
    "rag_search": 18091,
    "tei": 18092,
    "minio": 19000,  # MinIO S3 API (для pipeline)
}

# Зависимости между сервисами: если сервис не отвечает, зависящие от него
# могут работать неполноценно
SERVICE_DEPENDENCIES: Dict[str, list[str]] = {
    "converter_validator": ["registry"],
    "query": ["registry"],
    "orchestrator": ["auth", "registry", "query", "converter_validator", "parser", "ocr", "rag_search"],
    "rag_builder": ["registry"],
    "rag_search": ["registry"],
    "gateway": ["auth", "orchestrator", "query", "registry"],
}

# Реестр: service_key → функция для получения ServiceDef
# Функции могут принимать mode ("real"|"mock") для выбора credentials
SERVICE_REGISTRY: Dict[str, Callable[..., ServiceDef]] = {
    "auth": auth.get_service_def,
    "registry": registry.get_service_def,
    "orchestrator": orchestrator.get_service_def,
    "query": query.get_service_def,
    "parser": parser.get_service_def,
    "ocr": ocr.get_service_def,
    "converter_validator": converter_validator.get_service_def,
    "rag_builder": rag_builder.get_service_def,
    "rag_search": rag_search.get_service_def,
    "tei": tei.get_service_def,
    "gateway": gateway.get_service_def,
}

__all__ = [
    "ServiceDef",
    "SERVICE_KEYS",
    "MODE_PORTS",
    "SERVICE_DEPENDENCIES",
    "SERVICE_REGISTRY",
]
