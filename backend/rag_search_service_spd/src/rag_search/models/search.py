from typing import Any, Literal

from pydantic import BaseModel, Field


SearchType = Literal["dense", "sparse", "hybrid"]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)
    filters: dict[str, Any] | None = None
    search_type: SearchType = "hybrid"
    expand_context: bool = False


class SearchContextItem(BaseModel):
    relation: str
    document_section_id: int | None = None
    section_id: int | None = None
    clause: str | None = None
    path: str | None = None
    page: int | None = None
    bbox: list[float] | None = None
    chunk_type: str | None = None
    content: str


class SearchResultItem(BaseModel):
    chunk_id: int
    document_id: int
    document_version_id: int | None = None
    document_section_id: int | None = None
    section_id: int | None = None
    clause: str | None = None
    path: str | None = None
    page: int | None = None
    bbox: list[float] | None = None
    chunk_index: int | None = None
    chunk_type: str | None = None
    content: str
    score: float | None = None
    distance: float | None = None
    mode: str | None = None
    context: list[SearchContextItem] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    search_type_used: SearchType
    results: list[SearchResultItem]
    total_found: int
    processing_time_ms: int
    embedding_tokens: int = 0
    embedding_cost_usd: float = 0.0
    context_expanded: bool = False
