# tests/unit/test_chunking.py

import json
from pathlib import Path

from rag_builder.chunking.service import ChunkingService
from rag_builder.models.contracts import BuildRequest


def test_chunking_keeps_citation_metadata():
    json_path = Path("examples/gost_20868_81.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    request = BuildRequest.model_validate(data)

    service = ChunkingService()
    chunks = service.build_chunks(request)

    assert len(chunks) == 3

    first = chunks[0]

    assert first.document_id == 420000
    assert first.document_version_id == 420001
    assert first.section_id == 1
    assert first.clause == "1"
    assert first.page == 1
    assert first.bbox == [0.12, 0.18, 0.88, 0.26]
    assert first.chunk_type == "text"
    assert "Настоящий стандарт" in first.content


def test_chunking_keeps_references():
    json_path = Path("examples/gost_20868_81.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    request = BuildRequest.model_validate(data)

    service = ChunkingService()
    chunks = service.build_chunks(request)

    second = chunks[1]

    assert second.clause == "2"
    assert second.metadata["references"][0]["type"] == "range"
    assert second.metadata["references"][0]["target_doc_code"] == "ГОСТ 20862-81 – ГОСТ 20867-81"


def test_empty_text_section_is_skipped():
    data = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 420000,
            "document_version_id": 420001,
        },
        "document": {
            "id": 420000,
            "document_version_id": 420001,
            "pkb_code": "04",
            "doc_code": "ГОСТ 20868-81",
            "title": "Test",
        },
        "sections": [
            {
                "section_id": 1,
                "parent_id": None,
                "clause": "1",
                "title": None,
                "level": 1,
                "path": "1",
                "page": 1,
                "bbox": None,
                "type": "text",
                "content": {"text": ""},
                "references": [],
            }
        ],
        "terminology": [],
        "options": {},
    }

    request = BuildRequest.model_validate(data)

    service = ChunkingService()
    chunks = service.build_chunks(request)

    assert chunks == []

def test_long_text_is_split_into_multiple_chunks():
    long_text = "A " * 3000

    data = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 1,
            "document_version_id": 1,
        },
        "document": {
            "id": 1,
            "document_version_id": 1,
            "pkb_code": "04",
            "doc_code": "TEST",
            "title": "Test",
        },
        "sections": [
            {
                "section_id": 1,
                "parent_id": None,
                "clause": "1",
                "title": None,
                "level": 1,
                "path": "1",
                "page": 1,
                "bbox": None,
                "type": "text",
                "content": {
                    "text": long_text,
                },
                "references": [],
            }
        ],
        "terminology": [],
        "options": {},
    }

    request = BuildRequest.model_validate(data)

    service = ChunkingService()
    chunks = service.build_chunks(request)

    assert len(chunks) > 1

    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1

    assert all(
        len(chunk.content) <= service.MAX_CHUNK_CHARS
        for chunk in chunks
    )

