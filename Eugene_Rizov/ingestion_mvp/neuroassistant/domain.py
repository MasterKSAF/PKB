"""Domain models for document ingestion pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class CorpusLevel(str, Enum):
    """Corpus priority level."""

    level_a = "A"
    level_b = "B"
    level_c = "C"


class DocumentStatus(str, Enum):
    received = "received"
    stored = "stored"
    classified = "classified"
    preprocessed = "preprocessed"
    completed = "completed"
    completed_with_errors = "completed_with_errors"
    failed = "failed"


class PageStatus(str, Enum):
    received = "received"
    stored = "stored"
    classified = "classified"
    preprocessed = "preprocessed"
    completed = "completed"
    failed = "failed"


class ElementStatus(str, Enum):
    received = "received"
    processed = "processed"
    failed = "failed"


class PipelineScope(str, Enum):
    document = "document"
    page = "page"
    element = "element"


class PipelineStage(str, Enum):
    validate = "validate"
    store = "store"
    classify = "classify"
    preprocess = "preprocess"


class PipelineEventStatus(str, Enum):
    started = "started"
    succeeded = "succeeded"
    failed = "failed"


class PipelineError(BaseModel):
    error_type: str
    message: str
    stage: PipelineStage
    retryable: bool = False
    context: dict[str, Any] = Field(default_factory=dict)
    stacktrace: str | None = None


class PipelineEvent(BaseModel):
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    ingestion_id: str
    scope: PipelineScope
    stage: PipelineStage
    status: PipelineEventStatus
    duration_ms: int | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    error: PipelineError | None = None
    document_id: str | None = None
    page_number: int | None = None
    element_id: str | None = None


class DocumentMetadata(BaseModel):
    source: str | None = None
    corpus_level: CorpusLevel | None = None
    project_code: str | None = None
    discipline: str | None = None
    doc_type_hint: str | None = None
    version_date: str | None = None
    tags: list[str] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    doc_type: str
    language: str
    is_scan: bool | None = None
    page_count: int | None = None
    scan_quality: str | None = None
    scan_quality_reasons: list[str] = Field(default_factory=list)
    needs_preprocessing: bool = False
    title: str | None = None
    year_or_date: str | None = None
    version: str | None = None


class Document(BaseModel):
    document_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    filename: str
    content_type: str | None = None
    sha256: str
    size_bytes: int
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    status: DocumentStatus = DocumentStatus.received
    latest_ingestion_id: str | None = None


class IngestionRun(BaseModel):
    ingestion_id: str
    document_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: DocumentStatus = DocumentStatus.received
    classification: ClassificationResult | None = None
    errors: list[PipelineError] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class Page(BaseModel):
    document_id: str
    page_number: int
    status: PageStatus = PageStatus.received
    errors: list[PipelineError] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class Element(BaseModel):
    document_id: str
    page_number: int
    element_id: str
    status: ElementStatus = ElementStatus.received
    errors: list[PipelineError] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

