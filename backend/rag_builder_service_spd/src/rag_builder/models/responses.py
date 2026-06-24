# src/rag_builder/models/responses.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    error: str | None = None


class IndexIssue(BaseModel):
    code: str
    message: str
    section_id: int | None = None


class IndexStats(BaseModel):
    sections: int = 0
    chunks: int = 0
    embeddings: int = 0


class IndexResponse(BaseModel):
    status: str
    document_id: int
    indexing_txn_id: str
    task_id: int | None = None


class IndexStatusResponse(BaseModel):
    document_id: int
    status: str
    indexing_txn_id: str | None = None

    chunks_count: int = 0
    has_embeddings: bool = False
    indexed_at: datetime | None = None

    index_stats: IndexStats = Field(default_factory=IndexStats)
    warnings: list[IndexIssue] = Field(default_factory=list)
    errors: list[IndexIssue] = Field(default_factory=list)

class DeleteIndexResponse(BaseModel):
    document_id: int
    deleted_count: int
    status: str


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int


class IndexingJobItem(BaseModel):
    id: int
    indexing_txn_id: str
    document_id: int
    status: str

    chunks_count: int = 0
    has_embeddings: bool = False
    indexed_at: datetime | None = None

    index_stats: dict[str, Any] = Field(default_factory=dict)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime


class IndexingJobsResponse(BaseModel):
    items: list[IndexingJobItem] = Field(default_factory=list)
    meta: PaginationMeta
