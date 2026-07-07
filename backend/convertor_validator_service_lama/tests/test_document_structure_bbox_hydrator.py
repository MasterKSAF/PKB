from __future__ import annotations

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentStructureExtraction,
)
from convertor_validator_service_lama.services.document_structure_bbox_hydrator import (
    hydrate_document_structure_extraction_source_spans_from_parse_items,
)


def test_bbox_hydrator_fills_empty_spans_from_parse_item_position() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
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
                    "item_index": 1,
                    "role": "body_text",
                    "namespace_id": "main_document",
                    "clause": "1",
                    "belongs_to_clause": "1",
                    "is_normative_clause": True,
                    "source_span": {
                        "page": 1,
                        "item_index": 1,
                        "bbox": [],
                        "normalized_bbox": [],
                        "text_preview": "Clause text",
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
                    "title": None,
                    "section_kind": "numbered_clause",
                    "content_item_indices": [1],
                    "source_spans": [
                        {
                            "page": 1,
                            "item_index": 1,
                            "bbox": [],
                            "normalized_bbox": [],
                            "text_preview": "Clause text",
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
    )

    parse_items = [
        {
            "page_number": 1,
            "type": "text",
            "text": "Header",
            "bbox": [{"x": 1, "y": 1, "w": 2, "h": 2}],
            "page_width": 100,
            "page_height": 200,
        },
        {
            "page_number": 1,
            "type": "text",
            "text": "Clause text with more words.",
            "bbox": [
                {"x": 10, "y": 20, "w": 30, "h": 40},
                {"x": 20, "y": 25, "w": 25, "h": 45},
            ],
            "page_width": 100,
            "page_height": 200,
        },
    ]

    result = hydrate_document_structure_extraction_source_spans_from_parse_items(
        extraction,
        parse_items,
    )

    classification_span = result.extraction.item_classifications[0].source_span
    assert classification_span is not None
    assert classification_span.bbox == [10.0, 20.0, 35.0, 50.0]
    assert classification_span.normalized_bbox == [0.1, 0.1, 0.35, 0.25]

    section_span = result.extraction.sections[0].source_spans[0]
    assert section_span.bbox == [10.0, 20.0, 35.0, 50.0]
    assert section_span.normalized_bbox == [0.1, 0.1, 0.35, 0.25]

    assert result.diagnostics["spans_seen"] == 2
    assert result.diagnostics["spans_hydrated"] == 2
    assert result.diagnostics["spans_missing_parse_bbox"] == 0


def test_bbox_hydrator_skips_page_mismatch() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "simple_standard",
            "page_count": 2,
            "numbering_scopes": [
                {
                    "namespace_id": "main_document",
                    "title": "Main document",
                    "scope_type": "main_document",
                    "page_start": 1,
                    "page_end": 2,
                    "confidence": 0.9,
                    "reason": "Test scope.",
                }
            ],
            "item_classifications": [
                {
                    "item_index": 0,
                    "role": "body_text",
                    "source_span": {
                        "page": 2,
                        "item_index": 0,
                        "text_preview": "Clause text",
                    },
                    "confidence": 0.9,
                    "reason": "Test classification.",
                    "issues": [],
                }
            ],
            "sections": [],
            "issues": [],
            "diagnostics": {},
        }
    )

    result = hydrate_document_structure_extraction_source_spans_from_parse_items(
        extraction,
        [
            {
                "page_number": 1,
                "text": "Clause text",
                "bbox": [{"x": 10, "y": 20, "w": 30, "h": 40}],
                "page_width": 100,
                "page_height": 200,
            }
        ],
    )

    span = result.extraction.item_classifications[0].source_span
    assert span is not None
    assert span.bbox is None
    assert span.normalized_bbox is None
    assert result.diagnostics["spans_page_mismatch"] == 1


def test_bbox_hydrator_skips_text_mismatch() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "simple_standard",
            "page_count": 1,
            "numbering_scopes": [
                {
                    "namespace_id": "main_document",
                    "title": "Main document",
                    "scope_type": "main_document",
                    "confidence": 0.9,
                    "reason": "Test scope.",
                }
            ],
            "item_classifications": [
                {
                    "item_index": 0,
                    "role": "body_text",
                    "source_span": {
                        "page": 1,
                        "item_index": 0,
                        "text_preview": "Completely different technical clause",
                    },
                    "confidence": 0.9,
                    "reason": "Test classification.",
                    "issues": [],
                }
            ],
            "sections": [],
            "issues": [],
            "diagnostics": {},
        }
    )

    result = hydrate_document_structure_extraction_source_spans_from_parse_items(
        extraction,
        [
            {
                "page_number": 1,
                "text": "Short header",
                "bbox": [{"x": 10, "y": 20, "w": 30, "h": 40}],
                "page_width": 100,
                "page_height": 200,
            }
        ],
    )

    span = result.extraction.item_classifications[0].source_span
    assert span is not None
    assert span.bbox is None
    assert span.normalized_bbox is None
    assert result.diagnostics["spans_text_mismatch"] == 1

def test_bbox_hydrator_skips_section_span_when_clause_mismatches_preview() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "simple_standard",
            "page_count": 1,
            "numbering_scopes": [
                {
                    "namespace_id": "main_document",
                    "title": "Main document",
                    "scope_type": "main_document",
                    "confidence": 0.9,
                    "reason": "Test scope.",
                }
            ],
            "item_classifications": [],
            "sections": [
                {
                    "section_id": "main_document/6/6.2",
                    "namespace_id": "main_document",
                    "namespaced_path": "main_document/6/6.2",
                    "clause": "6.2",
                    "title": None,
                    "section_kind": "numbered_clause",
                    "content_item_indices": [0],
                    "source_spans": [
                        {
                            "page": 1,
                            "item_index": 0,
                            "text_preview": "6.4. Wrong clause text",
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
    )

    result = hydrate_document_structure_extraction_source_spans_from_parse_items(
        extraction,
        [
            {
                "page_number": 1,
                "text": "6.4. Wrong clause text",
                "bbox": [{"x": 10, "y": 20, "w": 30, "h": 40}],
                "page_width": 100,
                "page_height": 200,
            }
        ],
    )

    span = result.extraction.sections[0].source_spans[0]

    assert span.bbox is None
    assert span.normalized_bbox is None
    assert result.diagnostics["spans_clause_mismatch"] == 1

def test_bbox_hydrator_recovers_section_bbox_by_clause_when_source_span_wrong() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "simple_standard",
            "page_count": 1,
            "numbering_scopes": [
                {
                    "namespace_id": "main_document",
                    "title": "Main document",
                    "scope_type": "main_document",
                    "confidence": 0.9,
                    "reason": "Test scope.",
                }
            ],
            "item_classifications": [],
            "sections": [
                {
                    "section_id": "main_document/6/6.2",
                    "namespace_id": "main_document",
                    "namespaced_path": "main_document/6/6.2",
                    "clause": "6.2",
                    "title": None,
                    "section_kind": "numbered_clause",
                    "content_item_indices": [2],
                    "source_spans": [
                        {
                            "page": 1,
                            "item_index": 2,
                            "text_preview": "6.4. Wrong clause text",
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
    )

    result = hydrate_document_structure_extraction_source_spans_from_parse_items(
        extraction,
        [
            {
                "page_number": 1,
                "text": "6.2. Correct clause text",
                "bbox": [{"x": 10, "y": 20, "w": 30, "h": 40}],
                "page_width": 100,
                "page_height": 200,
            },
            {
                "page_number": 1,
                "text": "6.3. Another clause text",
                "bbox": [{"x": 50, "y": 60, "w": 20, "h": 10}],
                "page_width": 100,
                "page_height": 200,
            },
            {
                "page_number": 1,
                "text": "6.4. Wrong clause text",
                "bbox": [{"x": 70, "y": 80, "w": 20, "h": 10}],
                "page_width": 100,
                "page_height": 200,
            },
        ],
    )

    section = result.extraction.sections[0]
    assert len(section.source_spans) == 1
    assert section.source_spans[0].item_index == 0
    assert section.source_spans[0].bbox == [10.0, 20.0, 30.0, 40.0]
    assert section.source_spans[0].normalized_bbox == [0.1, 0.1, 0.3, 0.2]
    assert result.diagnostics["spans_clause_mismatch"] == 1
    assert result.diagnostics["sections_hydrated_by_clause_fallback"] == 1
    assert result.diagnostics["spans_replaced_by_clause_fallback"] == 1


def test_bbox_hydrator_adds_source_span_by_clause_when_section_has_no_spans() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "simple_standard",
            "page_count": 1,
            "numbering_scopes": [
                {
                    "namespace_id": "main_document",
                    "title": "Main document",
                    "scope_type": "main_document",
                    "confidence": 0.9,
                    "reason": "Test scope.",
                }
            ],
            "item_classifications": [],
            "sections": [
                {
                    "section_id": "main_document/6/6.3",
                    "namespace_id": "main_document",
                    "namespaced_path": "main_document/6/6.3",
                    "clause": "6.3",
                    "title": None,
                    "section_kind": "numbered_clause",
                    "content_item_indices": [],
                    "source_spans": [],
                    "confidence": 0.9,
                    "reason": "Test section.",
                    "issues": [],
                }
            ],
            "issues": [],
            "diagnostics": {},
        }
    )

    result = hydrate_document_structure_extraction_source_spans_from_parse_items(
        extraction,
        [
            {
                "page_number": 1,
                "text": "6.3. Missing span clause text",
                "bbox": [{"x": 25, "y": 50, "w": 25, "h": 50}],
                "page_width": 100,
                "page_height": 200,
            },
        ],
    )

    section = result.extraction.sections[0]
    assert len(section.source_spans) == 1
    assert section.source_spans[0].item_index == 0
    assert section.source_spans[0].bbox == [25.0, 50.0, 25.0, 50.0]
    assert section.source_spans[0].normalized_bbox == [0.25, 0.25, 0.25, 0.25]
    assert result.diagnostics["sections_hydrated_by_clause_fallback"] == 1
    assert result.diagnostics["spans_added_by_clause_fallback"] == 1

def test_bbox_hydrator_prefers_clause_span_over_table_span() -> None:
    extraction = DocumentStructureExtraction.model_validate(
        {
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "simple_standard",
            "page_count": 1,
            "numbering_scopes": [
                {
                    "namespace_id": "main_document",
                    "title": "Main document",
                    "scope_type": "main_document",
                    "confidence": 0.9,
                    "reason": "Test scope.",
                }
            ],
            "item_classifications": [],
            "sections": [
                {
                    "section_id": "main_document/6/6.1",
                    "namespace_id": "main_document",
                    "namespaced_path": "main_document/6/6.1",
                    "clause": "6.1",
                    "title": None,
                    "section_kind": "numbered_clause",
                    "content_item_indices": [1],
                    "source_spans": [
                        {
                            "page": 1,
                            "item_index": 1,
                            "text_preview": "Table values for clause 6.1",
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
    )

    result = hydrate_document_structure_extraction_source_spans_from_parse_items(
        extraction,
        [
            {
                "page_number": 1,
                "text": "6.1. Correct leading clause text",
                "bbox": [{"x": 10, "y": 20, "w": 30, "h": 40}],
                "page_width": 100,
                "page_height": 200,
            },
            {
                "page_number": 1,
                "text": "Table values for clause 6.1",
                "bbox": [{"x": 50, "y": 60, "w": 40, "h": 30}],
                "page_width": 100,
                "page_height": 200,
            },
        ],
    )

    section = result.extraction.sections[0]

    assert len(section.source_spans) == 2
    assert section.source_spans[0].item_index == 0
    assert section.source_spans[0].bbox == [10.0, 20.0, 30.0, 40.0]
    assert section.source_spans[0].normalized_bbox == [0.1, 0.1, 0.3, 0.2]
    assert section.source_spans[1].item_index == 1
    assert section.source_spans[1].bbox == [50.0, 60.0, 40.0, 30.0]
    assert section.source_spans[1].normalized_bbox == [0.5, 0.3, 0.4, 0.15]
    assert result.diagnostics["sections_preferred_clause_fallback"] == 1
