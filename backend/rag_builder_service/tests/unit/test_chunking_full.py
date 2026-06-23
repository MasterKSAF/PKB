"""Extended chunking tests — no DB, no vector required."""

import pytest

from rag_builder.chunking.service import ChunkingService
from rag_builder.models.contracts import ProtectedSpan, Section


@pytest.fixture
def service() -> ChunkingService:
    return ChunkingService()


def make_section(
    section_id: int = 1,
    document_id: int = 1,
    type_: str = "text",
    content: dict | None = None,
    page: int | None = 1,
) -> Section:
    return Section(
        section_id=section_id,
        document_id=document_id,
        clause="1",
        title=None,
        level=1,
        path=str(section_id),
        page=page,
        type=type_,  # type: ignore[arg-type]
        content=content or {"text": "default content"},
    )


class TestChunkingTextType:
    def test_empty_text_returns_empty_list(self, service: ChunkingService) -> None:
        section = make_section(content={"text": ""})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert chunks == []

    def test_whitespace_only_text_returns_empty(self, service: ChunkingService) -> None:
        section = make_section(content={"text": "   \n  \t  "})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert chunks == []

    def test_short_text_no_split(self, service: ChunkingService) -> None:
        section = make_section(content={"text": "hello world"})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert chunks[0].content == "hello world"
        assert chunks[0].chunk_index == 0

    def test_long_text_splits_across_chunks(self, service: ChunkingService) -> None:
        text = "word " * 2500
        section = make_section(content={"text": text})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 3  # 2500 words / 1024 ≈ 2.44 → 3 chunks
        assert all(len(c.content.split()) <= 1024 for c in chunks)
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1
        assert chunks[2].chunk_index == 2

    def test_exact_max_tokens_no_split(self, service: ChunkingService) -> None:
        text = "data " * 1024
        section = make_section(content={"text": text})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert len(chunks[0].content.split()) == 1024

    def test_single_word(self, service: ChunkingService) -> None:
        section = make_section(content={"text": "hello"})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert chunks[0].content == "hello"


class TestChunkingNonText:
    def test_table_with_markdown(self, service: ChunkingService) -> None:
        section = make_section(
            type_="table",
            content={"markdown": "| A | B |\n|---|---|\n| 1 | 2 |"},
        )
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert "| A | B |" in chunks[0].content

    def test_table_with_columns_rows(self, service: ChunkingService) -> None:
        section = make_section(
            type_="table",
            content={
                "columns": [{"name": "x", "header": "X"}],
                "rows": [{"cells": {"x": {"value": 10}}}],
            },
        )
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert "| X |" in chunks[0].content
        assert "| 10 |" in chunks[0].content

    def test_list_with_markdown(self, service: ChunkingService) -> None:
        section = make_section(
            type_="list",
            content={"markdown": "- item1\n- item2"},
        )
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert "- item1" in chunks[0].content

    def test_list_with_items(self, service: ChunkingService) -> None:
        section = make_section(
            type_="list",
            content={"items": ["a", "b", "c"]},
        )
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert chunks[0].content == "- a\n- b\n- c"

    def test_list_empty_items(self, service: ChunkingService) -> None:
        section = make_section(type_="list", content={"items": []})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert chunks[0].content == ""

    def test_image_with_caption(self, service: ChunkingService) -> None:
        section = make_section(
            type_="image",
            content={"caption": "Figure 1", "description": "A description"},
        )
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert "Figure 1" in chunks[0].content
        assert "A description" in chunks[0].content

    def test_image_with_markdown(self, service: ChunkingService) -> None:
        section = make_section(
            type_="image",
            content={"markdown": "![alt](img.png)"},
        )
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert "![alt](img.png)" in chunks[0].content

    def test_image_no_caption_empty(self, service: ChunkingService) -> None:
        section = make_section(type_="image", content={})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert chunks[0].content == ""

    def test_formula_with_latex(self, service: ChunkingService) -> None:
        section = make_section(
            type_="formula",
            content={"latex": "E=mc^2", "meaning": "energy equals mass times c squared"},
        )
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert "E=mc^2" in chunks[0].content
        assert "energy" in chunks[0].content

    def test_formula_with_markdown(self, service: ChunkingService) -> None:
        section = make_section(
            type_="formula",
            content={"markdown": "$$E=mc^2$$"},
        )
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert "$$E=mc^2$$" in chunks[0].content

    def test_textBlock_falls_through_to_text(self, service: ChunkingService) -> None:
        section = make_section(type_="textBlock", content={"text": "block content"})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert chunks[0].content == "block content"

    def test_headerFooter_falls_through_to_text(self, service: ChunkingService) -> None:
        section = make_section(type_="headerFooter", content={"text": "header"})
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert len(chunks) == 1
        assert chunks[0].content == "header"


class TestChunkingProtectedSpans:
    def test_protected_span_extended_chunk(self, service: ChunkingService) -> None:
        """If protected_span end_offset > raw_chunk text, next word is included."""
        text = "aaa " * 100 + "PROTECTED " + "bbb " * 100
        section = make_section(content={"text": text})
        # Set span start after the first word, end well beyond the raw chunk
        span = ProtectedSpan(section_id=1, start_offset=1, end_offset=10_000)
        chunks = service.build_chunks(1, [section], [span], "semantic_1024")
        # Should produce chunks, with protected span causing coalescing
        assert len(chunks) >= 1
        # The protected chunk should contain at least "PROTECTED"
        assert any("PROTECTED" in c.content for c in chunks)

    def test_protected_span_does_not_affect_unrelated_sections(self, service: ChunkingService) -> None:
        text = "x " * 50
        s1 = make_section(section_id=1, content={"text": text})
        s2 = make_section(section_id=2, content={"text": "important " * 50})
        span = ProtectedSpan(section_id=1, start_offset=0, end_offset=9999)
        chunks = service.build_chunks(1, [s1, s2], [span], "semantic_1024")
        s1_chunks = [c for c in chunks if c.section_id == 1]
        s2_chunks = [c for c in chunks if c.section_id == 2]
        assert len(s1_chunks) == 1  # coalesced by protected span
        assert len(s2_chunks) == 1  # fits in one chunk


class TestChunkingMultipleSections:
    def test_two_sections_produce_separate_chunks(self, service: ChunkingService) -> None:
        s1 = make_section(section_id=1, content={"text": "section one"})
        s2 = make_section(section_id=2, content={"text": "section two"})
        chunks = service.build_chunks(1, [s1, s2], [], "semantic_1024")
        assert len(chunks) == 2
        assert chunks[0].section_id == 1
        assert chunks[1].section_id == 2

    def test_chunks_have_correct_document_id(self, service: ChunkingService) -> None:
        section = make_section(document_id=42)
        chunks = service.build_chunks(42, [section], [], "semantic_1024")
        assert all(c.document_id == 42 for c in chunks)

    def test_chunks_have_correct_strategy(self, service: ChunkingService) -> None:
        section = make_section()
        chunks = service.build_chunks(1, [section], [], "custom_strategy")
        assert all(c.strategy == "custom_strategy" for c in chunks)

    def test_chunks_have_page_from_section(self, service: ChunkingService) -> None:
        section = make_section(page=5)
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert all(c.page == 5 for c in chunks)

    def test_chunks_with_indexing_txn_id(self, service: ChunkingService) -> None:
        from uuid import uuid4
        txn_id = uuid4()
        section = make_section()
        chunks = service.build_chunks(1, [section], [], "semantic_1024", indexing_txn_id=txn_id)
        assert all(c.indexing_txn_id == txn_id for c in chunks)

    def test_chunks_without_indexing_txn_id(self, service: ChunkingService) -> None:
        section = make_section()
        chunks = service.build_chunks(1, [section], [], "semantic_1024")
        assert all(c.indexing_txn_id is None for c in chunks)
