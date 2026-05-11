"""
Pydantic schemas for Validation API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class MatchStatus(str, Enum):
    """Comparison match status."""

    MATCH = "match"
    POSSIBLE_DISCREPANCY = "possible_discrepancy"
    NOT_FOUND_IN_PROJECT = "not_found_in_project"
    NOT_FOUND_IN_NORM = "not_found_in_norm"
    INSUFFICIENT_DATA = "insufficient_data"


# --- POST /validate/compare ---


class CompareRequest(BaseModel):
    """Compare request."""

    normative_query: Optional[str] = None
    project_document_id: Optional[str] = None
    normative_fragment_id: Optional[str] = None
    project_fragment_id: Optional[str] = None


class CompareInitResponse(BaseModel):
    """Compare initiation response (202 Accepted)."""

    comparison_id: str
    status: str
    created_at: datetime


# --- GET /validate/compare/{comparison_id} ---


class NormativeBlock(BaseModel):
    """Normative block in comparison result."""

    document_id: str
    document_title: str
    page_number: int
    requirement_text: str


class ProjectBlock(BaseModel):
    """Project block in comparison result."""

    document_id: str
    document_title: str
    page_number: int
    parameter_text: str


class SourceReference(BaseModel):
    """Source reference."""

    document_id: str
    page: int


class CompareResultResponse(BaseModel):
    """Comparison result response."""

    comparison_id: str
    status: str
    normative_block: NormativeBlock
    project_block: ProjectBlock
    match_status: MatchStatus
    details: str
    sources: List[SourceReference]
    disclaimer: str
    processing_time_ms: int


# --- POST /validate/compare/batch ---


class CompareBatchItem(BaseModel):
    """Batch comparison item result."""

    comparison_id: str
    match_status: MatchStatus
    summary: str


class CompareBatchResponse(BaseModel):
    """Batch comparison response."""

    batch_id: str
    comparisons: List[CompareBatchItem]
    total_pairs: int
    matched: int
    discrepancies_found: int
    insufficient_data: int


# --- POST /validate/checks ---


class CheckSource(BaseModel):
    """Source reference for check item."""

    document_id: str
    page: int
    page_preview_url: Optional[str] = None
    document_url: Optional[str] = None


class CheckItem(BaseModel):
    """Individual check result item."""

    check_item_id: str
    project: str
    section: str
    parameter: str
    project_value: str
    nsi_requirement: str
    nsi_document: str
    status: str  # ok / warning / error
    comment: Optional[str] = None
    project_source: Optional[CheckSource] = None
    nsi_source: Optional[CheckSource] = None


class CheckSummary(BaseModel):
    """Summary statistics for check run."""

    ok: int
    warning: int
    error: int


class CheckRunResponse(BaseModel):
    """Response after initiating a check run."""

    check_run_id: str
    status: str
    summary: CheckSummary
    items: List[CheckItem]


# --- GET /validate/checks/{check_run_id} ---


class CheckRunStatusResponse(BaseModel):
    """Check run status."""

    check_run_id: str
    status: str
    progress_percent: float = 0.0
    created_at: datetime
    updated_at: datetime


# --- GET /validate/checks/{check_run_id}/export ---


class CheckExportResponse(BaseModel):
    """Check export response."""

    check_run_id: str
    export_url: str
    format: str
    created_at: datetime


# --- Health ---


class HealthStatus(BaseModel):
    """Health check status."""

    status: str
    version: str
    uptime_seconds: int
    services: Dict[str, str]
    database: str
    search_index: str
    ocr_queue: str
    storage: str
