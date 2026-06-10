"""
Настройка логирования для всего сервиса.
Формат: JSON в stdout.
"""
import logging
import sys
import os
from pythonjsonlogger import jsonlogger

def setup_logging(service_name: str) -> logging.Logger:
    """
    Настраивает корневой логгер: JSON-формат, stdout, уровень из LOG_LEVEL.

    Args:
        service_name: имя сервиса для поля 'name' в логах

    Returns:
        настроенный логгер с именем service_name
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Удаляем старые хендлеры
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)

    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        rename_fields={'levelname': 'severity', 'asctime': 'timestamp'},
        json_ensure_ascii=False
    )
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # Создаём логгер для сервиса
    log = logging.getLogger(service_name)
    log.info(f"Logging configured for {service_name} with level {log_level}")
    return log