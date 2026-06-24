# rag_builder_service_spd/src/rag_builder/models/search.py

from typing import Literal, Any

from pydantic import BaseModel, Field, field_validator


class SearchFilters(BaseModel):
    """
    Минимальные фильтры MVP.

    Только поля, которые реально есть в nsi.chunks.
    """
    document_id: int | None = None
    document_version_id: int | None = None
    section_id: int | None = None
    chunk_type: str | None = None


class SearchRequest(BaseModel):
    """
    Запрос RAG Search MVP.

    Пока реально поддерживаем только dense search.
    Поля search_type и expand_context оставлены как архитектурный задел.
    """
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    filters: SearchFilters | None = None
    search_type: Literal["dense", "sparse", "hybrid"] = "dense"
    expand_context: bool = False

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("query must not be empty")
        return normalized

class SearchContextItem(BaseModel):
    """
    Context item returned by context expansion.

    MVP uses document_sections hierarchy:
    parent and direct children of the found chunk section.
    """
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
    """
    Один найденный chunk.

    Важно: возвращаем данные, достаточные для точной citation:
    document_id + document_version_id + clause + page + content.
    """
    chunk_id: int

    document_id: int
    document_version_id: int

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
    context: list[SearchContextItem] = Field(default_factory=list)




class SearchResponse(BaseModel):
    query: str
    search_type_used: Literal["dense", "sparse", "hybrid"]
    results: list[SearchChunkResult]

    total_found: int
    processing_time_ms: int

    embedding_tokens: int = 0
    embedding_cost_usd: float = 0.0

    context_expanded: bool = False