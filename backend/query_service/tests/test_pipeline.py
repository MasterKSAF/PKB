import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.clients.registry_client import normalize_term, enrich_query
from app.clients.rag_client import Chunk, search
from app.services.pipeline import _build_llm_mock, _enrich_citations


# ── registry_client ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_registry_normalize_known_term():
    result = await normalize_term("обшивка")
    assert result == "обшивка корпуса"


@pytest.mark.asyncio
async def test_registry_normalize_unknown_term():
    result = await normalize_term("xyz_неизвестный_термин_123")
    assert result == "xyz_неизвестный_термин_123"


@pytest.mark.asyncio
async def test_registry_normalize_case_insensitive():
    result = await normalize_term("ОБШИВКА")
    assert result == "обшивка корпуса"


@pytest.mark.asyncio
async def test_enrich_query_returns_tuple():
    enriched, synonyms = await enrich_query("толщина обшивки")
    assert isinstance(enriched, str)
    assert isinstance(synonyms, list)
    assert len(enriched) > 0


@pytest.mark.asyncio
async def test_enrich_query_normalizes_words():
    enriched, synonyms = await enrich_query("толщина обшивки")
    assert "толщина листа" in enriched or "обшивка корпуса" in enriched


@pytest.mark.asyncio
async def test_enrich_query_adds_synonyms_for_known_terms():
    _, synonyms = await enrich_query("ледовый пояс корпуса")
    assert len(synonyms) > 0


# ── rag_client ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rag_search_mock_returns_chunks():
    chunks = await search("Arc4 толщина")
    assert len(chunks) > 0
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
    assert chunk.document_id
    assert chunk.score > 0
    assert chunk.content
    assert chunk.excerpt
    assert chunk.section_id is not None
    assert chunk.page > 0


@pytest.mark.asyncio
async def test_rag_search_top_k_limits_results():
    chunks = await search("Arc4", top_k=1)
    assert len(chunks) == 1


@pytest.mark.asyncio
async def test_rag_search_chunk_has_all_fields():
    chunks = await search("Arc4")
    chunk = chunks[0]
    assert chunk.chunk_id
    assert chunk.document_title
    assert chunk.clause
    assert chunk.section_title
    assert 0.0 <= chunk.score <= 1.0
    assert 0.0 <= chunk.confidence <= 1.0


# ── pipeline helpers ──────────────────────────────────────────────────────────

def test_build_llm_mock_with_chunks():
    chunks = [
        Chunk(
            chunk_id=1, document_id="doc-001", document_title="Правила РС",
            section_id=42, page=42, content="full text",
            excerpt="Толщина не менее 12 мм.", score=0.9,
            clause="4.2", section_title="Ледовые усиления", confidence=0.85,
        )
    ]
    result = _build_llm_mock("Arc4?", chunks)
    assert "12 мм" in result
    assert "[source:0]" in result
    assert "%[" not in result


def test_build_llm_mock_empty_chunks():
    result = _build_llm_mock("Arc4?", [])
    assert len(result) > 0


def test_build_llm_mock_uses_source_ref_format():
    chunks = [
        Chunk(
            chunk_id=1, document_id="doc-001", document_title="Правила РС",
            section_id=42, page=42, content="text",
            excerpt="фрагмент про толщину", score=0.9,
            clause="4.2", section_title="раздел", confidence=0.85,
        )
    ]
    result = _build_llm_mock("Arc4?", chunks)
    assert "[source:0]" in result
    assert "%[" not in result


def test_enrich_citations_replaces_source_refs():
    chunks = [
        Chunk(
            chunk_id=1, document_id=42, document_title="Правила РС",
            section_id=420042, page=42, content="text",
            excerpt="Толщина не менее 12 мм.", score=0.9,
            clause="4.2", section_title="Ледовые усиления", confidence=0.85,
        )
    ]
    text = "Не менее 12 мм [source:0]."
    enriched, used = _enrich_citations(text, chunks)
    assert "[source:" not in enriched
    assert "document_id:42" in enriched
    assert "section_id:420042" in enriched
    assert used == [0]


def test_enrich_citations_filters_unused():
    chunks = [
        Chunk(chunk_id=1, document_id=1, document_title="Д1", section_id=10, page=1,
              content="a", excerpt="a", score=1.0, clause=None, section_title=None, confidence=1.0),
        Chunk(chunk_id=2, document_id=2, document_title="Д2", section_id=20, page=2,
              content="b", excerpt="b", score=1.0, clause=None, section_title=None, confidence=1.0),
    ]
    text = "Текст [source:0] без второго источника."
    _, used = _enrich_citations(text, chunks)
    assert used == [0]
    assert 1 not in used


def test_enrich_citations_out_of_range_ignored():
    chunks = [
        Chunk(chunk_id=1, document_id=1, document_title="Д1", section_id=10, page=1,
              content="a", excerpt="a", score=1.0, clause=None, section_title=None, confidence=1.0),
    ]
    text = "Текст [source:99]."
    enriched, used = _enrich_citations(text, chunks)
    assert "[source:" not in enriched
    assert used == []


# ── pipeline integration (с мок-БД) ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_sets_answered_status(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "pipeline test"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "Arc4 толщина?"})
    mid = r.json()["message_id"]

    await asyncio.sleep(2.5)

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/{mid}")
    msg = r.json()["message"]
    assert msg["status"] in ("answered", "not_found", "failed")


@pytest.mark.asyncio
async def test_pipeline_answered_message_has_sources(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "sources test"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "Arc4?"})
    mid = r.json()["message_id"]

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/{mid}?longpoll=10")
    msg = r.json()["message"]
    if msg["status"] == "answered":
        assert len(msg["sources"]) > 0
        assert "%[" not in (msg["content"] or "")
        assert "[source:" not in (msg["content"] or "")
        src = msg["sources"][0]
        assert "document_id" in src
        assert "section_id" in src
        assert "excerpt" in src
        assert "score" in src
        assert src["index"] is not None


@pytest.mark.asyncio
async def test_pipeline_sources_have_new_fields(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "new fields"})
    sid = r.json()["session_id"]
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "Arc4?"})
    mid = r.json()["message_id"]

    r = await client.get(f"/api/v1/chat/sessions/{sid}/messages/{mid}?longpoll=10")
    msg = r.json()["message"]
    if msg["status"] == "answered" and msg["sources"]:
        src = msg["sources"][0]
        assert "clause" in src
        assert "section_title" in src
        assert "confidence" in src
        assert src["excerpt"] is not None
        assert len(src["excerpt"]) <= 512
