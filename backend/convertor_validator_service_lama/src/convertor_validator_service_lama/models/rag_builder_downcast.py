from typing import Any

from pydantic import BaseModel, Field


class RagBuilderDowncastWarning(BaseModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    source_artifact: str | None = None


class RagBuilderPayloadMetadata(BaseModel):
    schema_name: str = "rag_builder_compatible_payload"
    source_package_name: str = "rich_document_package.json"
    generated_by: str = "convertor_validator_service_lama"
    notes: list[str] = Field(default_factory=list)


class RagBuilderDocumentPayload(BaseModel):
    document_code: str | None = None
    title: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    source_pdf_path: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class RagBuilderSectionPayload(BaseModel):
    section_id: str = Field(min_length=1)
    title: str | None = None
    text: str | None = None
    level: int | None = Field(default=None, ge=0)
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    path: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RagBuilderTablePayload(BaseModel):
    table_id: str = Field(min_length=1)
    caption: str | None = None
    page: int | None = Field(default=None, ge=0)
    raw: dict[str, Any] = Field(default_factory=dict)


class RagBuilderImagePayload(BaseModel):
    image_id: str = Field(min_length=1)
    caption: str | None = None
    page: int | None = Field(default=None, ge=0)
    raw: dict[str, Any] = Field(default_factory=dict)


class RagBuilderFormulaPayload(BaseModel):
    formula_id: str = Field(min_length=1)
    expression: str | None = None
    page: int | None = Field(default=None, ge=0)
    raw: dict[str, Any] = Field(default_factory=dict)


class RagBuilderCrossReferencePayload(BaseModel):
    reference_id: str = Field(min_length=1)
    source: str | None = None
    target: str | None = None
    reference_type: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RagBuilderCompatiblePayload(BaseModel):
    metadata: RagBuilderPayloadMetadata = Field(default_factory=RagBuilderPayloadMetadata)
    document: RagBuilderDocumentPayload = Field(default_factory=RagBuilderDocumentPayload)
    sections: list[RagBuilderSectionPayload] = Field(default_factory=list)
    tables: list[RagBuilderTablePayload] = Field(default_factory=list)
    images: list[RagBuilderImagePayload] = Field(default_factory=list)
    formulas: list[RagBuilderFormulaPayload] = Field(default_factory=list)
    cross_references: list[RagBuilderCrossReferencePayload] = Field(default_factory=list)


class RagBuilderDowncastResult(BaseModel):
    payload: RagBuilderCompatiblePayload
    warnings: list[RagBuilderDowncastWarning] = Field(default_factory=list)