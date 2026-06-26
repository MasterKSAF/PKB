"""
Structured JSON logging for Gateway Service (P11-1, P11-2, P11-3).

Формат каждой записи лога (JSON):
  - timestamp, level, service, trace_id, span_id, request_id, user_id,
    path, method, status, latency_ms, message, error_code, error_message, extra

PII-фильтрация (P11-1): password, access_token, refresh_token маскируются.
"""

import json
import logging
import logging.handlers
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

# ---------------------------------------------------------------------------
# PII fields для маскирования
# ---------------------------------------------------------------------------

DEFAULT_PII_FIELDS: Set[str] = {"password", "access_token", "refresh_token"}


def _parse_pii_fields(env_value: str | None) -> Set[str]:
    """Парсит LOG_PII_FIELDS из переменной окружения (через запятую)."""
    if not env_value:
        return DEFAULT_PII_FIELDS
    return {f.strip().lower() for f in env_value.split(",") if f.strip()}


PII_FIELDS: Set[str] = _parse_pii_fields(os.getenv("LOG_PII_FIELDS"))

# Паттерн для маскирования PII-полей в JSON-телах
_PII_KEY_PATTERN = re.compile(
    r'"(' + '|'.join(re.escape(f) for f in PII_FIELDS) + r')"\s*:\s*"[^"]*"',
    re.IGNORECASE,
)


def mask_pii_in_text(text: str) -> str:
    """Маскирует значения PII-полей в тексте (для логов)."""
    return _PII_KEY_PATTERN.sub(r'"\1":"***"', text)


# ---------------------------------------------------------------------------
# JSON Log Formatter
# ---------------------------------------------------------------------------


class JSONLogFormatter(logging.Formatter):
    """Сериализует log-запись в JSON со стандартными полями Gateway."""

    def format(self, record: logging.LogRecord) -> str:
        # Формируем timestamp вручную: strftime не поддерживает миллисекунды с ведущими нулями
        base_ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        frac = f"{record.created % 1:.3f}"[2:5]
        timestamp = f"{base_ts}.{frac}Z"
        log_entry: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "service": "gateway",
            "trace_id": getattr(record, "trace_id", None),
            "span_id": getattr(record, "span_id", None),
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "path": getattr(record, "req_path", None),
            "method": getattr(record, "req_method", None),
            "status": getattr(record, "req_status", None),
            "latency_ms": getattr(record, "latency_ms", None),
            "message": record.getMessage(),
            "error_code": getattr(record, "error_code", None),
            "error_message": getattr(record, "error_message", None),
            "extra": getattr(record, "extra", None),
        }
        # Удаляем None-поля для компактности
        cleaned = {k: v for k, v in log_entry.items() if v is not None}
        text = json.dumps(cleaned, ensure_ascii=False, default=str)
        return mask_pii_in_text(text)


# ---------------------------------------------------------------------------
# PII Filter — не пропускает сырые значения PII в лог
# ---------------------------------------------------------------------------


class PIIFilter(logging.Filter):
    """Удаляет/маскирует PII-поля из log-записи."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        # Если сообщение содержит незамаскированные PII — заменяем
        for field in PII_FIELDS:
            pattern = re.compile(
                rf'"{re.escape(field)}"\s*:\s*"[^"]*"', re.IGNORECASE
            )
            if pattern.search(msg):
                # Уже обработано в JSONLogFormatter.formatter для JSON-формата
                pass
        return True


# ---------------------------------------------------------------------------
# Setup function
# ---------------------------------------------------------------------------


def setup_logging() -> None:
    """Настраивает корневой логгер со структурированным JSON-выводом.

    Должна быть вызвана один раз при старте Gateway.
    """
    level_name = os.getenv("GATEWAY_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Удаляем существующие handlers (чтобы не дублировать при reload)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(JSONLogFormatter())
    handler.addFilter(PIIFilter())

    root_logger.addHandler(handler)

    # Логгер gateway — дочерний, наследует handler
    gw_logger = logging.getLogger("gateway")
    gw_logger.setLevel(level)

    # Отключаем лишнее логирование от внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    gw_logger.info("Structured JSON logging started", extra={"level": "INFO"})
