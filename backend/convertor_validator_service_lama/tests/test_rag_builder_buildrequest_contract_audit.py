from convertor_validator_service_lama.services.rag_builder_contract_audit import (
    build_rag_builder_buildrequest_gap_report,
)


def test_buildrequest_gap_report_detects_current_downcast_payload_gaps() -> None:
    payload = {
        "metadata": {
            "schema_name": "rag_builder_compatible_payload",
        },
        "document": {
            "document_code": "GOST-TEST",
            "title": "Test document",
        },
        "sections": [
            {
                "section_id": "s1",
                "title": "1. Scope",
                "text": "Scope text",
                "level": 1,
                "path": "1",
                "references": [],
            }
        ],
    }

    assert build_rag_builder_buildrequest_gap_report(payload) == [
        "metadata.schema",
        "metadata.document_id",
        "document.id",
        "document.pkb_code",
        "document.doc_code",
        "sections[0].type",
        "sections[0].content",
    ]


def test_buildrequest_gap_report_accepts_minimal_spd_builder_shape() -> None:
    payload = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 420000,
        },
        "document": {
            "id": 420000,
            "pkb_code": "04",
            "doc_code": "GOST-TEST",
            "title": "Test document",
        },
        "sections": [
            {
                "section_id": 1,
                "level": 1,
                "path": "1",
                "type": "text",
                "content": {"text": "Scope text"},
                "references": [],
            }
        ],
    }

    assert build_rag_builder_buildrequest_gap_report(payload) == []
