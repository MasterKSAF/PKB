"""API schemas (requests/responses)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from neuroassistant.domain import ClassificationResult
from neuroassistant.domain import DocumentMetadata
from neuroassistant.domain import DocumentStatus
from neuroassistant.domain import PipelineError


class UploadResponse(BaseModel):
    document_id: str
    ingestion_id: str
    status_url: str
    report_url: str


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str | None
    sha256: str
    size_bytes: int
    created_at: datetime
    metadata: DocumentMetadata
    status: DocumentStatus
    latest_ingestion_id: str | None


class RunResponse(BaseModel):
    ingestion_id: str
    document_id: str
    created_at: datetime
    status: DocumentStatus
    classification: ClassificationResult | None
    errors: list[PipelineError] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class UsageReport(BaseModel):
    documents_total: int
    runs_total: int
    documents_by_status: dict[str, int]
    runs_by_status: dict[str, int]
    latest_ingestions: list[RunResponse]

