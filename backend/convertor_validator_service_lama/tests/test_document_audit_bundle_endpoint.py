from fastapi.testclient import TestClient

from convertor_validator_service_lama.api.app import app


client = TestClient(app)


def _rich_package_payload() -> dict:
    return {
        "parse_job_id": "parse-job-1",
        "source_pdf_path": "source.pdf",
        "document_code": "GOST-TEST",
        "parse_result": {
            "job_id": "parse-job-1",
            "status": "COMPLETED",
            "markdown": "# Test document",
            "items": [],
            "metadata": {},
            "job_metadata": {},
            "raw_response": {},
        },
        "artifacts": {
            "metadata": {
                "artifact_key": "metadata",
                "produced_by": "registry",
                "source": "parse_result",
                "content": {
                    "title": "Test document",
                    "page_count": 2,
                },
                "raw_response": {},
            },
            "sections": {
                "artifact_key": "sections",
                "produced_by": "sections",
                "source": "extract_pass",
                "content": {
                    "sections": [
                        {
                            "section_id": "s1",
                            "title": "1. Scope",
                            "text": "Scope text",
                            "level": 1,
                            "page_start": 1,
                            "page_end": 1,
                            "path": "1",
                        }
                    ]
                },
                "raw_response": {},
            },
            "images": {
                "artifact_key": "images",
                "produced_by": "images",
                "source": "extract_pass",
                "content": {
                    "images": [
                        {
                            "image_id": "figure-1",
                            "caption": "Figure 1",
                            "page": 1,
                            "storage_uri": "assets/images/figure-1.png",
                        }
                    ]
                },
                "raw_response": {},
            },
            "formulas": {
                "artifact_key": "formulas",
                "produced_by": "formulas",
                "source": "extract_pass",
                "content": {
                    "formulas": [
                        {
                            "formula_id": "formula-1",
                            "expression": "D = L / 2",
                            "latex": "D = \\frac{L}{2}",
                            "page": 1,
                        }
                    ]
                },
                "raw_response": {},
            },
        },
        "document_structure": {
            "images": [
                {
                    "image_id": "figure-1",
                    "caption": "Figure 1",
                    "page": 1,
                    "storage_uri": "assets/images/figure-1.png",
                }
            ],
            "formulas": [
                {
                    "formula_id": "formula-1",
                    "expression": "D = L / 2",
                    "latex": "D = \\frac{L}{2}",
                    "page": 1,
                }
            ],
            "quality_report": {
                "status": "needs_review",
            },
            "diagnostics": {
                "source": "test",
            },
        },
        "final_correction_policy": "python_validator_assembler_applies_final_corrections",
    }


def test_document_audit_bundle_endpoint_returns_conversion_bundle() -> None:
    response = client.post(
        "/document-audit-bundle?document_id=420000",
        json=_rich_package_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["bundle_schema"] == "document_conversion_audit_bundle_v1"
    assert body["input"] == {
        "source_pdf_path": "source.pdf",
        "document_code": "GOST-TEST",
        "parse_job_id": "parse-job-1",
    }

    service_1 = body["service_1_rich"]
    assert service_1["rich_document_package"]["document_code"] == "GOST-TEST"
    assert service_1["parse_result"]["job_id"] == "parse-job-1"
    assert service_1["extract_artifacts"]["sections"]["artifact_key"] == "sections"
    assert service_1["asset_references"]["images"][0]["image_id"] == "figure-1"
    assert service_1["asset_references"]["formulas"][0]["formula_id"] == "formula-1"
    assert service_1["quality_report"] == {"status": "needs_review"}
    assert service_1["diagnostics"] == {"source": "test"}

    service_2 = body["service_2_rag_builder"]
    assert service_2["rag_builder_buildrequest"]["metadata"] == {
        "schema": "schema_registry_for_rag_v2",
        "document_id": 420000,
    }
    assert service_2["rag_builder_buildrequest"]["document"]["id"] == 420000
    assert service_2["rag_builder_buildrequest"]["document"]["pkb_code"] == "-1"
    assert service_2["rag_builder_buildrequest"]["document"]["doc_code"] == "GOST-TEST"
    assert service_2["rag_builder_buildrequest"]["document"]["title"] == "Test document"
    assert service_2["rag_builder_contract_gap_report"] == []
    assert service_2["warnings"] == []

    assert "audit_prompt_md" in body["llm_audit"]
    assert body["llm_audit"]["audit_result_md"] is None


def test_document_audit_bundle_endpoint_requires_document_id() -> None:
    response = client.post(
        "/document-audit-bundle",
        json=_rich_package_payload(),
    )

    assert response.status_code == 422
