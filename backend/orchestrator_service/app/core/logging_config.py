"""
Logging configuration for Orchestrator Service.

Provides structured logging with consistent formatting across all modules.
Includes trace_id injection for request tracing.
"""

import logging
import logging.config
from typing import Optional

from app.core.trace import TraceIdFilter


def setup_logging(debug: bool = False, log_file: Optional[str] = None) -> None:
    """Configure root logger with consistent format and level.

    Args:
        debug: If True, set level to DEBUG; otherwise INFO.
        log_file: Optional path to a log file. If None, logs go to stdout only.
    """
    level = logging.DEBUG if debug else logging.INFO

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
            "filters": ["trace_id"],
        },
    }

    if log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "standard",
            "filters": ["trace_id"],
        }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "trace_id": {
                    "()": TraceIdFilter,
                },
            },
            "formatters": {
                "standard": {
                    "format": (
                        "%(asctime)s | %(trace_id)-16s | %(name)-28s | "
                        "%(levelname)-8s | %(message)s"
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "detailed": {
                    "format": (
                        "%(asctime)s | %(trace_id)-16s | %(name)-28s | "
                        "%(levelname)-8s | %(message)s | [%(filename)s:%(lineno)d]"
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": handlers,
            "root": {
                "level": level,
                "handlers": list(handlers.keys()),
            },
            "loggers": {
                # Our application loggers
                "orchestrator": {"level": level, "propagate": True},
                "tasks": {"level": level, "propagate": True},
                "services": {"level": level, "propagate": True},
                # Third-party loggers — keep at WARN to reduce noise
                "httpx": {"level": "WARNING", "propagate": True},
                "httpcore": {"level": "WARNING", "propagate": True},
                "sqlalchemy.engine": {
                    "level": "WARNING" if not debug else "INFO",
                    "propagate": True,
                },
                "celery": {"level": "WARNING", "propagate": True},
                "uvicorn": {"level": "INFO", "propagate": True},
                "uvicorn.access": {"level": "INFO", "propagate": True},
            },
        }
    )
