"""
Unit tests for DocumentRepository.

Tests cover:
- Create document
- Get document by ID
- FSM transitions with FOR UPDATE
- Error state setting
- Hash uniqueness checks
- List by status
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document import DocumentRepository
from app.models.document import Document


@pytest.mark.asyncio
class TestDocumentRepository:
    """Tests for DocumentRepository CRUD and FSM operations."""

    async def test_create_document(self, db_session: AsyncSession):
        """Creating a document returns it with 'uploaded' status."""
        repo = DocumentRepository(db_session)
        doc = await repo.create(
            file_hash_sha256="abc123",
            original_filename="test.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
            source_type="GOST",
            title="Test Document",
        )
        assert doc.id is not None
        assert len(doc.id) == 36  # UUID
        assert doc.status == "uploaded"
        assert doc.file_hash_sha256 == "abc123"
        assert doc.original_filename == "test.pdf"

    async def test_get_document(self, db_session: AsyncSession):
        """Getting an existing document returns it."""
        repo = DocumentRepository(db_session)
        created = await repo.create(
            file_hash_sha256="def456",
            original_filename="doc.pdf",
            file_size_bytes=2048,
            mime_type="application/pdf",
        )
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.status == "uploaded"

    async def test_get_non_existent(self, db_session: AsyncSession):
        """Getting a non-existent document returns None."""
        repo = DocumentRepository(db_session)
        result = await repo.get("non-existent-id")
        assert result is None

    async def test_fsm_transition_valid(self, db_session: AsyncSession):
        """Valid FSM transition updates the status."""
        repo = DocumentRepository(db_session)
        doc = await repo.create(
            file_hash_sha256="fsm001",
            original_filename="fsm_test.pdf",
            file_size_bytes=512,
            mime_type="application/pdf",
        )
        updated = await repo.fsm_transition(doc.id, "previewing")
        assert updated is not None
        assert updated.status == "previewing"

    async def test_fsm_transition_on_nonexistent(self, db_session: AsyncSession):
        """FSM transition on non-existent returns None."""
        repo = DocumentRepository(db_session)
        result = await repo.fsm_transition("no-such-id", "previewing")
        assert result is None

    async def test_set_error(self, db_session: AsyncSession):
        """Setting error changes status to failed and records error info."""
        repo = DocumentRepository(db_session)
        doc = await repo.create(
            file_hash_sha256="err001",
            original_filename="err.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
        )
        errored = await repo.set_error(
            doc.id,
            error_code="OCR_FAILED",
            error_message="OCR service returned 503",
        )
        assert errored is not None
        assert errored.status == "failed"
        assert errored.error_code == "OCR_FAILED"
        assert "503" in errored.error_message

    async def test_set_error_increments_retry(self, db_session: AsyncSession):
        """set_error increments retry_count."""
        repo = DocumentRepository(db_session)
        doc = await repo.create(
            file_hash_sha256="retry001",
            original_filename="retry.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
        )
        assert doc.retry_count == 0
        errored = await repo.set_error(doc.id, "ERR", "msg")
        assert errored.retry_count == 1

    async def test_exists_by_hash_true(self, db_session: AsyncSession):
        """exists_by_hash returns True for existing hash."""
        repo = DocumentRepository(db_session)
        await repo.create(
            file_hash_sha256="hash001",
            original_filename="h.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
        )
        assert await repo.exists_by_hash("hash001") is True

    async def test_exists_by_hash_false(self, db_session: AsyncSession):
        """exists_by_hash returns False for non-existing hash."""
        repo = DocumentRepository(db_session)
        assert await repo.exists_by_hash("nonexistent-hash") is False

    async def test_update_status(self, db_session: AsyncSession):
        """update_status directly sets status."""
        repo = DocumentRepository(db_session)
        doc = await repo.create(
            file_hash_sha256="upd001",
            original_filename="update.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
        )
        updated = await repo.update_status(doc.id, "failed")
        assert updated is not None
        assert updated.status == "failed"

    async def test_list_by_status(self, db_session: AsyncSession):
        """list_by_status returns documents with given status."""
        repo = DocumentRepository(db_session)
        # Create 2 uploaded + 1 failed
        for i in range(2):
            await repo.create(
                file_hash_sha256=f"list_status_{i}",
                original_filename=f"doc_{i}.pdf",
                file_size_bytes=100,
                mime_type="application/pdf",
            )
        failed_doc = await repo.create(
            file_hash_sha256="list_status_fail",
            original_filename="failed.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
        )
        await repo.update_status(failed_doc.id, "failed")

        uploaded_docs = await repo.list_by_status("uploaded")
        assert len(uploaded_docs) == 2

        failed_docs = await repo.list_by_status("failed")
        assert len(failed_docs) == 1

    async def test_create_with_all_fields(self, db_session: AsyncSession):
        """Creating with all metadata fields stores them."""
        repo = DocumentRepository(db_session)
        doc = await repo.create(
            file_hash_sha256="allfields",
            original_filename="full.pdf",
            file_size_bytes=999,
            mime_type="image/tiff",
            source_type="ISO",
            title="ISO 12345",
            doc_code="ISO 12345:2024",
            era="CURRENT",
            jurisdiction="INTL",
            issuing_body="ISO",
            title_hash_sha256="title-hash-abc",
        )
        assert doc.source_type == "ISO"
        assert doc.title == "ISO 12345"
        assert doc.doc_code == "ISO 12345:2024"
        assert doc.era == "CURRENT"
        assert doc.jurisdiction == "INTL"
        assert doc.issuing_body == "ISO"
        assert doc.title_hash_sha256 == "title-hash-abc"

    async def test_increment_retry(self, db_session: AsyncSession):
        """increment_retry increases retry_count by 1."""
        repo = DocumentRepository(db_session)
        doc = await repo.create(
            file_hash_sha256="incretry",
            original_filename="ir.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
        )
        for _ in range(3):
            await repo.increment_retry(doc.id)
        fetched = await repo.get(doc.id)
        assert fetched.retry_count == 3

    async def test_fsm_transaction_isolation(self, db_session: AsyncSession):
        """FSM transition acquires a lock (test does not deadlock)."""
        repo = DocumentRepository(db_session)
        doc = await repo.create(
            file_hash_sha256="locktest",
            original_filename="lock.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
        )
        # Transition twice in sequence — should not deadlock
        await repo.fsm_transition(doc.id, "previewing")
        await repo.fsm_transition(doc.id, "awaiting_decision")
        fetched = await repo.get(doc.id)
        assert fetched.status == "awaiting_decision"
