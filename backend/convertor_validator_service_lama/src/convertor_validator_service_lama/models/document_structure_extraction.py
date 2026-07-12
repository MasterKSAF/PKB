from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictExtractionModel(BaseModel):
    """Base model for LlamaExtract structured outputs.

    extra="forbid" is intentional: the agent must follow the contract exactly.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DocumentProfile(str, Enum):
    SIMPLE_STANDARD = "simple_standard"
    COMPOUND_RULES = "compound_rules"
    TABLE_HEAVY_STANDARD = "table_heavy_standard"
    DRAWING_OR_FORMULA_STANDARD = "drawing_or_formula_standard"
    UNKNOWN = "unknown"


class NumberingScopeType(str, Enum):
    MAIN_DOCUMENT = "main_document"
    FRONT_MATTER = "front_matter"
    TABLE_OF_CONTENTS = "table_of_contents"
    INTRODUCTION = "introduction"
    CLASSIFICATION = "classification"
    APPENDIX = "appendix"
    PART = "part"
    SECTION_GROUP = "section_group"
    UNKNOWN = "unknown"


class ItemRole(str, Enum):
    BODY_TEXT = "body_text"
    HEADING = "heading"
    NORMATIVE_CLAUSE = "normative_clause"
    CLAUSE_CONTINUATION = "clause_continuation"
    TABLE = "table"
    TABLE_CAPTION = "table_caption"
    FIGURE = "figure"
    FIGURE_CAPTION = "figure_caption"
    FORMULA = "formula"
    FORMULA_PARAMETER = "formula_parameter"
    NOTE = "note"
    EXAMPLE = "example"
    DESIGNATION_EXAMPLE = "designation_example"
    PAGE_HEADER = "page_header"
    PAGE_FOOTER = "page_footer"
    TOC_ENTRY = "toc_entry"
    CROSS_REFERENCE = "cross_reference"
    TERM_DEFINITION = "term_definition"
    UNKNOWN = "unknown"


class SectionKind(str, Enum):
    HEADING_SECTION = "heading_section"
    NUMBERED_CLAUSE = "numbered_clause"
    APPENDIX = "appendix"
    TABLE_SECTION = "table_section"
    FIGURE_SECTION = "figure_section"
    FORMULA_SECTION = "formula_section"
    FRONT_MATTER = "front_matter"
    TOC = "toc"
    UNKNOWN = "unknown"


class IssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ParseItemSpan(StrictExtractionModel):
    # Backward-compatible alias for file_page_number.
    # Citation code should prefer file_page_number/file_page_index.
    page: int | None = Field(default=None, ge=1)
    file_page_number: int | None = Field(default=None, ge=1)
    file_page_index: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = Field(default=None, max_length=120)
    item_index: int | None = Field(default=None, ge=0)
    bbox: list[float] | None = Field(default=None, min_length=4, max_length=4)
    normalized_bbox: list[float] | None = Field(default=None, min_length=4, max_length=4)
    text_preview: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def normalize_file_page_aliases(self) -> "ParseItemSpan":
        if (
            self.page is not None
            and self.file_page_number is not None
            and self.page != self.file_page_number
        ):
            raise ValueError("page must match file_page_number")

        if self.file_page_number is None and self.page is not None:
            self.file_page_number = self.page

        if self.page is None and self.file_page_number is not None:
            self.page = self.file_page_number

        expected_index = (
            self.file_page_number - 1
            if self.file_page_number is not None
            else None
        )

        if (
            expected_index is not None
            and self.file_page_index is not None
            and self.file_page_index != expected_index
        ):
            raise ValueError("file_page_index must be file_page_number - 1")

        if self.file_page_index is None and expected_index is not None:
            self.file_page_index = expected_index

        return self

    @field_validator("bbox", "normalized_bbox", mode="before")
    @classmethod
    def _empty_bbox_array_to_none(cls, value: Any) -> Any:
        if value == []:
            return None

        return value

    @field_validator("bbox", "normalized_bbox")
    @classmethod
    def validate_bbox(
        cls,
        value: list[float] | None,
        info: Any,
    ) -> list[float] | None:
        if value is None:
            return value

        if len(value) != 4:
            raise ValueError("bbox must contain exactly 4 numbers")

        if info.field_name == "normalized_bbox":
            for number in value:
                if number < 0 or number > 1:
                    raise ValueError("normalized_bbox values must be in range 0..1")

        return value


class ExtractionIssue(StrictExtractionModel):
    severity: IssueSeverity = IssueSeverity.WARNING
    code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    item_index: int | None = Field(default=None, ge=0)
    evidence: dict[str, Any] = Field(default_factory=dict)


class NumberingScopeExtraction(StrictExtractionModel):
    namespace_id: str = Field(
        min_length=1,
        max_length=120,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    title: str = Field(min_length=1, max_length=500)
    scope_type: NumberingScopeType = NumberingScopeType.UNKNOWN
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    start_item_index: int | None = Field(default=None, ge=0)
    end_item_index_exclusive: int | None = Field(default=None, ge=0)
    numbering_restarts: bool = False
    parent_namespace_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ranges(self) -> "NumberingScopeExtraction":
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be greater than or equal to page_start")

        if (
            self.start_item_index is not None
            and self.end_item_index_exclusive is not None
            and self.end_item_index_exclusive < self.start_item_index
        ):
            raise ValueError(
                "end_item_index_exclusive must be greater than or equal to start_item_index"
            )

        return self


class ItemClassificationExtraction(StrictExtractionModel):
    item_index: int = Field(ge=0)
    role: ItemRole = ItemRole.UNKNOWN
    namespace_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    clause: str | None = Field(default=None, min_length=1, max_length=120)
    belongs_to_clause: str | None = Field(default=None, min_length=1, max_length=120)
    is_normative_clause: bool = False
    source_span: ParseItemSpan | None = None
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1)
    issues: list[ExtractionIssue] = Field(default_factory=list)


class SectionExtraction(StrictExtractionModel):
    section_id: str = Field(min_length=1, max_length=200)
    namespace_id: str = Field(
        min_length=1,
        max_length=120,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    namespaced_path: str = Field(min_length=1, max_length=500)
    clause: str | None = Field(default=None, min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=1000)
    parent_section_id: str | None = Field(default=None, min_length=1, max_length=200)
    parent_clause: str | None = Field(default=None, min_length=1, max_length=120)
    section_kind: SectionKind = SectionKind.UNKNOWN
    content_item_indices: list[int] = Field(default_factory=list)
    source_spans: list[ParseItemSpan] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1)
    issues: list[ExtractionIssue] = Field(default_factory=list)


class DocumentStructureExtraction(StrictExtractionModel):
    schema_version: Literal["document_structure_extraction_v1"] = (
        "document_structure_extraction_v1"
    )
    document_profile: DocumentProfile = DocumentProfile.UNKNOWN
    page_count: int | None = Field(default=None, ge=1)
    numbering_scopes: list[NumberingScopeExtraction] = Field(min_length=1)
    item_classifications: list[ItemClassificationExtraction] = Field(default_factory=list)
    sections: list[SectionExtraction] = Field(default_factory=list)
    issues: list[ExtractionIssue] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_global_invariants(self) -> "DocumentStructureExtraction":
        namespace_ids = [scope.namespace_id for scope in self.numbering_scopes]
        duplicated_namespace_ids = _find_duplicates(namespace_ids)
        if duplicated_namespace_ids:
            raise ValueError(
                "duplicated namespace_id values: "
                + ", ".join(duplicated_namespace_ids)
            )

        known_namespace_ids = set(namespace_ids)

        for scope in self.numbering_scopes:
            if (
                scope.parent_namespace_id is not None
                and scope.parent_namespace_id not in known_namespace_ids
            ):
                raise ValueError(
                    f"unknown parent_namespace_id: {scope.parent_namespace_id}"
                )

        section_ids = [section.section_id for section in self.sections]
        duplicated_section_ids = _find_duplicates(section_ids)
        if duplicated_section_ids:
            raise ValueError(
                "duplicated section_id values: " + ", ".join(duplicated_section_ids)
            )

        section_paths = [section.namespaced_path for section in self.sections]
        duplicated_section_paths = _find_duplicates(section_paths)
        if duplicated_section_paths:
            raise ValueError(
                "duplicated namespaced_path values: "
                + ", ".join(duplicated_section_paths)
            )

        for section in self.sections:
            if section.namespace_id not in known_namespace_ids:
                raise ValueError(f"unknown section namespace_id: {section.namespace_id}")

        item_indexes = [
            classification.item_index
            for classification in self.item_classifications
        ]
        duplicated_item_indexes = _find_duplicates(item_indexes)
        if duplicated_item_indexes:
            raise ValueError(
                "duplicated item classification indexes: "
                + ", ".join(str(value) for value in duplicated_item_indexes)
            )

        if self.page_count is not None:
            _validate_spans_do_not_exceed_page_count(
                self.sections,
                self.item_classifications,
                self.page_count,
            )

        return self


def _find_duplicates(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    duplicated: set[Any] = set()

    for value in values:
        if value in seen:
            duplicated.add(value)
        else:
            seen.add(value)

    return sorted(duplicated)


def _validate_spans_do_not_exceed_page_count(
    sections: list[SectionExtraction],
    item_classifications: list[ItemClassificationExtraction],
    page_count: int,
) -> None:
    for section in sections:
        for span in section.source_spans:
            if span.page is not None and span.page > page_count:
                raise ValueError(
                    f"section {section.section_id} has span page beyond page_count"
                )

    for classification in item_classifications:
        if (
            classification.source_span is not None
            and classification.source_span.page is not None
            and classification.source_span.page > page_count
        ):
            raise ValueError(
                f"item {classification.item_index} has span page beyond page_count"
            )
