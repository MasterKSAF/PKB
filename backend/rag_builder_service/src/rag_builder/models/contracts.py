from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

SectionType = Literal["text", "textBlock", "headerFooter", "table", "list", "image", "formula"]


class MetadataBlock(BaseModel):
    schema_name: str = Field(alias="schema")
    document_id: int
    created_at: datetime


class DocumentBlock(BaseModel):
    id: int
    doc_code: str | None = None
    title: str | None = None
    full_title: str | None = None
    normalized_title: str | None = None
    group: str | None = None
    mks_oks_code: str | None = None
    okstu: str | None = None
    udc: str | None = None
    era: str | None = None
    validity_status: str | None = None
    issuing_body: str | None = None
    adoption_date: str | None = None
    adoption_authority: str | None = None
    adoption_document_number: str | None = None
    effective_from: str | None = None
    replaces: str | None = None
    validity_restriction_removed_date: str | None = None
    validity_restriction_removed_authority: str | None = None
    validity_restriction_removed_document_number: str | None = None
    status_note: str | None = None
    page_count: int | None = None
    file_hash_sha256: str | None = None
    amendments: list[dict[str, Any]] = Field(default_factory=list)
    references: list[dict[str, Any]] = Field(default_factory=list)


class TerminologyItem(BaseModel):
    term: str
    definition: str
    source_clause: str | None = None
    normalized_term: str | None = None


class ProtectedSpan(BaseModel):
    section_id: int
    start_offset: int
    end_offset: int


class Section(BaseModel):
    section_id: int
    document_id: int
    parent_id: int | None = None
    clause: str | None = None
    title: str | None = None
    level: int
    path: str
    page: int | None = None
    bbox: list[float] | None = None
    type: SectionType
    content: dict[str, Any]
    created_at: datetime | None = None

    @model_validator(mode="after")
    def validate_page_is_1_based(self) -> "Section":
        if self.page is not None and self.page < 1:
            raise ValueError(f"page must be 1-based, got {self.page}")
        return self


class BuildRequest(BaseModel):
    document_id: int | None = None
    metadata: MetadataBlock | None = None
    document: DocumentBlock | None = None
    sections: list[Section]
    terminology: list[TerminologyItem] = Field(default_factory=list)
    protected_spans: list[ProtectedSpan] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_and_normalize_document_id(self) -> "BuildRequest":
        effective = self.document_id
        if effective is None and self.metadata is not None:
            effective = self.metadata.document_id
        if effective is None and self.document is not None:
            effective = self.document.id
        if effective is None:
            raise ValueError("document_id is required (root, metadata.document_id or document.id)")

        if self.metadata is not None and self.metadata.document_id != effective:
            raise ValueError("metadata.document_id must match document_id")
        if self.document is not None and self.document.id != effective:
            raise ValueError("document.id must match document_id")
        for section in self.sections:
            if section.document_id != effective:
                raise ValueError("section.document_id must match document_id")

        self.document_id = effective
        return self

    @model_validator(mode="after")
    def validate_section_ids_unique(self) -> "BuildRequest":
        seen = set()
        for s in self.sections:
            if s.section_id in seen:
                raise ValueError(f"duplicate section_id {s.section_id}")
            seen.add(s.section_id)
        return self

    @model_validator(mode="after")
    def validate_parent_id_refers_to_existing_section(self) -> "BuildRequest":
        section_ids = {s.section_id for s in self.sections}
        for s in self.sections:
            if s.parent_id is not None and s.parent_id not in section_ids:
                raise ValueError(
                    f"parent_id {s.parent_id} refers to non-existent section_id in request"
                )
        return self


class BuildResponse(BaseModel):
    document_id: int
    status: Literal["pending", "indexed", "failed"]
    indexed_at: datetime | None = None
    chunks_count: int
    index_stats: dict[str, int]
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DeleteResponse(BaseModel):
    document_id: int
    deleted_count: int
    status: Literal["completed"]


class StatusResponse(BaseModel):
    document_id: int
    status: Literal["pending", "indexing", "indexed", "failed"]
    chunks_count: int
    has_embeddings: bool
    indexed_at: datetime | None = None



