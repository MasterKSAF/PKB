from __future__ import annotations

from typing import Any

from convertor_validator_service_lama.models.contracts import (
    RagBuilderClientError,
)


def build_rag_builder_client_error(
    *,
    status_code: int,
    detail: Any,
) -> RagBuilderClientError:
    if isinstance(detail, dict):
        code = _as_non_empty_str(detail.get("code"), default="RAG_BUILDER_ERROR")
        message = _as_non_empty_str(detail.get("message"), default=code)
        details = detail.get("details")

        return RagBuilderClientError(
            status_code=status_code,
            code=code,
            message=message,
            details=details if isinstance(details, dict) else {},
        )

    if isinstance(detail, str) and detail.strip():
        return RagBuilderClientError(
            status_code=status_code,
            code="RAG_BUILDER_ERROR",
            message=detail.strip(),
            details={},
        )

    return RagBuilderClientError(
        status_code=status_code,
        code="RAG_BUILDER_ERROR",
        message="RAG Builder request failed",
        details={},
    )


def _as_non_empty_str(value: Any, *, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return default
