from typing import Any, Literal

from pydantic import BaseModel, Field

from convertor_validator_service_lama.models.extract_job import ExtractJobResult
from convertor_validator_service_lama.models.parse_job import ParseJobResult


class RichDocumentBoundary(BaseModel):
    boundary_id: str | None = None
    boundary_type: str | None = None
    title: str | None = None
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentTableOfContentsItem(BaseModel):
    item_id: str | None = None
    title: str = Field(min_length=1)
    level: int = Field(ge=0)
    page: int | None = Field(default=None, ge=0)
    path: str | None = None
    target_section_id: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentTableOfContentsBlock(BaseModel):
    toc_id: str = Field(min_length=1)
    title: str | None = None
    namespace_id: str | None = None
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    items: list[RichDocumentTableOfContentsItem] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentNestedDocument(BaseModel):
    nested_document_id: str | None = None
    document_code: str | None = None
    title: str | None = None
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    parent_boundary_id: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)



class RichDocumentNamespace(BaseModel):
    namespace_id: str = Field(min_length=1)
    title: str | None = None
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    start_heading_id: str | None = None
    start_item_index: int | None = Field(default=None, ge=0)
    end_item_index_exclusive: int | None = Field(default=None, ge=0)
    ordinal: int | None = Field(default=None, ge=1)
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentImage(BaseModel):
    image_id: str | None = None
    caption: str | None = None
    alt_text: str | None = None
    # Legacy ambiguous page field kept for compatibility.
    page: int | None = Field(default=None, ge=0)
    # Citation code should prefer file_page_number/file_page_index.
    file_page_number: int | None = Field(default=None, ge=1)
    file_page_index: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = None
    bbox: list[float] | None = None
    storage_uri: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentFormula(BaseModel):
    formula_id: str | None = None
    expression: str | None = None
    latex: str | None = None
    # Legacy ambiguous page field kept for compatibility.
    page: int | None = Field(default=None, ge=0)
    # Citation code should prefer file_page_number/file_page_index.
    file_page_number: int | None = Field(default=None, ge=1)
    file_page_index: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = None
    bbox: list[float] | None = None
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentTableCell(BaseModel):
    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)
    text: str | None = None
    markdown: str | None = None
    images: list[RichDocumentImage] = Field(default_factory=list)
    formulas: list[RichDocumentFormula] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentTable(BaseModel):
    table_id: str | None = None
    caption: str | None = None
    # Legacy ambiguous page field kept for compatibility.
    page: int | None = Field(default=None, ge=0)
    # Citation code should prefer file_page_number/file_page_index.
    file_page_number: int | None = Field(default=None, ge=1)
    file_page_index: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = None
    bbox: list[float] | None = None
    cells: list[RichDocumentTableCell] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentSection(BaseModel):
    section_id: str | None = None
    parent_section_id: str | None = None
    clause: str | None = None
    title: str | None = None
    level: int | None = Field(default=None, ge=0)
    path: str | None = None
    # Backward-compatible aliases for file_page_start/file_page_end.
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    file_page_start: int | None = Field(default=None, ge=1)
    file_page_end: int | None = Field(default=None, ge=1)
    file_page_index_start: int | None = Field(default=None, ge=0)
    file_page_index_end: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = None
    bbox: list[float] | None = None
    section_type: str | None = None
    content: Any | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentNote(BaseModel):
    note_id: str | None = None
    namespace_id: str | None = None
    section_id: str | None = None
    text: str | None = None
    # Legacy ambiguous page field kept for compatibility.
    page: int | None = Field(default=None, ge=0)
    # Citation code should prefer file_page_number/file_page_index.
    file_page_number: int | None = Field(default=None, ge=1)
    file_page_index: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = None
    bbox: list[float] | None = None
    raw: dict[str, Any] = Field(default_factory=dict)



class RichDocumentReference(BaseModel):
    reference_id: str | None = None
    namespace_id: str | None = None
    section_id: str | None = None
    reference_text: str | None = None
    target_document_code: str | None = None
    target_document_codes: list[str] = Field(default_factory=list)
    target_clause: str | None = None
    reference_type: str | None = None
    # Legacy ambiguous page field kept for compatibility.
    page: int | None = Field(default=None, ge=0)
    # Citation code should prefer file_page_number/file_page_index.
    file_page_number: int | None = Field(default=None, ge=1)
    file_page_index: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = None
    bbox: list[float] | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentCrossReference(BaseModel):
    reference_id: str | None = None
    source_id: str | None = None
    target_id: str | None = None
    target_document_code: str | None = None
    reference_type: str | None = None
    context: str | None = None
    note: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RichDocumentStructure(BaseModel):
    namespaces: list[RichDocumentNamespace] = Field(default_factory=list)
    document_boundaries: list[RichDocumentBoundary] = Field(default_factory=list)
    table_of_contents_blocks: list[RichDocumentTableOfContentsBlock] = Field(
        default_factory=list
    )
    table_of_contents: list[RichDocumentTableOfContentsItem] = Field(default_factory=list)
    nested_documents: list[RichDocumentNestedDocument] = Field(default_factory=list)

    sections: list[RichDocumentSection] = Field(default_factory=list)
    tables: list[RichDocumentTable] = Field(default_factory=list)
    images: list[RichDocumentImage] = Field(default_factory=list)
    formulas: list[RichDocumentFormula] = Field(default_factory=list)
    notes: list[RichDocumentNote] = Field(default_factory=list)
    references: list[RichDocumentReference] = Field(default_factory=list)
    cross_references: list[RichDocumentCrossReference] = Field(default_factory=list)

    quality_report: dict[str, Any] | None = None
    correction_proposals: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class RichDocumentPackageArtifact(BaseModel):
    artifact_key: str = Field(min_length=1)
    produced_by: str = Field(min_length=1)
    source: Literal["parse_result", "extract_pass", "python_validator"]
    content: Any | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class RichDocumentPackage(BaseModel):
    package_name: str = "rich_document_package.json"
    parse_job_id: str = Field(min_length=1)
    source_pdf_path: str | None = None
    document_code: str | None = None
    parse_result: ParseJobResult
    extract_results: dict[str, ExtractJobResult] = Field(default_factory=dict)
    artifacts: dict[str, RichDocumentPackageArtifact] = Field(default_factory=dict)
    document_structure: RichDocumentStructure = Field(default_factory=RichDocumentStructure)
    final_correction_policy: str = "python_validator_assembler_applies_final_corrections"


class RichDocumentPackageAssemblyRequest(BaseModel):
    source_pdf_path: str | None = None
    document_code: str | None = None
    parse_result: ParseJobResult
    extract_results: dict[str, ExtractJobResult] = Field(default_factory=dict)


class RichDocumentPackageAssemblyResult(BaseModel):
    package: RichDocumentPackage
    artifact_count: int = Field(ge=0)
