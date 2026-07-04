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
                "result": {"sections": [{"title": "1. Scope"}]},
                "raw_response": {
                    "job": {"id": "extract-job-sections", "status": "COMPLETED"},
                    "extract_result": {"sections": [{"title": "1. Scope"}]},
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

    assert data["artifact_count"] == 9
    assert package["package_name"] == "rich_document_package.json"
    assert package["parse_job_id"] == "parse-job-123"
    assert package["source_pdf_path"] == "document.pdf"
    assert package["document_code"] == "GOST-TEST"

    assert package["parse_result"]["job_id"] == "parse-job-123"
    assert package["extract_results"]["sections"]["job_id"] == "extract-job-sections"

    assert package["artifacts"]["markdown"]["source"] == "parse_result"
    assert package["artifacts"]["markdown"]["content"] == "# Parsed document"

    assert package["artifacts"]["sections"]["source"] == "extract_pass"
    assert package["artifacts"]["sections"]["content"] == {
        "sections": [{"title": "1. Scope"}]
    }

    assert package["artifacts"]["quality_report"]["source"] == "python_validator"
    assert package["artifacts"]["quality_report"]["content"] == {
        "status": "needs_review"
    }

    assert package["artifacts"]["correction_proposals"]["source"] == "python_validator"
    assert package["artifacts"]["correction_proposals"]["content"] == [
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