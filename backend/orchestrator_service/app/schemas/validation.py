"""
Pydantic schemas for Validation API.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MatchStatus(str, Enum):
    """Comparison match status."""
    MATCH = "match"
    POSSIBLE_DISCREPANCY = "possible_discrepancy"
    NOT_FOUND_IN_PROJECT = "not_found_in_project"
    NOT_FOUND_IN_NORM = "not_found_in_norm"
    INSUFFICIENT_DATA = "insufficient_data"


class CompareRequest(BaseModel):
    """Compare request (variant 1 - by query)."""
    normative_query: Optional[str] = None
    project_document_id: Optional[str] = None
    normative_fragment_id: Optional[str] = None
    project_fragment_id: Optional[str] = None


class CompareInitResponse(BaseModel):
    """Compare initiation response."""
    comparison_id: str
    status: str
    created_at: datetime


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


class HealthStatus(BaseModel):
    """Health check status."""
    status: str
    version: str
    uptime_seconds: int
    services: Dict[str, str]
