import pytest

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentProfile,
    DocumentStructureExtraction,
    ExtractionIssue,
    IssueSeverity,
    ItemClassificationExtraction,
    ItemRole,
    NumberingScopeExtraction,
    NumberingScopeType,
    ParseItemSpan,
    SectionExtraction,
    SectionKind,
)
from convertor_validator_service_lama.services.document_structure_extraction_merge import (
    merge_document_structure_extractions,
)


def make_scope(
    namespace_id: str = "main_document",
    *,
    page_start: int = 1,
    page_end: int = 10,
    confidence: float = 0.9,
) -> NumberingScopeExtraction:
    return NumberingScopeExtraction(
        namespace_id=namespace_id,
        title=namespace_id.replace("_", " ").title(),
        scope_type=NumberingScopeType.MAIN_DOCUMENT,
        page_start=page_start,
        page_end=page_end,
        confidence=confidence,
        reason="Test scope.",
    )


def make_extraction(
    *,
    document_profile: DocumentProfile = DocumentProfile.SIMPLE_STANDARD,
    page_count: int = 10,
    scopes: list[NumberingScopeExtraction] | None = None,
    item_classifications: list[ItemClassificationExtraction] | None = None,
    sections: list[SectionExtraction] | None = None,
    issues: list[ExtractionIssue] | None = None,
) -> DocumentStructureExtraction:
    return DocumentStructureExtraction(
        document_profile=document_profile,
        page_count=page_count,
        numbering_scopes=scopes or [make_scope()],
        item_classifications=item_classifications or [],
        sections=sections or [],
        issues=issues or [],
    )


def make_section(
    path: str,
    *,
    namespace_id: str = "main_document",
    clause: str = "1.1",
    confidence: float = 0.8,
    content_item_indices: list[int] | None = None,
    source_spans: list[ParseItemSpan] | None = None,
) -> SectionExtraction:
    return SectionExtraction(
        section_id=path,
        namespace_id=namespace_id,
        namespaced_path=path,
        clause=clause,
        title="Test section",
        section_kind=SectionKind.NUMBERED_CLAUSE,
        content_item_indices=content_item_indices or [],
        source_spans=source_spans or [],
        confidence=confidence,
        reason="Test section.",
    )


def make_classification(
    item_index: int,
    *,
    role: ItemRole = ItemRole.NORMATIVE_CLAUSE,
    confidence: float = 0.8,
    is_normative_clause: bool = True,
) -> ItemClassificationExtraction:
    return ItemClassificationExtraction(
        item_index=item_index,
        role=role,
        namespace_id="main_document",
        clause="1.1" if is_normative_clause else None,
        is_normative_clause=is_normative_clause,
        source_span=ParseItemSpan(page=1, item_index=item_index),
        confidence=confidence,
        reason="Test classification.",
    )


def test_merge_document_structure_extractions_combines_overview_and_scope_outputs():
    overview = make_extraction(
        document_profile=DocumentProfile.COMPOUND_RULES,
        page_count=139,
        scopes=[
            make_scope("classification", page_start=9, page_end=37),
            make_scope("ptnp", page_start=93, page_end=139),
        ],
    )
    scope_extraction = make_extraction(
        document_profile=DocumentProfile.UNKNOWN,
        page_count=139,
        scopes=[
            make_scope("classification", page_start=9, page_end=37),
        ],
        sections=[
            make_section(
                "classification/1/1",
                namespace_id="classification",
                clause="1.1",
                content_item_indices=[100, 101],
                source_spans=[
                    ParseItemSpan(page=10, item_index=100),
                    ParseItemSpan(page=10, item_index=101),
                ],
            )
        ],
    )

    merged = merge_document_structure_extractions(
        overview_extraction=overview,
        scope_extractions=[scope_extraction],
    )

    assert merged.document_profile == DocumentProfile.COMPOUND_RULES
    assert merged.page_count == 139
    assert [scope.namespace_id for scope in merged.numbering_scopes] == [
        "classification",
        "ptnp",
    ]
    assert len(merged.sections) == 1
    assert merged.sections[0].namespaced_path == "classification/1/1"
    assert merged.diagnostics["input_extractions_count"] == 2
    assert merged.diagnostics["duplicate_numbering_scopes_merged"] == 1


def test_merge_document_structure_extractions_deduplicates_overlap_sections():
    left = make_extraction(
        sections=[
            make_section(
                "main_document/1/1",
                confidence=0.7,
                content_item_indices=[10, 11],
                source_spans=[
                    ParseItemSpan(page=1, item_index=10),
                    ParseItemSpan(page=1, item_index=11),
                ],
            )
        ]
    )
    right = make_extraction(
        sections=[
            make_section(
                "main_document/1/1",
                confidence=0.9,
                content_item_indices=[11, 12],
                source_spans=[
                    ParseItemSpan(page=1, item_index=11),
                    ParseItemSpan(page=2, item_index=12),
                ],
            )
        ]
    )

    merged = merge_document_structure_extractions(
        scope_extractions=[left, right],
    )

    assert len(merged.sections) == 1
    section = merged.sections[0]
    assert section.confidence == 0.9
    assert section.content_item_indices == [10, 11, 12]
    assert [(span.page, span.item_index) for span in section.source_spans] == [
        (1, 10),
        (1, 11),
        (2, 12),
    ]
    assert merged.diagnostics["duplicate_sections_merged"] == 1
    assert merged.diagnostics["section_source_spans_merged"] == 1
    assert merged.diagnostics["section_content_item_indices_merged"] == 1


def test_merge_document_structure_extractions_deduplicates_item_classifications():
    left = make_extraction(
        item_classifications=[
            make_classification(
                12,
                role=ItemRole.DESIGNATION_EXAMPLE,
                confidence=0.6,
                is_normative_clause=False,
            )
        ]
    )
    right = make_extraction(
        item_classifications=[
            make_classification(
                12,
                role=ItemRole.NORMATIVE_CLAUSE,
                confidence=0.9,
                is_normative_clause=True,
            )
        ]
    )

    merged = merge_document_structure_extractions(
        scope_extractions=[left, right],
    )

    assert len(merged.item_classifications) == 1
    classification = merged.item_classifications[0]
    assert classification.item_index == 12
    assert classification.role == ItemRole.NORMATIVE_CLAUSE
    assert classification.confidence == 0.9
    assert classification.is_normative_clause is True
    assert classification.issues[0].code == "merge_conflicting_item_classification"
    assert merged.issues[0].code == "merge_conflicting_item_classification"
    assert merged.diagnostics["duplicate_item_classifications_merged"] == 1


def test_merge_document_structure_extractions_adds_scope_only_namespace():
    scope_extraction = make_extraction(
        document_profile=DocumentProfile.UNKNOWN,
        scopes=[
            make_scope("ptne", page_start=67, page_end=92),
        ],
        sections=[
            make_section(
                "ptne/1/1",
                namespace_id="ptne",
                clause="1.1",
            )
        ],
    )

    merged = merge_document_structure_extractions(
        scope_extractions=[scope_extraction],
    )

    assert [scope.namespace_id for scope in merged.numbering_scopes] == ["ptne"]
    assert merged.sections[0].namespace_id == "ptne"


def test_merge_document_structure_extractions_rejects_empty_input():
    with pytest.raises(ValueError, match="at least one extraction"):
        merge_document_structure_extractions()


def test_merge_document_structure_extractions_accepts_dict_inputs():
    extraction = make_extraction(
        sections=[
            make_section(
                "main_document/1/1",
                content_item_indices=[1],
                source_spans=[ParseItemSpan(page=1, item_index=1)],
            )
        ]
    )

    merged = merge_document_structure_extractions(
        scope_extractions=[extraction.model_dump(mode="json")],
    )

    assert len(merged.sections) == 1
    assert merged.sections[0].namespaced_path == "main_document/1/1"


def test_merge_document_structure_extractions_reports_conflicting_scope_ranges():
    left = make_extraction(
        scopes=[
            make_scope("main_document", page_start=1, page_end=5, confidence=0.9),
        ]
    )
    right = make_extraction(
        scopes=[
            make_scope("main_document", page_start=1, page_end=6, confidence=0.8),
        ]
    )

    merged = merge_document_structure_extractions(
        scope_extractions=[left, right],
    )

    assert merged.numbering_scopes[0].page_end == 5
    assert merged.issues[0].code == "merge_conflicting_numbering_scope"
    assert merged.diagnostics["duplicate_numbering_scopes_merged"] == 1


def test_merge_document_structure_extractions_reports_conflicting_section_clause():
    left = make_extraction(
        sections=[
            make_section(
                "main_document/1/1",
                clause="1.1",
            )
        ]
    )
    right = make_extraction(
        sections=[
            make_section(
                "main_document/1/1",
                clause="1.2",
            )
        ]
    )

    merged = merge_document_structure_extractions(
        scope_extractions=[left, right],
    )

    assert len(merged.sections) == 1
    assert merged.sections[0].issues[0].code == "merge_conflicting_section_clause"
    assert merged.issues[0].code == "merge_conflicting_section_clause"
