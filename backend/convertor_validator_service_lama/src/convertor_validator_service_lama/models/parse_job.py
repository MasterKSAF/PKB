from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ParseJobStatus(StrEnum):
    pending = "PENDING"
    running = "RUNNING"
    completed = "COMPLETED"
    failed = "FAILED"
    cancelled = "CANCELLED"


class ParseJobSubmitResponse(BaseModel):
    job_id: str = Field(min_length=1)
    status: ParseJobStatus | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ParseJobResult(BaseModel):
    job_id: str = Field(min_length=1)
    status: ParseJobStatus
    markdown: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    job_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ParseJobPollingConfig(BaseModel):
    max_attempts: int = Field(default=60, ge=1)
    interval_seconds: float = Field(default=2.0, ge=0.0)