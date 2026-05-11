"""
Pydantic schemas for Search and RAG API.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Search filters."""
    document_type: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request."""
    query: str
    document_ids: Optional[List[str]] = None
    top_k: int = 5
    filters: Optional[SearchFilters] = None


class SearchResultFragment(BaseModel):
    """Search result fragment."""
    fragment_id: str
    document_id: str
    document_title: str
    page_number: int
    text: str
    coordinates: Optional[Dict[str, int]] = None
    score: float
    document_type: str


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    results: List[SearchResultFragment]
    total_found: int
    processing_time_ms: int


class SearchQueryParams(BaseModel):
    """GET search query parameters."""
    q: str
    document_id: Optional[str] = None
    page: int = 1
    limit: int = 10


class AskOptions(BaseModel):
    """Ask options."""
    temperature: Optional[float] = 0.2


class AskRequest(BaseModel):
    """Ask request."""
    question: str
    document_ids: Optional[List[str]] = None
    options: Optional[AskOptions] = None


class AskSource(BaseModel):
    """Ask response source."""
    document_id: str
    document_title: str
    page_number: int
    fragment_id: str
    text: str
    score: float


class AskResponse(BaseModel):
    """Ask response."""
    question: str
    answer: str
    sources: List[AskSource]
    processing_time_ms: int
    model_used: str
