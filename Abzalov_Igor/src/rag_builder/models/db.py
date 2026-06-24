from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import BigInteger, DateTime, Float, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from rag_builder.core.config import settings


class Base(DeclarativeBase):
    pass


class RagDocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = ({"schema": "rag"},)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    section_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.vector_dimension), nullable=True)
    tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    strategy: Mapped[str] = mapped_column(String(32), nullable=False)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


Index("ix_rag_doc_chunks_doc_id", RagDocumentChunk.document_id)
