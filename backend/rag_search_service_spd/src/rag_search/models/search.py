from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


SearchType = Literal["dense", "sparse", "hybrid"]


class SearchFilters(BaseModel):
    document_id: int | None = None
    section_id: int | None = None
    chunk_type: str | None = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    filters: SearchFilters | None = None
    search_type: SearchType = "hybrid"
    expand_context: bool = False

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("query must not be empty")
        return normalized


class SearchContextItem(BaseModel):
    relation: Literal["parent", "child"]

    document_section_id: int
    section_id: int
    parent_id: int | None = None

    clause: str | None = None
    title: str | None = None
    path: str
    page: int | None = None

    section_type: str
    content: Any | None = None


class SearchChunkResult(BaseModel):
    chunk_id: int

    document_id: int

    document_section_id: int
    section_id: int

    clause: str | None = None
    path: str | None = None
    page: int | None = None
    bbox: Any | None = None

    chunk_index: int
    chunk_type: str
    content: str

    score: float
    distance: float | None = None
    mode: str | None = None
    context: list[SearchContextItem] = Field(default_factory=list)


SearchResultItem = SearchChunkResult


class SearchResponse(BaseModel):
    query: str
    search_type_used: SearchType
    results: list[SearchChunkResult]

    total_found: int
    processing_time_ms: int

    embedding_tokens: int = 0
    embedding_cost_usd: float = 0.0

    context_expanded: bool = False
