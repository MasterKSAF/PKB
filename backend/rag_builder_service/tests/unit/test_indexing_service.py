"""IndexingService unit tests — no DB required (mocked session + repo)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from rag_builder.models.contracts import BuildRequest, Section
from rag_builder.services.indexing_service import IndexingService

UTC_PLUS_3 = timezone(timedelta(hours=3))


@pytest.fixture
def service() -> IndexingService:
    return IndexingService()


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    # Proper async context manager for session.begin()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=session)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    return session


def make_req(
    document_id: int = 100,
    text: str = "hello world",
    section_id: int = 1,
    strategy: str = "semantic_1024",
) -> BuildRequest:
    return BuildRequest(
        document_id=document_id,
        sections=[
            Section(
                section_id=section_id,
                document_id=document_id,
                clause="1",
                title=None,
                level=1,
                path="1",
                page=1,
                type="text",
                content={"text": text},
            )
        ],
        options={"strategy": strategy},
    )


class TestBuild:
    async def test_build_returns_indexed_status(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch.object(service.chunking, "build_chunks") as mock_chunking, \
             patch.object(service.embedding, "embed_many") as mock_embed, \
             patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:

            mock_repo = AsyncMock()
            mock_repo.delete_by_document = AsyncMock(return_value=0)
            mock_repo.insert_chunks = AsyncMock(return_value=1)
            mock_repo_cls.return_value = mock_repo
            mock_chunking.return_value = [
                MagicMock(section_id=1, document_id=100, chunk_index=0,
                          content="hello", strategy="semantic_1024", page=1,
                          indexing_txn_id=None)
            ]
            mock_embed.return_value = [[0.1] * 2048]

            req = make_req()
            resp = await service.build(req, mock_session)

            assert resp.status == "indexed"
            assert resp.document_id == 100
            assert resp.chunks_count == 1
            assert resp.index_stats["sections"] == 1
            assert resp.index_stats["chunks"] == 1
            assert resp.index_stats["embeddings"] == 1
            # errors/warnings default to empty
            assert resp.errors == []
            assert resp.warnings == []

    async def test_build_generates_uuid4_txn_id(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch.object(service.chunking, "build_chunks") as mock_chunking, \
             patch.object(service.embedding, "embed_many") as mock_embed, \
             patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:

            mock_repo = AsyncMock()
            mock_repo.delete_by_document = AsyncMock(return_value=0)
            mock_repo.insert_chunks = AsyncMock(return_value=1)
            mock_repo_cls.return_value = mock_repo
            mock_chunking.return_value = [
                MagicMock(section_id=1, document_id=100, chunk_index=0,
                          content="hello", strategy="semantic_1024", page=1,
                          indexing_txn_id="some-uuid")
            ]
            mock_embed.return_value = [[0.1] * 2048]

            req = make_req()
            await service.build(req, mock_session)

            # build_chunks was called with a txn_id
            call_kwargs = mock_chunking.call_args
            txn_id_arg = call_kwargs[0][4]  # 5th positional arg (indexing_txn_id)
            assert txn_id_arg is not None
            assert isinstance(txn_id_arg, type(uuid4()))

    async def test_build_with_strategy_from_request(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch.object(service.chunking, "build_chunks") as mock_chunking, \
             patch.object(service.embedding, "embed_many", return_value=[[0.1] * 2048]), \
             patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:

            mock_repo = AsyncMock()
            mock_repo.delete_by_document = AsyncMock(return_value=0)
            mock_repo.insert_chunks = AsyncMock(return_value=1)
            mock_repo_cls.return_value = mock_repo
            mock_chunking.return_value = [
                MagicMock(section_id=1, document_id=100, chunk_index=0,
                          content="hello", strategy="custom", page=1,
                          indexing_txn_id=None)
            ]

            req = make_req(strategy="custom")
            await service.build(req, mock_session)

            call_args = mock_chunking.call_args[0]
            assert call_args[3] == "custom"  # strategy arg

    async def test_build_empty_sections_ok(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch.object(service.chunking, "build_chunks") as mock_chunking, \
             patch.object(service.embedding, "embed_many", return_value=[]), \
             patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:

            mock_repo = AsyncMock()
            mock_repo.delete_by_document = AsyncMock(return_value=0)
            mock_repo.insert_chunks = AsyncMock(return_value=0)
            mock_repo_cls.return_value = mock_repo
            mock_chunking.return_value = []

            req = BuildRequest(document_id=100, sections=[], options={})
            resp = await service.build(req, mock_session)

            assert resp.status == "indexed"
            assert resp.chunks_count == 0

    async def test_build_sets_status_indexing_then_indexed(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch.object(service.chunking, "build_chunks") as mock_chunking, \
             patch.object(service.embedding, "embed_many", return_value=[]), \
             patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:

            mock_repo = AsyncMock()
            mock_repo.delete_by_document = AsyncMock(return_value=0)
            mock_repo.insert_chunks = AsyncMock(return_value=0)
            mock_repo_cls.return_value = mock_repo
            mock_chunking.return_value = []

            req = make_req()
            await service.build(req, mock_session)

            status = service._status.get("100")
            assert status is not None
            assert status.status == "indexed"

    async def test_build_sets_failed_on_exception(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch.object(service.chunking, "build_chunks", side_effect=ValueError("chunking failed")):
            req = make_req()
            with pytest.raises(ValueError, match="chunking failed"):
                await service.build(req, mock_session)

            status = service._status.get("100")
            assert status is not None
            assert status.status == "failed"

    async def test_build_raises_if_document_id_none(self) -> None:
        # Pydantic validation catches this before service.build() is called
        with pytest.raises(ValidationError, match="document_id is required"):
            BuildRequest(document_id=None, sections=[])


class TestDelete:
    async def test_delete_returns_status_completed(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.delete_by_document = AsyncMock(return_value=5)
            mock_repo_cls.return_value = mock_repo

            resp = await service.delete(100, mock_session)

            assert resp.status == "completed"
            assert resp.document_id == 100
            assert resp.deleted_count == 5

    async def test_delete_resets_status_to_pending(self, service: IndexingService, mock_session: AsyncMock) -> None:
        # First set status to indexed
        service._status["100"] = MagicMock(status="indexed")

        with patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.delete_by_document = AsyncMock(return_value=3)
            mock_repo_cls.return_value = mock_repo

            await service.delete(100, mock_session)

            status = service._status.get("100")
            assert status is not None
            assert status.status == "pending"

    async def test_delete_zero_chunks_ok(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.delete_by_document = AsyncMock(return_value=0)
            mock_repo_cls.return_value = mock_repo

            resp = await service.delete(999, mock_session)
            assert resp.deleted_count == 0


class TestStatus:
    async def test_status_returns_pending_for_unknown_doc(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.count_by_document = AsyncMock(return_value=0)
            mock_repo.has_embeddings = AsyncMock(return_value=False)
            mock_repo_cls.return_value = mock_repo

            resp = await service.status(100, mock_session, longpoll=0)

            assert resp.status == "pending"
            assert resp.chunks_count == 0
            assert resp.has_embeddings is False

    async def test_status_returns_indexed_for_doc_with_chunks(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.count_by_document = AsyncMock(return_value=5)
            mock_repo.has_embeddings = AsyncMock(return_value=True)
            mock_repo_cls.return_value = mock_repo

            resp = await service.status(100, mock_session, longpoll=0)

            assert resp.status == "indexed"
            assert resp.chunks_count == 5
            assert resp.has_embeddings is True

    async def test_status_longpoll_timeout_returns_current(self, service: IndexingService, mock_session: AsyncMock) -> None:
        with patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.count_by_document = AsyncMock(return_value=0)
            mock_repo.has_embeddings = AsyncMock(return_value=False)
            mock_repo_cls.return_value = mock_repo

            # Status is pending, longpoll > 0 will wait and timeout
            resp = await service.status(100, mock_session, longpoll=1)

            assert resp.status == "pending"

    async def test_status_returns_cached_value_without_db(self, service: IndexingService, mock_session: AsyncMock) -> None:
        service._status["100"] = MagicMock(status="indexed", chunks_count=10, has_embeddings=True, indexed_at=datetime.now(UTC_PLUS_3))

        with patch("rag_builder.services.indexing_service.ChunkRepository") as mock_repo_cls:
            resp = await service.status(100, mock_session, longpoll=0)

            assert resp.status == "indexed"
            assert resp.chunks_count == 10
            mock_repo_cls.assert_not_called()
