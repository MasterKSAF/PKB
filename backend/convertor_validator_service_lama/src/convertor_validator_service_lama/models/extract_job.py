from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from convertor_validator_service_lama.models.contracts import LlamaExtractPassName


class ExtractJobStatus(StrEnum):
    pending = "PENDING"
    running = "RUNNING"
    completed = "COMPLETED"
    failed = "FAILED"
    cancelled = "CANCELLED"


class ExtractJobSubmitResponse(BaseModel):
    job_id: str = Field(min_length=1)
    pass_name: LlamaExtractPassName
    status: ExtractJobStatus | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ExtractJobResult(BaseModel):
    job_id: str = Field(min_length=1)
    pass_name: LlamaExtractPassName
    status: ExtractJobStatus
    result: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ExtractPassRequest(BaseModel):
    parse_job_id: str = Field(min_length=1)
    pass_name: LlamaExtractPassName
    project_id: str = Field(min_length=1)
    schema_name: str | None = None
    extraction_schema: dict[str, Any] = Field(default_factory=dict)
    instructions: str | None = None
    target_pages: str | None = Field(default=None, min_length=1)
    max_pages: int | None = Field(default=None, ge=1)


class ExtractJobPollingConfig(BaseModel):
    max_attempts: int = Field(default=60, ge=1)
    interval_seconds: float = Field(default=2.0, ge=0.0)