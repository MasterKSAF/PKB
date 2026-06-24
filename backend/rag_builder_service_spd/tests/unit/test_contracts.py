# tests/unit/test_contracts.py

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from rag_builder.models.contracts import BuildRequest

def test_load_gost_container():
    json_path = Path("examples/gost_20868_81.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    request = BuildRequest.model_validate(data)

    assert request.document.id == 420000
    assert request.document.document_version_id == 420001

    assert len(request.sections) > 0


def test_document_id_is_required():
    payload = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_version_id": 420001,
        },
        "document": {
            "id": 420000,
            "version_id": 420001,
            "pkb_code": "04",
            "doc_code": "ГОСТ 20868-81",
            "title": "Test",
        },
        "sections": [],
    }

    with pytest.raises(ValidationError):
        BuildRequest.model_validate(payload)


def test_document_version_id_is_optional_for_input_contract():
    payload = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 420000,
        },
        "document": {
            "id": 420000,
            "pkb_code": "04",
            "doc_code": "ГОСТ 20868-81",
            "title": "Test",
        },
        "sections": [],
    }

    request = BuildRequest.model_validate(payload)

    assert request.metadata.document_version_id == 420000
    assert request.document.document_version_id == 420000


def test_sections_are_required():
    payload = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 420000,
            "document_version_id": 420001,
        },
        "document": {
            "id": 420000,
            "version_id": 420001,
            "pkb_code": "04",
            "doc_code": "ГОСТ 20868-81",
            "title": "Test",
        },
    }

    with pytest.raises(ValidationError):
        BuildRequest.model_validate(payload)


def test_build_request_accepts_flat_registry_payload():
    payload = {
        "document_id": 420000,
        "sections": [
            {
                "section_id": 1,
                "document_id": 420000,
                "parent_id": None,
                "clause": "1",
                "title": None,
                "level": 1,
                "path": "1",
                "page": 1,
                "bbox": None,
                "type": "text",
                "content": {
                    "text": "Настоящий стандарт распространяется...",
                },
            }
        ],
        "protected_spans": [],
        "options": {
            "strategy": "semantic_1024",
        },
    }

    request = BuildRequest.model_validate(payload)

    assert request.metadata.document_id == 420000
    assert request.metadata.document_version_id == 420000
    assert request.document.id == 420000
    assert request.document.document_version_id == 420000
    assert request.sections[0].section_id == 1
    assert request.protected_spans == []
    assert request.options["strategy"] == "semantic_1024"
