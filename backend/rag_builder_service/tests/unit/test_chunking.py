from rag_builder.chunking.service import ChunkingService
from rag_builder.models.contracts import ProtectedSpan, Section



def test_chunking_splits_to_1024_tokens() -> None:
    service = ChunkingService()
    text = "w " * 2400
    section = Section(
        section_id=1,
        document_id=1,
        clause="1",
        title=None,
        level=1,
        path="1",
        page=1,
        type="text",
        content={"text": text},
    )
    chunks = service.build_chunks(section.document_id, [section], [], "semantic_1024")
    assert len(chunks) == 3
    assert all(len(c.content.split()) <= 1024 for c in chunks)



def test_table_to_markdown_chunk() -> None:
    service = ChunkingService()
    section = Section(
        section_id=2,
        document_id=2,
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
    chunks = service.build_chunks(section.document_id, [section], [ProtectedSpan(section_id=2, start_offset=0, end_offset=3)], "semantic_1024")
    assert len(chunks) == 1
    assert "| A |" in chunks[0].content
