# src/rag_builder/models/contracts.py

from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

# SectionType = Literal[
#     "section",
#     "table",
#     "image",
#     "formula"
# ]

SectionType = Literal[
    "headerFooter",
    "text",
    "textBlock",
    "table",
    "list",
    "image",
    "formula",
]

class MetadataBlock(BaseModel):
    schema_name: str = Field(alias="schema")
    document_id: int
    document_version_id: int


class DocumentBlock(BaseModel):
    id: int
    document_version_id: int

    pkb_code: str
    doc_code: str

    title: str
    full_title: str | None = None
    normalized_title: str | None = None

    validity_status: str | None = None
    era: str | None = None

    page_count: int | None = None

    file_hash_sha256: str | None = None


class ReferenceItem(BaseModel):
    target_document_id: int | None = None
    target_doc_code: str

    type: str
    context: str | None = None
    note: str | None = None


class Section(BaseModel):
    section_id: int

    parent_id: int | None = None

    clause: str | None = None
    title: str | None = None

    level: int
    path: str

    page: int | None = None

    bbox: list[float] | None = None

    type: SectionType

    content: dict[str, Any]

    references: list[ReferenceItem] = Field(default_factory=list)


class BuildRequest(BaseModel):
    metadata: MetadataBlock
    document: DocumentBlock

    sections: list[Section]

    terminology: list[dict[str, Any]] = Field(default_factory=list)

    options: dict[str, Any] = Field(default_factory=dict)
