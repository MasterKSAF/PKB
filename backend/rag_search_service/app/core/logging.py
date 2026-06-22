"""Структурированное логирование с PII-фильтром и OpenTelemetry."""

from __future__ import annotations

import logging
import os
import sys

from app.config import get_settings


class PIIFilter(logging.Filter):
    """Маскирует чувствительные поля в логах."""

    def __init__(self, pii_fields: list[str]):
        super().__init__()
        self.pii_fields = {f.lower() for f in pii_fields}

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "__dict__"):
            for key in list(record.__dict__.keys()):
                if key.lower() in self.pii_fields:
                    record.__dict__[key] = "***"
        if isinstance(record.msg, dict):
            for field in self.pii_fields:
                if field in record.msg:
                    record.msg[field] = "***"
        return True


def setup_logging() -> logging.Logger:
    """Инициализация логгера сервиса с OTLP-экспортом (если настроен)."""
    settings = get_settings()

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if otlp_endpoint:
        from app.core.telemetry import setup_observability

        _, _, root_logger = setup_observability(
            service_name=settings.service_name,
            otlp_endpoint=otlp_endpoint,
        )
    else:
        # Fallback: JSON-логирование в stdout без OTLP
        try:
            from pythonjsonlogger import jsonlogger

            json_formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                rename_fields={"levelname": "severity", "asctime": "timestamp"},
                json_ensure_ascii=False,
            )
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(json_formatter)
        except ImportError:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )

        root_logger = logging.getLogger()
        root_logger.setLevel(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        )
        root_logger.handlers.clear()
        root_logger.addHandler(handler)

    # PII-фильтр на корневом логгере
    root_logger.addFilter(PIIFilter(settings.pii_fields_list))

    # Снижаем шум от сторонних библиотек
    for noisy in ["httpx", "httpcore", "urllib3"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logger = logging.getLogger(settings.service_name)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Получить логгер с префиксом сервиса."""
    settings = get_settings()
    prefix = settings.service_name
    return logging.getLogger(f"{prefix}.{name}" if name else prefix)
