from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from rag_builder.models.db import RagDocumentChunk
from rag_builder.models.domain import Chunk


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_chunks(self, chunks: list[Chunk], embeddings: list[list[float] | None]) -> int:
        logger.debug("Repository.insert_chunks start chunks={} embeddings={}", len(chunks), len(embeddings))
        rows = [
            RagDocumentChunk(
                section_id=c.section_id,
                document_id=c.document_id,
                chunk_index=c.chunk_index,
                content=c.content,
                embedding=e,
                strategy=c.strategy,
                page=c.page,
            )
            for c, e in zip(chunks, embeddings, strict=True)
        ]
        self.session.add_all(rows)
        await self.session.flush()
        logger.info("Repository.insert_chunks done inserted={}", len(rows))
        return len(rows)

    async def delete_by_document(self, document_id: str) -> int:
        logger.debug("Repository.delete_by_document start document_id={}", document_id)
        stmt = delete(RagDocumentChunk).where(RagDocumentChunk.document_id == document_id)
        result = await self.session.execute(stmt)
        deleted = int(getattr(result, "rowcount", 0) or 0)
        logger.info("Repository.delete_by_document done document_id={} deleted={}", document_id, deleted)
        return deleted

    async def count_by_document(self, document_id: str) -> int:
        logger.debug("Repository.count_by_document document_id={}", document_id)
        stmt = select(RagDocumentChunk.id).where(RagDocumentChunk.document_id == document_id)
        result = await self.session.execute(stmt)
        count = len(result.scalars().all())
        logger.debug("Repository.count_by_document result document_id={} count={}", document_id, count)
        return count

    async def has_embeddings(self, document_id: str) -> bool:
        logger.debug("Repository.has_embeddings document_id={}", document_id)
        stmt = select(RagDocumentChunk.id).where(
            RagDocumentChunk.document_id == document_id, RagDocumentChunk.embedding.is_not(None)
        )
        result = await self.session.execute(stmt)
        has_value = result.first() is not None
        logger.debug("Repository.has_embeddings result document_id={} has_embeddings={}", document_id, has_value)
        return has_value
