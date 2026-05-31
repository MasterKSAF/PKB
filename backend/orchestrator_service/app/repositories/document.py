"""
Document repository — CRUD operations and FSM-statem transitions.

Uses SELECT FOR UPDATE for atomic FSM transitions to prevent
race conditions between concurrent pipeline workers.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.document import Document


class DocumentRepository:
    """Repository for Document entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        file_hash_sha256: str,
        original_filename: str,
        file_size_bytes: int,
        mime_type: str,
        source_type: Optional[str] = None,
        title: Optional[str] = None,
        doc_code: Optional[str] = None,
        era: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        issuing_body: Optional[str] = None,
        title_hash_sha256: Optional[str] = None,
    ) -> Document:
        """Create a new document record."""
        doc = Document(
            id=str(uuid.uuid4()),
            file_hash_sha256=file_hash_sha256,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            source_type=source_type,
            title=title,
            doc_code=doc_code,
            era=era,
            jurisdiction=jurisdiction,
            issuing_body=issuing_body,
            title_hash_sha256=title_hash_sha256,
            status="uploaded",
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def get(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_for_update(self, document_id: str) -> Optional[Document]:
        """Get document with FOR UPDATE lock for atomic FSM transitions."""
        result = await self.db.execute(
            select(Document)
            .where(Document.id == document_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, document_id: str, new_status: str
    ) -> Optional[Document]:
        """Update document FSM status with optimistic locking."""
        doc = await self.get_for_update(document_id)
        if doc is None:
            return None
        doc.status = new_status
        doc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return doc

    async def fsm_transition(
        self, document_id: str, new_status: str
    ) -> Optional[Document]:
        """Atomically transition FSM status.

        Uses SELECT FOR UPDATE to prevent concurrent modifications.
        Returns None if document not found.
        Raises ValueError if transition is invalid (caller should validate via FSM).
        """
        doc = await self.get_for_update(document_id)
        if doc is None:
            return None
        old_status = doc.status
        doc.status = new_status
        doc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return doc

    async def set_error(
        self,
        document_id: str,
        error_code: str,
        error_message: str,
    ) -> Optional[Document]:
        """Set error state on document."""
        doc = await self.get_for_update(document_id)
        if doc is None:
            return None
        doc.status = "failed"
        doc.error_code = error_code
        doc.error_message = error_message
        doc.retry_count = doc.retry_count + 1
        doc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return doc

    async def increment_retry(self, document_id: str) -> Optional[Document]:
        """Increment retry counter."""
        doc = await self.get_for_update(document_id)
        if doc is None:
            return None
        doc.retry_count = doc.retry_count + 1
        doc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return doc

    async def exists_by_hash(self, file_hash_sha256: str) -> bool:
        """Check if a document with the given hash already exists."""
        result = await self.db.execute(
            select(Document.id).where(Document.file_hash_sha256 == file_hash_sha256)
        )
        return result.first() is not None

    async def list_by_status(
        self, status: str, limit: int = 50, offset: int = 0
    ) -> list[Document]:
        """List documents with a specific FSM status."""
        result = await self.db.execute(
            select(Document)
            .where(Document.status == status)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
