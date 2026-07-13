from convertor_validator_service_lama.models.extract_job import ExtractJobResult
from convertor_validator_service_lama.models.parse_job import ParseJobResult
from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentStructure,
)
from convertor_validator_service_lama.services.rich_document_package_assembler import (
    assemble_rich_document_package,
)
from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackageAssemblyRequest,
)
from gost_20868_fixture_helpers import (
    gost_20868_chunk_container_extract_results,
    load_gost_20868_formula_chunk_container,
    load_gost_20868_v2_chunk_container,
)


def _parse_result() -> ParseJobResult:
    return ParseJobResult.model_construct(
        job_id="parse-job-1",
        status="COMPLETED",
        markdown="# Test document",
        items=[],
        metadata={"title": "Test document"},
        job_metadata={},
        raw_response={"job_id": "parse-job-1"},
    )


def _extract_result(result: dict[str, object]) -> ExtractJobResult:
    return ExtractJobResult.model_construct(
        job_id="extract-job-1",
        status="COMPLETED",
        result=result,
        raw_response=result,
    )


def test_assembler_fills_document_structure_from_extract_artifacts() -> None:
    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        parse_result=_parse_result(),
        extract_results={
            "document_boundaries": _extract_result(
                {
                    "document_boundaries": [
                        {
                            "boundary_id": "boundary-1",
                            "boundary_type": "main_document",
                            "title": "Main document",
                            "page_start": 1,
                            "page_end": 10,
                        }
                    ]
                }
            ),
            "table_of_contents": _extract_result(
                {
                    "table_of_contents": [
                        {
                            "item_id": "toc-1",
                            "title": "1. Scope",
                            "level": 1,
                            "page": 1,
                            "path": "1",
                            "target_section_id": "section-1",
                        }
                    ]
                }
            ),
            "table_of_contents_blocks": _extract_result(
                {
                    "table_of_contents_blocks": [
                        {
                            "toc_id": "toc-main",
                            "title": "Table of contents",
                            "namespace_id": "front_matter",
                            "page_start": 1,
                            "page_end": 1,
                            "items": [
                                {
                                    "item_id": "toc-main-1",
                                    "title": "1. Scope",
                                    "level": 1,
                                    "page": 1,
                                    "path": "1",
                                    "target_section_id": "section-1",
                                }
                            ],
                        },
                        {
                            "toc_id": "toc-appendix",
                            "title": "Appendix table of contents",
                            "namespace_id": "appendix_a",
                            "page_start": 10,
                            "page_end": 10,
                            "items": [
                                {
                                    "item_id": "toc-appendix-1",
                                    "title": "A.1 Additional requirements",
                                    "level": 1,
                                    "page": 11,
                                    "path": "appendix_a/a_1",
                                }
                            ],
                        },
                    ]
                }
            ),
            "nested_documents": _extract_result(
                {
                    "nested_documents": [
                        {
                            "nested_document_id": "nested-1",
                            "document_code": "APPENDIX-A",
                            "title": "Appendix A",
                            "page_start": 11,
                            "page_end": 12,
                            "parent_boundary_id": "boundary-1",
                        }
                    ]
                }
            ),
            "sections": _extract_result(
                {
                    "sections": [
                        {
                            "section_id": "section-1",
                            "clause": "1",
                            "title": "1. Scope",
                            "level": 1,
                            "path": "1",
                            "page_start": 1,
                            "page_end": 1,
                            "section_type": "text",
                            "content": {"text": "Scope text"},
                        }
                    ]
                }
            ),
            "tables": _extract_result(
                {
                    "tables": [
                        {
                            "table_id": "table-1",
                            "caption": "Table 1",
                            "page": 2,
                            "cells": [
                                {
                                    "row_index": 0,
                                    "column_index": 1,
                                    "text": "Cell text",
                                    "images": [
                                        {
                                            "image_id": "image-in-cell-1",
                                            "caption": "Cell image",
                                            "page": 2,
                                        }
                                    ],
                                    "formulas": [
                                        {
                                            "formula_id": "formula-in-cell-1",
                                            "expression": "a=b",
                                            "page": 2,
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ),
            "images": _extract_result(
                {
                    "images": [
                        {
                            "image_id": "image-1",
                            "caption": "Figure 1",
                            "alt_text": "Figure alt",
                            "page": 3,
                            "bbox": [0.1, 0.2, 0.3, 0.4],
                            "storage_uri": "minio://bucket/image-1.png",
                        }
                    ]
                }
            ),
            "formulas": _extract_result(
                {
                    "formulas": [
                        {
                            "formula_id": "formula-1",
                            "expression": "x=y",
                            "latex": "x=y",
                            "page": 4,
                            "parameters": [{"name": "x"}],
                        }
                    ]
                }
            ),
            "notes": _extract_result(
                {
                    "notes": [
                        {
                            "note_id": "note-1",
                            "namespace_id": "main_document",
                            "section_id": "section-1",
                            "text": "Note text",
                            "page": 2,
                            "bbox": [0.1, 0.2, 0.3, 0.4],
                        }
                    ]
                }
            ),
            "references": _extract_result(
                {
                    "references": [
                        {
                            "reference_id": "reference-1",
                            "namespace_id": "main_document",
                            "section_id": "section-1",
                            "reference_text": "\u0413\u041e\u0421\u0422 20862-81- \u0413\u041e\u0421\u0422 20867-81",
                            "target_document_code": "GOST 123",
                            "target_clause": "1.2",
                            "reference_type": "normative_reference",
                            "page": 3,
                            "bbox": [0.1, 0.2, 0.3, 0.4],
                        }
                    ]
                }
            ),
            "cross_references": _extract_result(
                {
                    "cross_references": [
                        {
                            "reference_id": "ref-1",
                            "source_id": "section-1",
                            "target_document_code": "ГОСТ 123",
                            "reference_type": "normative_reference",
                            "context": "See ГОСТ 123",
                        }
                    ]
                }
            ),
            "validation_critic": _extract_result(
                {
                    "quality_report": {"score": 0.95},
                    "correction_proposals": [
                        {
                            "kind": "replace_text",
                            "target": "section-1",
                        }
                    ],
                }
            ),
        },
    )

    result = assemble_rich_document_package(request)

    structure = result.package.document_structure

    assert isinstance(structure, RichDocumentStructure)
    assert structure.document_boundaries[0].boundary_id == "boundary-1"
    assert len(structure.table_of_contents_blocks) == 2
    assert structure.table_of_contents_blocks[0].toc_id == "toc-main"
    assert structure.table_of_contents_blocks[1].namespace_id == "appendix_a"
    assert structure.table_of_contents_blocks[1].items[0].title == "A.1 Additional requirements"
    assert structure.table_of_contents[0].target_section_id == "section-1"
    assert structure.nested_documents[0].document_code == "APPENDIX-A"

    assert structure.sections[0].section_id == "section-1"
    assert structure.sections[0].content == {"text": "Scope text"}

    assert structure.tables[0].table_id == "table-1"
    assert structure.tables[0].cells[0].text == "Cell text"
    assert structure.tables[0].cells[0].images[0].image_id == "image-in-cell-1"
    assert structure.tables[0].cells[0].formulas[0].expression == "a=b"

    assert structure.images[0].image_id == "image-1"
    assert structure.images[0].storage_uri == "minio://bucket/image-1.png"

    assert structure.formulas[0].formula_id == "formula-1"
    assert structure.formulas[0].parameters == [{"name": "x"}]

    assert structure.cross_references[0].target_document_code == "ГОСТ 123"

    assert structure.quality_report == {"score": 0.95}
    assert structure.correction_proposals[0]["kind"] == "replace_text"


def test_assembler_uses_empty_document_structure_when_extract_artifacts_are_absent() -> None:
    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        parse_result=_parse_result(),
        extract_results={},
    )

    result = assemble_rich_document_package(request)

    structure = result.package.document_structure

    assert structure.document_boundaries == []
    assert structure.table_of_contents_blocks == []
    assert structure.table_of_contents == []
    assert structure.nested_documents == []
    assert structure.sections == []
    assert structure.tables == []
    assert structure.images == []
    assert structure.formulas == []
    assert structure.notes == []
    assert structure.references == []
    assert structure.cross_references == []
    assert structure.quality_report is None
    assert structure.correction_proposals == []


def test_assembler_builds_document_structure_from_parse_items_when_extract_sections_absent() -> None:
    parse_result = ParseJobResult.model_construct(
        job_id="parse-job-items",
        status="COMPLETED",
        markdown="# Parsed document",
        items=[
            {
                "type": "heading",
                "md": "# \u0427\u0410\u0421\u0422\u042c I \u00ab\u041a\u041b\u0410\u0421\u0421\u0418\u0424\u0418\u041a\u0410\u0426\u0418\u042f\u00bb",
                "page_number": 9,
                "page_width": 100.0,
                "page_height": 200.0,
                "bbox": [{"x": 10.0, "y": 10.0, "w": 80.0, "h": 10.0}],
            },
            {
                "type": "heading",
                "md": "# 1. \u041e\u0431\u0449\u0438\u0435 \u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f",
                "page_number": 10,
                "page_width": 100.0,
                "page_height": 200.0,
                "bbox": [{"x": 10.0, "y": 20.0, "w": 80.0, "h": 10.0}],
            },
            {
                "type": "heading",
                "md": "## 1.1. \u041e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f",
                "page_number": 10,
                "page_width": 100.0,
                "page_height": 200.0,
                "bbox": [{"x": 10.0, "y": 30.0, "w": 80.0, "h": 10.0}],
            },
            {
                "type": "text",
                "md": "Definition text.",
                "page_number": 10,
                "page_width": 100.0,
                "page_height": 200.0,
                "bbox": [{"x": 20.0, "y": 40.0, "w": 70.0, "h": 8.0}],
            },
        ],
        metadata={"pages": [{"page": 1}] * 10},
        job_metadata={"pdf-pages": 10},
        raw_response={"job_id": "parse-job-items"},
    )

    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GIMS-TEST",
        parse_result=parse_result,
        extract_results={},
    )

    result = assemble_rich_document_package(request)

    structure = result.package.document_structure

    assert [namespace.namespace_id for namespace in structure.namespaces] == [
        "front_matter",
        "classification",
    ]

    by_path = {section.path: section for section in structure.sections}

    assert "classification/1/1" in by_path

    section = by_path["classification/1/1"]

    assert section.section_id == "3"
    assert section.parent_section_id == "2"
    assert section.clause == "1.1"
    assert section.title == "1.1. \u041e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f"
    assert section.section_type == "numbered_section"
    assert section.content == "Definition text."
    assert section.page_start == 10
    assert section.page_end == 10
    assert section.bbox == [0.1, 0.15, 0.8, 0.05]
    assert section.raw["namespaced_path"] == "classification/1/1"
    assert section.raw["source_spans"][1]["normalized_bbox"] == {
        "x": 0.2,
        "y": 0.2,
        "w": 0.7,
        "h": 0.04,
    }

    assert structure.diagnostics["parse_item_structure"]["sections_count"] == 3
    assert structure.diagnostics["parse_item_structure"]["namespaces_count"] == 2


def test_assembler_maps_document_structure_extraction_artifact_into_structure() -> None:
    extraction_payload = {
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
                "confidence": 0.95,
                "reason": "Fake overview.",
            }
        ],
        "item_classifications": [
            {
                "item_index": 0,
                "role": "normative_clause",
                "namespace_id": "main_document",
                "clause": "1.1",
                "is_normative_clause": True,
                "source_span": {"page": 1, "item_index": 0},
                "confidence": 0.9,
                "reason": "Fake classification.",
            }
        ],
        "sections": [
            {
                "section_id": "main_document/1/1",
                "namespace_id": "main_document",
                "namespaced_path": "main_document/1/1",
                "clause": "1.1",
                "title": "Clause 1.1",
                "section_kind": "numbered_clause",
                "content_item_indices": [0, 1],
                "source_spans": [
                    {
                        "page": 1,
                        "item_index": 0,
                        "normalized_bbox": [0.1, 0.2, 0.3, 0.4],
                    },
                    {
                        "page": 2,
                        "item_index": 1,
                        "normalized_bbox": [0.2, 0.3, 0.4, 0.5],
                    },
                ],
                "confidence": 0.9,
                "reason": "Fake section.",
            }
        ],
        "issues": [],
        "diagnostics": {"workflow_scope_inputs_count": 1},
    }

    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        parse_result=_parse_result(),
        extract_results={
            "document_structure_extraction": _extract_result(
                {
                    "merged_extraction": extraction_payload,
                }
            ),
            "tables": _extract_result(
                {
                    "tables": [
                        {
                            "table_id": "table-1",
                            "caption": "Table 1",
                            "page": 2,
                            "cells": [],
                        }
                    ]
                }
            ),
        },
    )

    result = assemble_rich_document_package(request)

    structure = result.package.document_structure

    assert [namespace.namespace_id for namespace in structure.namespaces] == [
        "main_document"
    ]
    assert structure.namespaces[0].title == "Main document"
    assert structure.namespaces[0].page_start == 1
    assert structure.namespaces[0].page_end == 2

    assert len(structure.sections) == 1

    section = structure.sections[0]

    assert section.section_id == "main_document/1/1"
    assert section.clause == "1.1"
    assert section.title == "Clause 1.1"
    assert section.path == "main_document/1/1"
    assert section.page_start == 1
    assert section.page_end == 2
    assert section.bbox == [0.1, 0.2, 0.3, 0.4]
    assert section.section_type == "numbered_clause"
    assert section.content["content_item_indices"] == [0, 1]
    assert section.content["confidence"] == 0.9
    assert section.raw["source_spans"][1]["page"] == 2

    assert structure.tables[0].table_id == "table-1"

    assert structure.diagnostics["document_structure_extraction"] == {
        "schema_version": "document_structure_extraction_v1",
        "document_profile": "simple_standard",
        "page_count": 2,
        "numbering_scopes_count": 1,
        "item_classifications_count": 1,
        "sections_count": 1,
        "issues_count": 0,
        "diagnostics": {"workflow_scope_inputs_count": 1},
    }


def test_assembler_keeps_legacy_sections_when_document_structure_extraction_invalid() -> None:
    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        parse_result=_parse_result(),
        extract_results={
            "document_structure_extraction": _extract_result(
                {
                    "merged_extraction": {
                        "schema_version": "document_structure_extraction_v1",
                        "document_profile": "simple_standard",
                        "page_count": 2,
                        "numbering_scopes": [],
                    }
                }
            ),
            "sections": _extract_result(
                {
                    "sections": [
                        {
                            "section_id": "legacy-section",
                            "title": "Legacy section",
                            "path": "1",
                            "content": "Legacy text",
                        }
                    ]
                }
            ),
        },
    )

    result = assemble_rich_document_package(request)

    structure = result.package.document_structure

    assert structure.sections[0].section_id == "legacy-section"
    assert structure.sections[0].content == "Legacy text"
    assert "document_structure_extraction" not in structure.diagnostics


def test_assembler_builds_document_structure_from_raw_response_items_when_top_level_items_empty() -> None:
    parse_result = ParseJobResult.model_construct(
        job_id="parse-job-raw-response-items",
        status="COMPLETED",
        markdown="# Parsed document",
        items=[],
        metadata={"pages": [{"page": 1}] * 10},
        job_metadata={"pdf-pages": 10},
        raw_response={
            "job_id": "parse-job-raw-response-items",
            "items": {
                "pages": [
                    {
                        "page": 9,
                        "page_number": 9,
                        "width": 100.0,
                        "height": 200.0,
                        "page_width": 100.0,
                        "page_height": 200.0,
                        "items": [
                            {
                                "type": "heading",
                                "md": "# \u0427\u0410\u0421\u0422\u042c I \u00ab\u041a\u041b\u0410\u0421\u0421\u0418\u0424\u0418\u041a\u0410\u0426\u0418\u042f\u00bb",
                                "page_number": 9,
                                "page_width": 100.0,
                                "page_height": 200.0,
                                "bbox": [
                                    {"x": 10.0, "y": 10.0, "w": 80.0, "h": 10.0}
                                ],
                            }
                        ],
                    },
                    {
                        "page": 10,
                        "page_number": 10,
                        "width": 100.0,
                        "height": 200.0,
                        "page_width": 100.0,
                        "page_height": 200.0,
                        "items": [
                            {
                                "type": "heading",
                                "md": "# 1. \u041e\u0431\u0449\u0438\u0435 \u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f",
                                "page_number": 10,
                                "page_width": 100.0,
                                "page_height": 200.0,
                                "bbox": [
                                    {"x": 10.0, "y": 20.0, "w": 80.0, "h": 10.0}
                                ],
                            },
                            {
                                "type": "heading",
                                "md": "## 1.1. \u041e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f",
                                "page_number": 10,
                                "page_width": 100.0,
                                "page_height": 200.0,
                                "bbox": [
                                    {"x": 10.0, "y": 30.0, "w": 80.0, "h": 10.0}
                                ],
                            },
                            {
                                "type": "text",
                                "md": "Definition text.",
                                "page_number": 10,
                                "page_width": 100.0,
                                "page_height": 200.0,
                                "bbox": [
                                    {"x": 20.0, "y": 40.0, "w": 70.0, "h": 8.0}
                                ],
                            },
                        ],
                    },
                ]
            },
        },
    )

    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GIMS-RAW-RESPONSE-ITEMS",
        parse_result=parse_result,
        extract_results={},
    )

    result = assemble_rich_document_package(request)

    structure = result.package.document_structure

    assert parse_result.items == []

    assert [namespace.namespace_id for namespace in structure.namespaces] == [
        "front_matter",
        "classification",
    ]

    by_path = {section.path: section for section in structure.sections}

    assert "classification/1/1" in by_path

    section = by_path["classification/1/1"]

    assert section.clause == "1.1"
    assert section.title == "1.1. \u041e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f"
    assert section.section_type == "numbered_section"
    assert section.content == "Definition text."
    assert section.page_start == 10
    assert section.page_end == 10
    assert section.bbox == [0.1, 0.15, 0.8, 0.05]
    assert section.raw["namespaced_path"] == "classification/1/1"

    assert structure.diagnostics["parse_item_structure"]["sections_count"] == 3
    assert structure.diagnostics["parse_item_structure"]["namespaces_count"] == 2


def test_assembler_expands_gost_reference_range_from_target_document_code() -> None:
    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        parse_result=_parse_result(),
        extract_results={
            "references": _extract_result(
                {
                    "references": [
                        {
                            "reference_id": "reference-range",
                            "reference_text": "External standard range",
                            "target_document_code": "\u0413\u041e\u0421\u0422 20862-81- \u0413\u041e\u0421\u0422 20867-81",
                            "reference_type": "normative_reference",
                        }
                    ]
                }
            )
        },
    )

    result = assemble_rich_document_package(request)
    reference = result.package.document_structure.references[0]

    assert reference.target_document_code == "\u0413\u041e\u0421\u0422 20862-81"
    assert reference.target_document_codes == [
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20863-81",
        "\u0413\u041e\u0421\u0422 20864-81",
        "\u0413\u041e\u0421\u0422 20865-81",
        "\u0413\u041e\u0421\u0422 20866-81",
        "\u0413\u041e\u0421\u0422 20867-81",
    ]

def test_assembler_preserves_gost_20868_v2_chunk_container_layers() -> None:
    data = load_gost_20868_v2_chunk_container()
    fixture_sections_by_clause = {
        section["clause"]: section
        for section in data["sections"]
    }

    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="gost_20868_81.pdf",
        document_code=data["document"]["doc_code"],
        parse_result=_parse_result(),
        extract_results=gost_20868_chunk_container_extract_results(data),
    )

    result = assemble_rich_document_package(request)
    structure = result.package.document_structure

    section_clauses = {section.clause for section in structure.sections}
    assert {"title", "1", "6", "6.1", "9"}.issubset(section_clauses)

    title_section = next(
        section
        for section in structure.sections
        if section.clause == "title"
    )
    assert data["document"]["doc_code"] in title_section.content

    assert [image.image_id for image in structure.images] == [
        "figure-1",
        "figure-2",
    ]
    assert structure.images[0].caption == (
        fixture_sections_by_clause["figure-1"]["content"]["caption"]
    )
    assert structure.images[1].caption == (
        fixture_sections_by_clause["figure-2"]["content"]["caption"]
    )

    assert len(structure.tables) == 1
    assert structure.tables[0].table_id == "table-1"
    assert structure.tables[0].caption == fixture_sections_by_clause["table-1"]["title"]
    assert len(structure.tables[0].cells) == 12

    assert len(structure.notes) == 1
    assert structure.notes[0].note_id == "note"
    assert structure.notes[0].text == fixture_sections_by_clause["note"]["content"]["text"]

    assert len(structure.references) == 6
    reference_types = [reference.reference_type for reference in structure.references]
    assert reference_types.count("normative_reference") == 5
    assert reference_types.count("table_reference") == 1

    expected_target_document_codes = {
        reference["target_doc_code"]
        for section in data["sections"]
        for reference in section.get("references") or []
    }
    actual_target_document_codes = {
        reference.target_document_code
        for reference in structure.references
    }
    assert actual_target_document_codes == expected_target_document_codes


def test_assembler_preserves_gost_20868_formula_chunk_container_layer() -> None:
    data = load_gost_20868_formula_chunk_container()
    formula_section = next(
        section
        for section in data["sections"]
        if section["type"] == "formula"
    )
    formula_content = formula_section["content"]

    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="gost_20868_81.pdf",
        document_code=data["document"]["doc_code"],
        parse_result=_parse_result(),
        extract_results=gost_20868_chunk_container_extract_results(data),
    )

    result = assemble_rich_document_package(request)
    structure = result.package.document_structure

    assert len(structure.formulas) == 1
    formula = structure.formulas[0]

    assert formula.formula_id == formula_section["clause"]
    assert formula.expression == formula_content["text"]
    assert formula.latex == formula_content["latex"]
    assert formula.page == formula_section["page"]
    assert formula.parameters == formula_content["parameters"]
    assert formula.raw["raw"] == formula_section


def test_assembler_expands_gost_20868_reference_range_from_fixture_text() -> None:
    data = load_gost_20868_v2_chunk_container()
    range_section = next(
        section
        for section in data["sections"]
        if section["clause"] == "2"
    )
    source_refs = range_section["references"]

    first_code = source_refs[0]["target_doc_code"]
    last_code = source_refs[-1]["target_doc_code"]

    prefix, first_number_year = first_code.split()
    _, last_number_year = last_code.split()

    first_number, year = first_number_year.split("-")
    last_number, last_year = last_number_year.split("-")

    assert year == last_year

    expected_target_document_codes = [
        f"{prefix} {number}-{year}"
        for number in range(int(first_number), int(last_number) + 1)
    ]

    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="gost_20868_81.pdf",
        document_code=data["document"]["doc_code"],
        parse_result=_parse_result(),
        extract_results=gost_20868_chunk_container_extract_results(data),
    )

    result = assemble_rich_document_package(request)
    structure = result.package.document_structure

    reference = next(
        reference
        for reference in structure.references
        if reference.section_id == str(range_section["section_id"])
        and reference.target_document_code == first_code
    )

    assert reference.reference_text == range_section["content"]["text"]
    assert reference.target_document_codes == expected_target_document_codes


def test_assembler_maps_reference_printed_page_to_section_file_page() -> None:
    extraction_payload = {
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
                "confidence": 0.95,
                "reason": "Fake overview.",
            }
        ],
        "item_classifications": [],
        "sections": [
            {
                "section_id": "main_document/4",
                "namespace_id": "main_document",
                "namespaced_path": "main_document/4",
                "clause": "4",
                "title": "Clause 4",
                "section_kind": "numbered_clause",
                "content_item_indices": [0],
                "source_spans": [
                    {
                        "page": 1,
                        "file_page_number": 1,
                        "file_page_index": 0,
                        "item_index": 0,
                        "normalized_bbox": [0.1, 0.2, 0.3, 0.4],
                    }
                ],
                "confidence": 0.9,
                "reason": "Fake section.",
            }
        ],
        "issues": [],
        "diagnostics": {},
    }

    parse_result = ParseJobResult.model_construct(
        job_id="parse-job-1",
        status="COMPLETED",
        markdown="# Test document",
        items=[],
        metadata={"pages": [{}, {}]},
        job_metadata={"pdf-pages": 2},
        raw_response={"job_id": "parse-job-1"},
    )

    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        parse_result=parse_result,
        extract_results={
            "document_structure_extraction": _extract_result(
                {
                    "merged_extraction": extraction_payload,
                }
            ),
            "references": _extract_result(
                {
                    "references": [
                        {
                            "reference_id": "reference-1",
                            "section_id": "4",
                            "reference_text": "GOST 10549-80",
                            "target_document_code": "GOST 10549-80",
                            "reference_type": "standard",
                            "page": 35,
                        }
                    ]
                }
            ),
        },
    )

    result = assemble_rich_document_package(request)
    reference = result.package.document_structure.references[0]

    assert reference.page == 35
    assert reference.printed_page_label == "35"
    assert reference.file_page_number == 1
    assert reference.file_page_index == 0


def test_assembler_filters_self_reference_from_document_structure() -> None:
    request = RichDocumentPackageAssemblyRequest(
        source_pdf_path="source.pdf",
        document_code="GOST 20868-81",
        parse_result=_parse_result(),
        extract_results={
            "references": _extract_result(
                {
                    "references": [
                        {
                            "reference_id": "self-reference",
                            "section_id": "2",
                            "reference_text": "\u0413\u041e\u0421\u0422 20868\u201481",
                            "target_document_code": "\u0413\u041e\u0421\u0422 20868\u201481",
                            "reference_type": "standard",
                        },
                        {
                            "reference_id": "external-reference",
                            "section_id": "2",
                            "reference_text": "\u0413\u041e\u0421\u0422 20862-81",
                            "target_document_code": "\u0413\u041e\u0421\u0422 20862-81",
                            "reference_type": "standard",
                        },
                    ]
                }
            )
        },
    )

    result = assemble_rich_document_package(request)

    references = result.package.document_structure.references

    assert [reference.reference_id for reference in references] == [
        "external-reference"
    ]
    assert references[0].target_document_code == "\u0413\u041e\u0421\u0422 20862-81"
