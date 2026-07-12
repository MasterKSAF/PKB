from convertor_validator_service_lama.services.rag_builder_buildrequest_adapter import (
    build_rag_builder_buildrequest_envelope,
    build_rag_builder_buildrequest_payload,
    build_rag_builder_buildrequest_section_shape,
)
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



def test_buildrequest_envelope_closes_metadata_document_gaps() -> None:
    payload = {
        "metadata": {
            "schema_name": "rag_builder_compatible_payload",
        },
        "document": {
            "document_code": "GOST-TEST",
            "title": "Test document",
            "page_count": 2,
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

    buildrequest_payload = build_rag_builder_buildrequest_envelope(
        payload,
        document_id=420000,
        pkb_code="04",
    )

    assert buildrequest_payload["metadata"] == {
        "schema": "schema_registry_for_rag_v2",
        "document_id": 420000,
    }
    assert buildrequest_payload["document"]["id"] == 420000
    assert buildrequest_payload["document"]["pkb_code"] == "04"
    assert buildrequest_payload["document"]["doc_code"] == "GOST-TEST"
    assert buildrequest_payload["document"]["title"] == "Test document"
    assert buildrequest_payload["document"]["page_count"] == 2

    assert build_rag_builder_buildrequest_gap_report(buildrequest_payload) == [
        "sections[0].type",
        "sections[0].content",
    ]



def test_buildrequest_section_shape_closes_section_gaps() -> None:
    payload = {
        "metadata": {
            "schema_name": "rag_builder_compatible_payload",
        },
        "document": {
            "document_code": "GOST-TEST",
            "title": "Test document",
            "page_count": 2,
        },
        "sections": [
            {
                "section_id": "s1",
                "title": "1. Scope",
                "text": "Scope text",
                "level": 1,
                "path": "1",
                "page_start": 1,
                "references": [],
                "raw": {
                    "section_id": 7,
                    "parent_id": None,
                    "clause": "1",
                    "page": 1,
                    "type": "text",
                    "bbox": [0.1, 0.2, 0.8, 0.3],
                },
            }
        ],
    }

    buildrequest_payload = build_rag_builder_buildrequest_envelope(
        payload,
        document_id=420000,
        pkb_code="04",
    )
    buildrequest_payload = build_rag_builder_buildrequest_section_shape(
        buildrequest_payload
    )

    section = buildrequest_payload["sections"][0]
    assert section["section_id"] == 7
    assert section["parent_id"] is None
    assert section["clause"] == "1"
    assert section["title"] == "1. Scope"
    assert section["level"] == 1
    assert section["path"] == "1"
    assert section["page"] == 1
    assert section["bbox"] == [0.1, 0.2, 0.8, 0.3]
    assert section["type"] == "text"
    assert section["content"] == {"text": "Scope text"}
    assert section["references"] == []

    assert build_rag_builder_buildrequest_gap_report(buildrequest_payload) == []



def test_buildrequest_payload_helper_closes_all_gaps() -> None:
    payload = {
        "metadata": {
            "schema_name": "rag_builder_compatible_payload",
        },
        "document": {
            "document_code": "GOST-TEST",
            "title": "Test document",
            "page_count": 2,
        },
        "sections": [
            {
                "section_id": "s1",
                "title": "1. Scope",
                "text": "Scope text",
                "level": 1,
                "path": "1",
                "page_start": 1,
                "references": [
                    {
                        "target_doc_code": "GOST-REF",
                        "type": "normative_reference",
                        "context": "Scope text cites GOST-REF",
                    }
                ],
                "raw": {
                    "section_id": 7,
                    "clause": "1",
                    "page": 1,
                    "type": "text",
                },
            }
        ],
    }

    buildrequest_payload = build_rag_builder_buildrequest_payload(
        payload,
        document_id=420000,
        pkb_code="04",
    )

    assert build_rag_builder_buildrequest_gap_report(buildrequest_payload) == []
    assert buildrequest_payload["metadata"]["document_id"] == 420000
    assert buildrequest_payload["document"]["doc_code"] == "GOST-TEST"

    section = buildrequest_payload["sections"][0]
    assert section["section_id"] == 7
    assert section["clause"] == "1"
    assert section["type"] == "text"
    assert section["content"] == {"text": "Scope text"}
    assert section["references"] == [
        {
            "target_doc_code": "GOST-REF",
            "type": "normative_reference",
            "context": "Scope text cites GOST-REF",
        }
    ]



def test_buildrequest_payload_defaults_missing_pkb_code_to_minus_one() -> None:
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
                "section_id": 1,
                "title": "1. Scope",
                "text": "Scope text",
                "level": 1,
                "path": "1",
            }
        ],
    }

    buildrequest_payload = build_rag_builder_buildrequest_payload(
        payload,
        document_id=420000,
    )

    assert buildrequest_payload["document"]["pkb_code"] == "-1"
    assert build_rag_builder_buildrequest_gap_report(buildrequest_payload) == []
