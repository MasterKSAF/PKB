from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

SectionType = Literal["section", "table", "image", "formula"]


class ProtectedSpan(BaseModel):
    section_id: int
    start_offset: int
    end_offset: int


class Section(BaseModel):
    section_id: int
    document_id: UUID
    clause: str | None = None
    title: str | None = None
    level: int
    path: str
    page: int | None = None
    type: SectionType
    content: dict[str, Any]


class BuildRequest(BaseModel):
    document_id: UUID
    sections: list[Section]
    protected_spans: list[ProtectedSpan] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)


class BuildResponse(BaseModel):
    document_id: UUID
    status: Literal["completed", "failed"]
    indexed_at: datetime
    chunks_count: int
    index_stats: dict[str, int]


class DeleteResponse(BaseModel):
    document_id: UUID
    deleted_count: int
    status: Literal["completed"]


class StatusResponse(BaseModel):
    document_id: UUID
    status: Literal["pending", "indexing", "indexed", "failed"]
    chunks_count: int
    has_embeddings: bool
    indexed_at: datetime | None = None
