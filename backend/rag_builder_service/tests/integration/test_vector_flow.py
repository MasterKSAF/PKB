"""Vector integration tests — require PostgreSQL + pgvector on localhost:5433.

Run with:
  docker compose up -d postgres
  python -m pytest tests/integration/test_vector_flow.py -v
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag_builder.models.contracts import BuildRequest, Section
from rag_builder.services.indexing_service import IndexingService


pytestmark = pytest.mark.db


@pytest.mark.asyncio
async def test_vector_dimension_2048(session: AsyncSession) -> None:
    """Verify stored vectors have the correct dimension (2048)."""
    doc_id = 5000
    req = BuildRequest(
        document_id=doc_id,
        sections=[
            Section(
                section_id=5010,
                document_id=doc_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": "vector dimension test text " * 10},
            )
        ],
        options={"strategy": "semantic_1024"},
    )
    svc = IndexingService()
    resp = await svc.build(req, session)
    assert resp.status == "indexed"
    assert resp.chunks_count >= 1

    # Read vector dimension directly from DB
    result = await session.execute(
        text("SELECT vector_dims(embedding) FROM rag.document_chunks WHERE document_id = :did LIMIT 1"),
        {"did": doc_id},
    )
    dim = result.scalar()
    assert dim == 2048, f"Expected vector dim=2048, got {dim}"


@pytest.mark.asyncio
async def test_vector_embedding_roundtrip(session: AsyncSession) -> None:
    """Embed → store → read back → verify non-null vector."""
    doc_id = 5001
    req = BuildRequest(
        document_id=doc_id,
        sections=[
            Section(
                section_id=5011,
                document_id=doc_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": "round trip test content for embeddings"},
            )
        ],
        options={"strategy": "semantic_1024"},
    )
    svc = IndexingService()
    resp = await svc.build(req, session)
    assert resp.status == "indexed"
    assert resp.chunks_count == 1

    # Read back
    result = await session.execute(
        text("""
            SELECT embedding IS NOT NULL, vector_dims(embedding)
            FROM rag.document_chunks
            WHERE document_id = :did
        """),
        {"did": doc_id},
    )
    row = result.one()
    assert row[0] is True, "embedding must not be NULL"
    assert row[1] == 2048


@pytest.mark.asyncio
async def test_vector_cosine_similarity_search(session: AsyncSession) -> None:
    """Basic cosine similarity search via pgvector works."""
    doc_id = 5002
    text_content = "word " * 100

    # Build index with known content
    req = BuildRequest(
        document_id=doc_id,
        sections=[
            Section(
                section_id=5021,
                document_id=doc_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": text_content},
            )
        ],
        options={"strategy": "semantic_1024"},
    )
    svc = IndexingService()
    resp = await svc.build(req, session)
    assert resp.status == "indexed"
    assert resp.chunks_count >= 1

    # Try cosine similarity search via pgvector operator
    result = await session.execute(
        text("""
            SELECT id, chunk_index, content
            FROM rag.document_chunks
            WHERE document_id = :did
            ORDER BY embedding <=> (SELECT embedding FROM rag.document_chunks WHERE document_id = :did LIMIT 1)
            LIMIT 1
        """),
        {"did": doc_id},
    )
    row = result.one()
    assert row[0] is not None
    assert row[1] == 0  # closest to itself


@pytest.mark.asyncio
async def test_indexing_txn_id_stored(session: AsyncSession) -> None:
    """Verify indexing_txn_id is stored correctly."""
    doc_id = 5003
    req = BuildRequest(
        document_id=doc_id,
        sections=[
            Section(
                section_id=5031,
                document_id=doc_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": "txn id test"},
            )
        ],
        options={"strategy": "semantic_1024"},
    )
    svc = IndexingService()
    resp = await svc.build(req, session)
    assert resp.status == "indexed"

    result = await session.execute(
        text("SELECT indexing_txn_id IS NOT NULL FROM rag.document_chunks WHERE document_id = :did"),
        {"did": doc_id},
    )
    assert result.scalar() is True, "indexing_txn_id must not be NULL"


@pytest.mark.asyncio
async def test_multiple_chunks_same_section_have_unique_chunk_indices(session: AsyncSession) -> None:
    """When a section produces multiple chunks, each has unique chunk_index."""
    doc_id = 5004
    long_text = "data " * 3000  # will create 3 chunks
    req = BuildRequest(
        document_id=doc_id,
        sections=[
            Section(
                section_id=5041,
                document_id=doc_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": long_text},
            )
        ],
        options={"strategy": "semantic_1024"},
    )
    svc = IndexingService()
    resp = await svc.build(req, session)
    assert resp.status == "indexed"
    assert resp.chunks_count == 3

    # Verify chunk indices are 0, 1, 2
    result = await session.execute(
        text("""
            SELECT chunk_index FROM rag.document_chunks
            WHERE document_id = :did
            ORDER BY chunk_index
        """),
        {"did": doc_id},
    )
    indices = result.scalars().all()
    assert indices == [0, 1, 2]


@pytest.mark.asyncio
async def test_delete_cleans_all_chunks(session: AsyncSession) -> None:
    """After delete, no chunks remain for the document."""
    doc_id = 5005
    req = BuildRequest(
        document_id=doc_id,
        sections=[
            Section(
                section_id=5051,
                document_id=doc_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": "delete test"},
            )
        ],
        options={"strategy": "semantic_1024"},
    )
    svc = IndexingService()
    await svc.build(req, session)
    await svc.delete(doc_id, session)

    result = await session.execute(
        text("SELECT COUNT(*) FROM rag.document_chunks WHERE document_id = :did"),
        {"did": doc_id},
    )
    assert result.scalar() == 0
