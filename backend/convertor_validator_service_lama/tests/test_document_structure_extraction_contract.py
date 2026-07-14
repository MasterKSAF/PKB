import pytest
from pydantic import ValidationError

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentProfile,
    DocumentStructureExtraction,
    ItemClassificationExtraction,
    ItemRole,
    NumberingScopeExtraction,
    NumberingScopeType,
    ParseItemSpan,
    SectionExtraction,
    SectionKind,
)
from convertor_validator_service_lama.prompts.document_structure_extraction import (
    SYSTEM_PROMPT,
    build_document_structure_extraction_prompt,
    document_structure_extraction_json_schema,
)


def test_document_structure_extraction_accepts_simple_standard_contract():
    extraction = DocumentStructureExtraction(
        document_profile=DocumentProfile.SIMPLE_STANDARD,
        page_count=5,
        numbering_scopes=[
            NumberingScopeExtraction(
                namespace_id="main_document",
                title="Main document",
                scope_type=NumberingScopeType.MAIN_DOCUMENT,
                page_start=1,
                page_end=5,
                start_item_index=0,
                end_item_index_exclusive=82,
                numbering_restarts=False,
                confidence=0.95,
                reason="The document has one continuous numbering scope.",
            )
        ],
        item_classifications=[
            ItemClassificationExtraction(
                item_index=5,
                role=ItemRole.NORMATIVE_CLAUSE,
                namespace_id="main_document",
                clause="1.1",
                is_normative_clause=True,
                source_span=ParseItemSpan(
                    page=1,
                    item_index=5,
                    bbox=[10, 20, 300, 40],
                    normalized_bbox=[0.01, 0.02, 0.3, 0.04],
                    text_preview="1.1. Clause text",
                ),
                confidence=0.93,
                reason="The item starts with a clause number and belongs to section 1.",
            )
        ],
        sections=[
            SectionExtraction(
                section_id="main_document/1/1",
                namespace_id="main_document",
                namespaced_path="main_document/1/1",
                clause="1.1",
                title="Clause text",
                parent_section_id=None,
                parent_clause="1",
                section_kind=SectionKind.NUMBERED_CLAUSE,
                content_item_indices=[5, 6, 7],
                source_spans=[
                    ParseItemSpan(
                        page=1,
                        item_index=5,
                        bbox=[10, 20, 300, 40],
                        normalized_bbox=[0.01, 0.02, 0.3, 0.04],
                    )
                ],
                confidence=0.91,
                reason="The clause starts at item 5 and continues until the next clause.",
            )
        ],
    )

    assert extraction.schema_version == "document_structure_extraction_v1"
    assert extraction.numbering_scopes[0].namespace_id == "main_document"
    assert extraction.sections[0].namespaced_path == "main_document/1/1"


def test_document_structure_extraction_accepts_compound_repeated_local_paths():
    extraction = DocumentStructureExtraction(
        document_profile=DocumentProfile.COMPOUND_RULES,
        page_count=139,
        numbering_scopes=[
            NumberingScopeExtraction(
                namespace_id="classification",
                title="Classification",
                scope_type=NumberingScopeType.CLASSIFICATION,
                page_start=9,
                page_end=37,
                numbering_restarts=True,
                confidence=0.9,
                reason="The classification part has its own numbering.",
            ),
            NumberingScopeExtraction(
                namespace_id="ptne",
                title="PTNE",
                scope_type=NumberingScopeType.PART,
                page_start=67,
                page_end=92,
                numbering_restarts=True,
                confidence=0.9,
                reason="The PTNE part restarts numbering.",
            ),
        ],
        sections=[
            SectionExtraction(
                section_id="classification/1/1",
                namespace_id="classification",
                namespaced_path="classification/1/1",
                clause="1.1",
                section_kind=SectionKind.NUMBERED_CLAUSE,
                source_spans=[ParseItemSpan(page=10, item_index=100)],
                confidence=0.88,
                reason="Clause belongs to classification scope.",
            ),
            SectionExtraction(
                section_id="ptne/1/1",
                namespace_id="ptne",
                namespaced_path="ptne/1/1",
                clause="1.1",
                section_kind=SectionKind.NUMBERED_CLAUSE,
                source_spans=[ParseItemSpan(page=68, item_index=900)],
                confidence=0.88,
                reason="Same local clause number belongs to another scope.",
            ),
        ],
    )

    assert [section.clause for section in extraction.sections] == ["1.1", "1.1"]
    assert extraction.sections[0].namespaced_path != extraction.sections[1].namespaced_path


def test_document_structure_extraction_rejects_duplicate_namespace_ids():
    with pytest.raises(ValidationError, match="duplicated namespace_id"):
        DocumentStructureExtraction(
            numbering_scopes=[
                NumberingScopeExtraction(
                    namespace_id="main_document",
                    title="Main",
                    confidence=0.8,
                    reason="First scope.",
                ),
                NumberingScopeExtraction(
                    namespace_id="main_document",
                    title="Main duplicate",
                    confidence=0.7,
                    reason="Duplicate scope.",
                ),
            ]
        )


def test_document_structure_extraction_rejects_duplicate_section_paths():
    with pytest.raises(ValidationError, match="duplicated namespaced_path"):
        DocumentStructureExtraction(
            numbering_scopes=[
                NumberingScopeExtraction(
                    namespace_id="main_document",
                    title="Main",
                    confidence=0.8,
                    reason="Single scope.",
                )
            ],
            sections=[
                SectionExtraction(
                    section_id="a",
                    namespace_id="main_document",
                    namespaced_path="main_document/1",
                    source_spans=[ParseItemSpan(page=1)],
                    confidence=0.8,
                    reason="First.",
                ),
                SectionExtraction(
                    section_id="b",
                    namespace_id="main_document",
                    namespaced_path="main_document/1",
                    source_spans=[ParseItemSpan(page=1)],
                    confidence=0.8,
                    reason="Duplicate.",
                ),
            ],
        )


def test_document_structure_extraction_rejects_invalid_normalized_bbox():
    with pytest.raises(ValidationError, match="normalized_bbox values"):
        ParseItemSpan(
            page=1,
            item_index=1,
            normalized_bbox=[0.1, 0.2, 1.5, 0.4],
        )


def test_prompt_builder_uses_external_schema_and_includes_input():
    prompt = build_document_structure_extraction_prompt(
        document_markdown="## 1. Test\n1.1. Clause text",
        parse_items_preview=[
            {
                "item_index": 5,
                "type": "text",
                "page_number": 1,
                "text": "1.1. Clause text",
            }
        ],
        page_count=1,
        document_hint="simple standard",
    )

    schema = document_structure_extraction_json_schema()

    assert "Supplied separately via data_schema" in prompt
    assert "DocumentStructureExtraction" not in prompt
    assert "document_structure_extraction_v1" not in prompt
    assert "simple standard" in prompt
    assert "1.1. Clause text" in prompt
    assert "Return JSON only" in prompt
    assert schema["title"] == "DocumentStructureExtraction"
    assert "Return JSON only" in SYSTEM_PROMPT

def test_document_structure_extraction_classifies_numbered_lookalikes():
    extraction = DocumentStructureExtraction(
        document_profile=DocumentProfile.SIMPLE_STANDARD,
        page_count=5,
        numbering_scopes=[
            NumberingScopeExtraction(
                namespace_id="main_document",
                title="Main document",
                scope_type=NumberingScopeType.MAIN_DOCUMENT,
                page_start=1,
                page_end=5,
                confidence=0.95,
                reason="The document has one continuous numbering scope.",
            )
        ],
        item_classifications=[
            ItemClassificationExtraction(
                item_index=12,
                role=ItemRole.DESIGNATION_EXAMPLE,
                namespace_id="main_document",
                belongs_to_clause="1.1",
                is_normative_clause=False,
                source_span=ParseItemSpan(
                    page=2,
                    item_index=12,
                    text_preview="750 X 50 ? 64? 16-? ???? 10054?82",
                ),
                confidence=0.89,
                reason="The item is a product designation example, not a clause.",
            ),
            ItemClassificationExtraction(
                item_index=28,
                role=ItemRole.PAGE_HEADER,
                namespace_id="main_document",
                is_normative_clause=False,
                source_span=ParseItemSpan(
                    page=3,
                    item_index=28,
                    text_preview="?. 3 ???? 10054?12",
                ),
                confidence=0.91,
                reason="The item is a page header with a suspected OCR error.",
            ),
            ItemClassificationExtraction(
                item_index=29,
                role=ItemRole.NORMATIVE_CLAUSE,
                namespace_id="main_document",
                clause="2.4",
                is_normative_clause=True,
                source_span=ParseItemSpan(
                    page=3,
                    item_index=29,
                    text_preview="2.4. ???????????? ?????? ???? ?????? ?????? ? ???????...",
                ),
                confidence=0.94,
                reason="The item starts with a valid clause number in the current scope.",
            ),
        ],
    )

    roles = {
        classification.item_index: classification.role
        for classification in extraction.item_classifications
    }

    assert roles[12] == ItemRole.DESIGNATION_EXAMPLE
    assert roles[28] == ItemRole.PAGE_HEADER
    assert roles[29] == ItemRole.NORMATIVE_CLAUSE
    assert extraction.item_classifications[0].is_normative_clause is False
    assert extraction.item_classifications[2].is_normative_clause is True

def test_parse_item_span_treats_empty_bbox_arrays_as_absent() -> None:
    payload = {
        "schema_version": "document_structure_extraction_v1",
        "document_profile": "simple_standard",
        "page_count": 1,
        "numbering_scopes": [
            {
                "namespace_id": "main_document",
                "title": "Main document",
                "scope_type": "main_document",
                "page_start": 1,
                "page_end": 1,
                "confidence": 0.9,
                "reason": "Test scope.",
            }
        ],
        "item_classifications": [
            {
                "item_index": 0,
                "role": "body_text",
                "namespace_id": "main_document",
                "clause": "1",
                "belongs_to_clause": "1",
                "is_normative_clause": True,
                "source_span": {
                    "page": 1,
                    "item_index": 0,
                    "bbox": [],
                    "normalized_bbox": [],
                    "text_preview": "Clause text.",
                },
                "confidence": 0.9,
                "reason": "Test classification.",
                "issues": [],
            }
        ],
        "sections": [
            {
                "section_id": "main_document/1",
                "namespace_id": "main_document",
                "namespaced_path": "main_document/1",
                "clause": "1",
                "title": "Clause 1",
                "section_kind": "numbered_clause",
                "content_item_indices": [0],
                "source_spans": [
                    {
                        "page": 1,
                        "item_index": 0,
                        "bbox": [],
                        "normalized_bbox": [],
                        "text_preview": "Clause text.",
                    }
                ],
                "confidence": 0.9,
                "reason": "Test section.",
                "issues": [],
            }
        ],
        "issues": [],
        "diagnostics": {},
    }

    extraction = DocumentStructureExtraction.model_validate(payload)

    source_span = extraction.item_classifications[0].source_span
    assert source_span is not None
    assert source_span.bbox is None
    assert source_span.normalized_bbox is None

    section_span = extraction.sections[0].source_spans[0]
    assert section_span.bbox is None
    assert section_span.normalized_bbox is None

def test_document_structure_extraction_normalizes_nullable_collections() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "compound_rules",
            "page_count": 139,
            "numbering_scopes": [
                {
                    "namespace_id": "classification",
                    "title": "Classification",
                    "page_start": 9,
                    "page_end": 37,
                    "start_item_index": 96,
                    "end_item_index_exclusive": 530,
                    "confidence": 0.99,
                    "reason": "Test scope.",
                }
            ],
            "item_classifications": None,
            "sections": None,
            "issues": None,
            "diagnostics": None,
        }
    )

    assert extraction.item_classifications == []
    assert extraction.sections == []
    assert extraction.issues == []
    assert extraction.diagnostics == {}

def test_document_structure_extraction_drops_duplicate_numbering_scopes() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "compound_rules",
            "page_count": 139,
            "numbering_scopes": [
                {
                    "namespace_id": "classification",
                    "title": "Classification",
                    "page_start": 9,
                    "page_end": 37,
                    "start_item_index": 96,
                    "end_item_index_exclusive": 530,
                    "confidence": 0.99,
                    "reason": "First scope.",
                },
                {
                    "namespace_id": "classification",
                    "title": "Classification duplicate",
                    "page_start": 10,
                    "page_end": 37,
                    "start_item_index": 100,
                    "end_item_index_exclusive": 530,
                    "confidence": 0.8,
                    "reason": "Duplicate scope.",
                },
            ],
            "item_classifications": [],
            "sections": [],
            "issues": [],
            "diagnostics": {},
        }
    )

    assert [scope.namespace_id for scope in extraction.numbering_scopes] == [
        "classification"
    ]
    assert extraction.diagnostics["duplicate_numbering_scopes_dropped"] == [
        "classification"
    ]

def test_document_structure_extraction_normalizes_nullable_section_collections() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "compound_rules",
            "page_count": 139,
            "numbering_scopes": [
                {
                    "namespace_id": "classification",
                    "title": "Classification",
                    "page_start": 9,
                    "page_end": 37,
                    "start_item_index": 96,
                    "end_item_index_exclusive": 530,
                    "confidence": 0.99,
                    "reason": "Test scope.",
                }
            ],
            "sections": [
                {
                    "section_id": "classification/1",
                    "namespace_id": "classification",
                    "namespaced_path": "classification/1",
                    "clause": "1",
                    "title": "General",
                    "parent_section_id": None,
                    "parent_clause": None,
                    "section_kind": "numbered_clause",
                    "content_item_indices": None,
                    "source_spans": None,
                    "confidence": 0.9,
                    "reason": "Test section.",
                    "issues": None,
                }
            ],
            "item_classifications": [],
            "issues": [],
            "diagnostics": {},
        }
    )

    section = extraction.sections[0]
    assert section.content_item_indices == []
    assert section.source_spans == []
    assert section.issues == []
