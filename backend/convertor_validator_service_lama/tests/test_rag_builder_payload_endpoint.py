from fastapi.testclient import TestClient

from convertor_validator_service_lama.api.app import app


client = TestClient(app)


def test_rag_builder_payload_endpoint_returns_downcast_payload() -> None:
    response = client.post(
        "/rag-builder-payload",
        json={
            "parse_job_id": "parse-job-1",
            "source_pdf_path": "source.pdf",
            "document_code": "GOST-TEST",
            "parse_result": {
                "job_id": "parse-job-1",
                "status": "COMPLETED",
                "markdown": "# Test document",
                "items": [],
                "metadata": {
                    "title": "Test document",
                    "page_count": 2,
                },
                "job_metadata": {},
                "raw_response": {},
            },
            "artifacts": {
                "metadata": {
                    "artifact_key": "metadata",
                    "produced_by": "parse_result",
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
                "references": {
                    "artifact_key": "references",
                    "produced_by": "references",
                    "source": "extract_pass",
                    "content": {
                        "references": [
                            {
                                "section_id": "s1",
                                "target_doc_code": "GOST-REF",
                                "type": "normative_reference",
                                "reference_text": "Scope text cites GOST-REF",
                            }
                        ]
                    },
                    "raw_response": {},
                },
            },
            "final_correction_policy": "python_validator_assembler_applies_final_corrections",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["payload"]["metadata"]["schema_name"] == "rag_builder_compatible_payload"
    assert body["payload"]["document"]["document_code"] == "GOST-TEST"
    assert body["payload"]["document"]["title"] == "Test document"
    assert body["payload"]["document"]["page_count"] == 2
    assert body["payload"]["sections"][0]["section_id"] == "s1"
    assert body["payload"]["sections"][0]["title"] == "1. Scope"

    references = body["payload"]["sections"][0]["references"]
    assert len(references) == 1
    assert references[0]["target_doc_code"] == "GOST-REF"
    assert references[0]["type"] == "normative_reference"
    assert references[0]["context"] == "Scope text cites GOST-REF"

    assert body["warnings"] == []


def test_rag_builder_payload_endpoint_returns_warnings_for_minimal_package() -> None:
    response = client.post(
        "/rag-builder-payload",
        json={
            "parse_job_id": "parse-job-1",
            "document_code": "GOST-TEST",
            "parse_result": {
                "job_id": "parse-job-1",
                "status": "COMPLETED",
                "raw_response": {},
            },
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["payload"]["document"]["document_code"] == "GOST-TEST"
    assert body["payload"]["sections"] == []

    warning_codes = {warning["code"] for warning in body["warnings"]}
    assert warning_codes == {
        "missing_document_title",
        "missing_sections",
    }


def test_rag_builder_payload_endpoint_rejects_missing_parse_result() -> None:
    response = client.post(
        "/rag-builder-payload",
        json={
            "parse_job_id": "parse-job-1",
            "document_code": "GOST-TEST",
        },
    )

    assert response.status_code == 422


def test_rag_builder_buildrequest_endpoint_returns_spd_buildrequest_payload() -> None:
    response = client.post(
        "/rag-builder-buildrequest?document_id=420000",
        json={
            "parse_job_id": "parse-job-1",
            "source_pdf_path": "source.pdf",
            "document_code": "GOST-TEST",
            "parse_result": {
                "job_id": "parse-job-1",
                "status": "COMPLETED",
                "markdown": "# Test document",
                "items": [],
                "metadata": {
                    "title": "Test document",
                    "page_count": 2,
                },
                "job_metadata": {},
                "raw_response": {},
            },
            "artifacts": {
                "metadata": {
                    "artifact_key": "metadata",
                    "produced_by": "parse_result",
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
                "references": {
                    "artifact_key": "references",
                    "produced_by": "references",
                    "source": "extract_pass",
                    "content": {
                        "references": [
                            {
                                "section_id": "s1",
                                "target_doc_code": "GOST-REF",
                                "type": "normative_reference",
                                "reference_text": "Scope text cites GOST-REF",
                            }
                        ]
                    },
                    "raw_response": {},
                },
            },
            "final_correction_policy": "python_validator_assembler_applies_final_corrections",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["payload"]["metadata"] == {
        "schema": "schema_registry_for_rag_v2",
        "document_id": 420000,
    }
    assert body["payload"]["document"]["id"] == 420000
    assert body["payload"]["document"]["pkb_code"] == "-1"
    assert body["payload"]["document"]["doc_code"] == "GOST-TEST"
    assert body["payload"]["document"]["title"] == "Test document"

    section = body["payload"]["sections"][0]
    assert section["section_id"] == 1
    assert section["title"] == "1. Scope"
    assert section["level"] == 1
    assert section["path"] == "1"
    assert section["page"] == 1
    assert section["type"] == "text"
    assert section["content"] == {"text": "Scope text"}

    references = section["references"]
    assert len(references) == 1
    assert references[0]["target_doc_code"] == "GOST-REF"
    assert references[0]["type"] == "normative_reference"
    assert references[0]["context"] == "Scope text cites GOST-REF"

    assert body["warnings"] == []
    assert body["gap_report"] == []


def test_rag_builder_buildrequest_endpoint_requires_document_id() -> None:
    response = client.post(
        "/rag-builder-buildrequest",
        json={
            "parse_job_id": "parse-job-1",
            "document_code": "GOST-TEST",
            "parse_result": {
                "job_id": "parse-job-1",
                "status": "COMPLETED",
                "raw_response": {},
            },
        },
    )

    assert response.status_code == 422
