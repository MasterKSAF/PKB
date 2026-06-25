# tests/unit/test_chunking.py

import pytest
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
        },
        "document": {
            "id": 420000,
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
    long_text = " ".join(
        f"Предложение номер {i}. Это тестовый текст для проверки нарезки."
        for i in range(300)
    )

    data = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 1,
        },
        "document": {
            "id": 1,
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

    assert chunks[0].content != chunks[1].content

def test_chunking_uses_semantic_1024_by_default(monkeypatch):
    monkeypatch.setattr(
        "rag_builder.chunking.service.settings.CHUNK_STRATEGY",
        "semantic_1024",
    )

    service = ChunkingService()

    assert service.chunk_strategy == "semantic_1024"
    assert service.MAX_CHUNK_CHARS == 4000
    assert service.OVERLAP_RATIO == 0.2
    assert service.prefer_sentence_boundary is True

def test_chunking_supports_semantic_512():
    service = ChunkingService(chunk_strategy="semantic_512")

    assert service.chunk_strategy == "semantic_512"
    assert service.MAX_CHUNK_CHARS == 2000
    assert service.OVERLAP_RATIO == 0.2
    assert service.prefer_sentence_boundary is True

def test_chunking_supports_fixed_256():
    service = ChunkingService(chunk_strategy="fixed_256")

    assert service.chunk_strategy == "fixed_256"
    assert service.MAX_CHUNK_CHARS == 1000
    assert service.OVERLAP_RATIO == 0.1
    assert service.prefer_sentence_boundary is False

def test_chunking_rejects_unknown_strategy():
    with pytest.raises(ValueError, match="Unsupported CHUNK_STRATEGY"):
        ChunkingService(chunk_strategy="unknown_strategy")


def test_protected_span_is_not_split_between_chunks():
    prefix = "A " * 450
    protected_block = (
            "BEGIN_PROTECTED "
            + ("Z " * 125)
            + "END_PROTECTED"
    )
    suffix = "B " * 600

    text = prefix + protected_block + suffix

    span_start = len(prefix)
    span_end = span_start + len(protected_block)

    data = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 1,
        },
        "document": {
            "id": 1,
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
                    "text": text,
                },
                "references": [],
            }
        ],
        "protected_spans": [
            {
                "section_id": 1,
                "start_offset": span_start,
                "end_offset": span_end,
                "reason": "test protected block",
            }
        ],
        "terminology": [],
        "options": {},
    }

    request = BuildRequest.model_validate(data)

    service = ChunkingService(chunk_strategy="fixed_256")
    service.MAX_CHUNK_CHARS = 1000
    service.OVERLAP_RATIO = 0.0

    chunks = service.build_chunks(request)

    assert len(chunks) > 1
    assert any(protected_block in chunk.content for chunk in chunks)

    for chunk in chunks:
        contains_start = "BEGIN_PROTECTED" in chunk.content
        contains_end = "END_PROTECTED" in chunk.content

        if contains_start or contains_end:
            assert protected_block in chunk.content


def test_protected_span_from_other_section_is_ignored():
    prefix = "A " * 450
    protected_block = (
            "BEGIN_PROTECTED "
            + ("Z " * 125)
            + "END_PROTECTED"
    )
    suffix = "B " * 600

    text = prefix + protected_block + suffix

    span_start = len(prefix)
    span_end = span_start + len(protected_block)

    data = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 1,
        },
        "document": {
            "id": 1,
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
                    "text": text,
                },
                "references": [],
            }
        ],
        "protected_spans": [
            {
                "section_id": 2,
                "start_offset": span_start,
                "end_offset": span_end,
                "reason": "span belongs to another section",
            }
        ],
        "terminology": [],
        "options": {},
    }

    request = BuildRequest.model_validate(data)

    service = ChunkingService(chunk_strategy="fixed_256")
    service.MAX_CHUNK_CHARS = 1000
    service.OVERLAP_RATIO = 0.0

    chunks = service.build_chunks(request)

    assert len(chunks) > 1
    assert not any(protected_block in chunk.content for chunk in chunks)
    assert any(
        "BEGIN_PROTECTED" in chunk.content
        and "END_PROTECTED" not in chunk.content
        for chunk in chunks
    )
