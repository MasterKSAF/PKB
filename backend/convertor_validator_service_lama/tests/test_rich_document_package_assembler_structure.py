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
    assert structure.table_of_contents == []
    assert structure.nested_documents == []
    assert structure.sections == []
    assert structure.tables == []
    assert structure.images == []
    assert structure.formulas == []
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
