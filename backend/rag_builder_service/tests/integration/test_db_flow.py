import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from rag_builder.models.contracts import BuildRequest, Section
from rag_builder.services.indexing_service import IndexingService


@pytest.mark.asyncio
async def test_build_persists_chunks(session: AsyncSession) -> None:
    doc_id = 100
    req = BuildRequest(
        document_id=doc_id,
        sections=[
            Section(
                section_id=10,
                document_id=doc_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": "hello world"},
            )
        ],
        options={"strategy": "semantic_1024"},
    )
    svc = IndexingService()
    resp = await svc.build(req, session)
    assert resp.status == "indexed"
    assert resp.chunks_count == 1


@pytest.mark.asyncio
async def test_delete_removes_chunks(session: AsyncSession) -> None:
    doc_id = 101
    req = BuildRequest(
        document_id=doc_id,
        sections=[
            Section(
                section_id=11,
                document_id=doc_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": "bye"},
            )
        ],
        options={"strategy": "semantic_1024"},
    )
    svc = IndexingService()
    await svc.build(req, session)
    deleted = await svc.delete(doc_id, session)
    assert deleted.status == "completed"
    assert deleted.deleted_count >= 1
