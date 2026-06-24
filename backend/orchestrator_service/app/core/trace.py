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
_user_id: ContextVar[str] = ContextVar("user_id", default="")
_draft_id: ContextVar[str] = ContextVar("draft_id", default="")
_document_id: ContextVar[str] = ContextVar("document_id", default="")
_version_id: ContextVar[str] = ContextVar("version_id", default="")


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
    """Reset trace ID and all correlation IDs to empty."""
    _trace_id.set("")
    _user_id.set("")
    _draft_id.set("")
    _document_id.set("")
    _version_id.set("")


# --- Correlation IDs (CM-5) ---


def set_user_id(user_id: str) -> None:
    """Set X-User-ID in context."""
    _user_id.set(user_id)


def get_user_id() -> str:
    """Get current X-User-ID from context."""
    return _user_id.get()


def set_draft_id(draft_id: str) -> None:
    """Set X-Draft-ID in context."""
    _draft_id.set(str(draft_id))


def get_draft_id() -> str:
    """Get current X-Draft-ID."""
    return _draft_id.get()


def set_document_id(document_id: str) -> None:
    """Set X-Document-ID in context."""
    _document_id.set(str(document_id))


def get_document_id() -> str:
    """Get current X-Document-ID."""
    return _document_id.get()


def set_version_id(version_id: str) -> None:
    """Set X-Version-ID in context."""
    _version_id.set(str(version_id))


def get_version_id() -> str:
    """Get current X-Version-ID."""
    return _version_id.get()


def build_correlation_headers() -> dict:
    """Build correlation headers from current trace context (CM-5)."""
    headers = {}
    tid = get_trace_id()
    if tid:
        headers["X-Trace-ID"] = tid
        headers["X-Request-ID"] = tid
    uid = get_user_id()
    if uid:
        headers["X-User-ID"] = uid
    did = get_draft_id()
    if did:
        headers["X-Draft-ID"] = did
    doc_id = get_document_id()
    if doc_id:
        headers["X-Document-ID"] = doc_id
    vid = get_version_id()
    if vid:
        headers["X-Version-ID"] = vid
    return headers


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
