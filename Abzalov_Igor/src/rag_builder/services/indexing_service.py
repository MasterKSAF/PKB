from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from rag_builder.chunking.service import ChunkingService
from rag_builder.core.config import settings
from rag_builder.embeddings.service import EmbeddingService
from rag_builder.models.contracts import BuildRequest, BuildResponse, DeleteResponse, StatusResponse
from rag_builder.repositories.chunk_repository import ChunkRepository

StatusType = Literal["pending", "indexing", "indexed", "failed"]


@dataclass
class DocStatus:
    status: StatusType
    chunks_count: int = 0
    has_embeddings: bool = False
    indexed_at: datetime | None = None


class IndexingService:
    def __init__(self) -> None:
        self.chunking = ChunkingService()
        self.embedding = EmbeddingService()
        self._status: dict[str, DocStatus] = {}
        self._events: dict[str, asyncio.Event] = {}

    async def build(self, req: BuildRequest, session: AsyncSession) -> BuildResponse:
        doc_id = str(req.document_id)
        logger.info("Indexing start document_id={}", doc_id)
        self._set_status(doc_id, DocStatus(status="indexing"))
        try:
            repo = ChunkRepository(session)
            strategy = str(req.options.get("strategy", settings.chunk_default_strategy))
            chunks = self.chunking.build_chunks(doc_id, req.sections, req.protected_spans, strategy)
            vectors = await self.embedding.embed_many([c.content for c in chunks])
            vectors_for_repo: list[list[float] | None] = [v for v in vectors]
            async with session.begin():
                await repo.delete_by_document(doc_id)
                created = await repo.insert_chunks(chunks, vectors_for_repo)
            now = datetime.now(UTC)
            self._set_status(doc_id, DocStatus(status="indexed", chunks_count=created, has_embeddings=created > 0, indexed_at=now))
            logger.info("Indexing completed document_id={} chunks={}", doc_id, created)
            return BuildResponse(
                document_id=req.document_id,
                status="completed",
                indexed_at=now,
                chunks_count=created,
                index_stats={"sections": len(req.sections), "chunks": created, "embeddings": created},
            )
        except Exception:
            self._set_status(doc_id, DocStatus(status="failed"))
            logger.exception("Indexing failed document_id={}", doc_id)
            raise

    async def delete(self, document_id: UUID, session: AsyncSession) -> DeleteResponse:
        logger.info("Delete index start document_id={}", document_id)
        try:
            repo = ChunkRepository(session)
            async with session.begin():
                deleted = await repo.delete_by_document(str(document_id))
            self._set_status(str(document_id), DocStatus(status="pending", chunks_count=0, has_embeddings=False))
            logger.info("Delete index completed document_id={} deleted_count={}", document_id, deleted)
            return DeleteResponse(document_id=document_id, deleted_count=deleted, status="completed")
        except Exception:
            logger.exception("Delete index failed document_id={}", document_id)
            raise

    async def status(self, document_id: UUID, session: AsyncSession, longpoll: int) -> StatusResponse:
        doc_id = str(document_id)
        logger.debug("Status check start document_id={} longpoll={}", doc_id, longpoll)
        try:
            if doc_id not in self._status:
                repo = ChunkRepository(session)
                count = await repo.count_by_document(doc_id)
                has_emb = await repo.has_embeddings(doc_id)
                self._status[doc_id] = DocStatus(status="indexed" if count > 0 else "pending", chunks_count=count, has_embeddings=has_emb)
            if self._status[doc_id].status in {"pending", "indexing"} and longpoll > 0:
                event = self._events.setdefault(doc_id, asyncio.Event())
                try:
                    await asyncio.wait_for(event.wait(), timeout=longpoll)
                except TimeoutError:
                    logger.debug("Longpoll timeout document_id={} timeout={}s", doc_id, longpoll)
            cur = self._status[doc_id]
            logger.debug("Status check done document_id={} status={}", doc_id, cur.status)
            return StatusResponse(document_id=document_id, status=cur.status, chunks_count=cur.chunks_count, has_embeddings=cur.has_embeddings, indexed_at=cur.indexed_at)
        except Exception:
            logger.exception("Status check failed document_id={}", doc_id)
            raise

    def _set_status(self, doc_id: str, status: DocStatus) -> None:
        self._status[doc_id] = status
        event = self._events.setdefault(doc_id, asyncio.Event())
        event.set()
        self._events[doc_id] = asyncio.Event()


indexing_service = IndexingService()
