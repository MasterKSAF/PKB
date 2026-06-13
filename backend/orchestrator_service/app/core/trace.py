"""
Trace ID — сквозной идентификатор для трассировки запросов.

Хранится в contextvars, пробрасывается через FastAPI middleware
и аргументы Celery-задач.
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def generate_trace_id() -> str:
    """Generate a new trace ID (UUID4)."""
    return uuid.uuid4().hex[:16]


def get_trace_id() -> str:
    """Get current trace ID from context."""
    return _trace_id.get()


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """Set trace ID in context. Generates a new one if not provided."""
    tid = trace_id or generate_trace_id()
    _trace_id.set(tid)
    return tid


def reset_trace_id() -> None:
    """Reset trace ID to empty string."""
    _trace_id.set("")


class TraceIdFilter(logging.Filter):
    """Logging filter that injects trace_id into log records.

    Usage in dictConfig:
        "filters": {
            "trace_id": {"()": "app.core.trace.TraceIdFilter"},
        }
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or "-"
        return True
