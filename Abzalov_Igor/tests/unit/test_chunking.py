from uuid import uuid4

from rag_builder.chunking.service import ChunkingService
from rag_builder.models.contracts import ProtectedSpan, Section


def test_chunking_splits_to_512_tokens() -> None:
    service = ChunkingService()
    text = "w " * 1200
    section = Section(
        section_id=1,
        document_id=uuid4(),
        clause="1",
        title=None,
        level=1,
        path="1",
        page=1,
        type="section",
        content={"text": text},
    )
    chunks = service.build_chunks(str(section.document_id), [section], [], "semantic_512")
    assert len(chunks) == 3
    assert all(len(c.content.split()) <= 512 for c in chunks)


def test_table_to_markdown_chunk() -> None:
    service = ChunkingService()
    section = Section(
        section_id=2,
        document_id=uuid4(),
        clause="2",
        title=None,
        level=1,
        path="2",
        page=1,
        type="table",
        content={
            "columns": [{"name": "a", "header": "A"}],
            "rows": [{"cells": {"a": {"value": 1}}}],
        },
    )
    chunks = service.build_chunks(str(section.document_id), [section], [ProtectedSpan(section_id=2, start_offset=0, end_offset=3)], "semantic_512")
    assert len(chunks) == 1
    assert "| A |" in chunks[0].content
