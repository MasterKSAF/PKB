"""Структурированное логирование с PII-фильтром."""

from __future__ import annotations

import logging
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
        # Также маскируем в сообщении, если там есть чувствительные данные
        if isinstance(record.msg, dict):
            for field in self.pii_fields:
                if field in record.msg:
                    record.msg[field] = "***"
        return True


def setup_logging() -> logging.Logger:
    """Инициализация корневого логгера сервиса."""
    settings = get_settings()

    # Настраиваем базовый формат
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    logger = logging.getLogger(settings.service_name)
    logger.addFilter(PIIFilter(settings.pii_fields_list))

    # Снижаем шум от сторонних библиотек
    for noisy in [
        "httpx",
        "httpcore",
        "urllib3",
        "sentence_transformers",
        "transformers",
        "huggingface_hub",
    ]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Получить логгер с префиксом сервиса."""
    settings = get_settings()
    prefix = settings.service_name
    return logging.getLogger(f"{prefix}.{name}" if name else prefix)