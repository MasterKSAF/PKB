from fastapi.testclient import TestClient

from convertor_validator_service_lama.api.app import app


client = TestClient(app)


def _payload() -> dict:
    return {
        "source_pdf_path": "document.pdf",
        "document_code": "GOST-TEST",
        "parse_result": {
            "job_id": "parse-job-123",
            "status": "COMPLETED",
            "markdown": "# Parsed document",
            "items": [{"type": "heading", "value": "1. Scope"}],
            "metadata": {"page_count": 2},
            "job_metadata": {"duration_seconds": 10},
            "raw_response": {
                "job": {"id": "parse-job-123", "status": "COMPLETED"},
                "result": {"markdown": "# Parsed document"},
            },
        },
        "extract_results": {
            "sections": {
                "job_id": "extract-job-sections",
                "pass_name": "sections",
                "status": "COMPLETED",
                "result": {
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
                },
                "raw_response": {
                    "job": {"id": "extract-job-sections", "status": "COMPLETED"},
                    "extract_result": {
                        "sections": [
                            {
                                "section_id": "section-1",
                                "title": "1. Scope",
                            }
                        ]
                    },
                },
            },
            "tables": {
                "job_id": "extract-job-tables",
                "pass_name": "tables",
                "status": "COMPLETED",
                "result": {
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
                },
                "raw_response": {
                    "job": {"id": "extract-job-tables", "status": "COMPLETED"},
                    "extract_result": {"tables": [{"table_id": "table-1"}]},
                },
            },
            "cross_references": {
                "job_id": "extract-job-cross-references",
                "pass_name": "cross_references",
                "status": "COMPLETED",
                "result": {
                    "cross_references": [
                        {
                            "reference_id": "ref-1",
                            "source_id": "section-1",
                            "target_document_code": "ГОСТ 123",
                            "reference_type": "normative_reference",
                            "context": "See ГОСТ 123",
                        }
                    ]
                },
                "raw_response": {
                    "job": {
                        "id": "extract-job-cross-references",
                        "status": "COMPLETED",
                    },
                    "extract_result": {"cross_references": [{"reference_id": "ref-1"}]},
                },
            },
            "validation_critic": {
                "job_id": "extract-job-validation",
                "pass_name": "validation_critic",
                "status": "COMPLETED",
                "result": {
                    "quality_report": {"status": "needs_review"},
                    "correction_proposals": [
                        {"field": "title", "proposal": "fix spacing"}
                    ],
                },
                "raw_response": {
                    "job": {"id": "extract-job-validation", "status": "COMPLETED"},
                    "extract_result": {
                        "quality_report": {"status": "needs_review"},
                        "correction_proposals": [
                            {"field": "title", "proposal": "fix spacing"}
                        ],
                    },
                },
            },
        },
    }


def test_rich_document_package_endpoint_returns_assembled_package() -> None:
    response = client.post("/rich-document-package", json=_payload())

    assert response.status_code == 200

    data = response.json()
    package = data["package"]

    assert data["artifact_count"] == 11
    assert package["package_name"] == "rich_document_package.json"
    assert package["parse_job_id"] == "parse-job-123"
    assert package["source_pdf_path"] == "document.pdf"
    assert package["document_code"] == "GOST-TEST"

    assert package["parse_result"]["job_id"] == "parse-job-123"
    assert package["extract_results"]["sections"]["job_id"] == "extract-job-sections"

    assert package["artifacts"]["markdown"]["source"] == "parse_result"
    assert package["artifacts"]["markdown"]["content"] == "# Parsed document"

    assert package["artifacts"]["sections"]["source"] == "extract_pass"
    assert package["artifacts"]["sections"]["content"]["sections"][0]["title"] == "1. Scope"

    assert package["artifacts"]["tables"]["source"] == "extract_pass"
    assert package["artifacts"]["tables"]["content"]["tables"][0]["table_id"] == "table-1"

    assert package["artifacts"]["cross_references"]["source"] == "extract_pass"
    assert (
        package["artifacts"]["cross_references"]["content"]["cross_references"][0][
            "target_document_code"
        ]
        == "ГОСТ 123"
    )

    assert package["artifacts"]["quality_report"]["source"] == "python_validator"
    assert package["artifacts"]["quality_report"]["content"] == {
        "status": "needs_review"
    }

    assert package["artifacts"]["correction_proposals"]["source"] == "python_validator"
    assert package["artifacts"]["correction_proposals"]["content"] == [
        {"field": "title", "proposal": "fix spacing"}
    ]


def test_rich_document_package_endpoint_exposes_document_structure_contract() -> None:
    response = client.post("/rich-document-package", json=_payload())

    assert response.status_code == 200

    package = response.json()["package"]
    structure = package["document_structure"]

    assert structure["sections"][0]["section_id"] == "section-1"
    assert structure["sections"][0]["title"] == "1. Scope"
    assert structure["sections"][0]["content"] == {"text": "Scope text"}

    assert structure["tables"][0]["table_id"] == "table-1"
    assert structure["tables"][0]["caption"] == "Table 1"
    assert structure["tables"][0]["cells"][0]["text"] == "Cell text"
    assert (
        structure["tables"][0]["cells"][0]["images"][0]["image_id"]
        == "image-in-cell-1"
    )
    assert (
        structure["tables"][0]["cells"][0]["formulas"][0]["expression"]
        == "a=b"
    )

    assert structure["cross_references"][0]["reference_id"] == "ref-1"
    assert structure["cross_references"][0]["source_id"] == "section-1"
    assert structure["cross_references"][0]["target_document_code"] == "ГОСТ 123"

    assert structure["quality_report"] == {"status": "needs_review"}
    assert structure["correction_proposals"] == [
        {"field": "title", "proposal": "fix spacing"}
    ]


def test_rich_document_package_endpoint_rejects_missing_parse_result() -> None:
    payload = _payload()
    payload.pop("parse_result")

    response = client.post("/rich-document-package", json=payload)

    assert response.status_code == 422


def test_rich_document_package_endpoint_rejects_empty_parse_job_id() -> None:
    payload = _payload()
    payload["parse_result"]["job_id"] = ""

    response = client.post("/rich-document-package", json=payload)

    assert response.status_code == 422


def test_rich_document_package_endpoint_exposes_document_structure_extraction() -> None:
    payload = _payload()

    payload["extract_results"]["document_structure_extraction"] = {
        "job_id": "extract-job-document-structure",
        "pass_name": "sections",
        "status": "COMPLETED",
        "result": {
            "merged_extraction": {
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
                                "normalized_bbox": [0.1, 0.2, 0.3, 0.4],
                            }
                        ],
                        "confidence": 0.9,
                        "reason": "Fake section.",
                    }
                ],
                "diagnostics": {"workflow_scope_inputs_count": 1},
            }
        },
        "raw_response": {},
    }

    response = client.post("/rich-document-package", json=payload)

    assert response.status_code == 200

    structure = response.json()["package"]["document_structure"]

    assert structure["namespaces"][0]["namespace_id"] == "main_document"
    assert structure["sections"][0]["section_id"] == "main_document/1"
    assert structure["sections"][0]["path"] == "main_document/1"
    assert structure["sections"][0]["section_type"] == "numbered_clause"
    assert structure["sections"][0]["bbox"] == [0.1, 0.2, 0.3, 0.4]
    assert structure["diagnostics"]["document_structure_extraction"]["sections_count"] == 1
