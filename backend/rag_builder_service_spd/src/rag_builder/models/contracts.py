# src/rag_builder/models/contracts.py

from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


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
    document_version_id: int | None = None


class DocumentBlock(BaseModel):
    id: int
    document_version_id: int | None = None

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

    @model_validator(mode="after")
    def fill_legacy_document_version_id(self) -> "BuildRequest":
        """
        document_version_id больше не является обязательным
        входным полем RAG Builder.

        Для обратной совместимости с текущими Chunk/DB/Search
        временно заполняем legacy/audit document_version_id:

        1. metadata.document_version_id
        2. document.document_version_id
        3. metadata.document_id
        """

        document_version_id = self.metadata.document_version_id

        if document_version_id is None:
            document_version_id = self.document.document_version_id

        if document_version_id is None:
            document_version_id = self.metadata.document_id

        self.metadata.document_version_id = document_version_id
        self.document.document_version_id = document_version_id

        return self