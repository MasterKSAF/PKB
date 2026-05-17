from typing import Optional
import datetime
import enum
import uuid

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKeyConstraint, Index, PrimaryKeyConstraint, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class DocStatus(str, enum.Enum):
    DRAFT = 'draft'
    UPLOADED = 'uploaded'
    VALIDATING = 'validating'
    PROCESSING = 'processing'
    REVIEW_REQUIRED = 'review_required'
    READY_FOR_PROMOTION = 'ready_for_promotion'
    APPROVED = 'approved'
    FAILED = 'failed'
    ARCHIVED = 'archived'


class ValidationStatus(str, enum.Enum):
    PENDING = 'pending'
    VALID = 'valid'
    INVALID = 'invalid'


class FormatRegistryPurgatory(Base):
    __tablename__ = 'format_registry'
    __table_args__ = (
        PrimaryKeyConstraint('code', name='format_registry_pkey'),
        {'comment': 'File format registry mapping MIME types to parser plugins',
         'schema': 'purgatory'}
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    parser_plugin: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    document_versions_purgatory: Mapped[list['DocumentVersionsPurgatory']] = relationship('DocumentVersionsPurgatory', back_populates='format_registry_purgatory')


class DocumentsPurgatory(Base):
    __tablename__ = 'documents'
    __table_args__ = (
        ForeignKeyConstraint(['classifier_code'], ['purgatory.classifier_registry.code'], name='documents_classifier_code_fkey'),
        PrimaryKeyConstraint('id', name='documents_pkey'),
        UniqueConstraint('title_hash_sha256', name='documents_title_hash_sha256_key'),
        Index('idx_docs_classifier', 'classifier_code'),
        Index('idx_docs_status', 'status'),
        Index('idx_docs_title_hash', 'title_hash_sha256'),
        {'comment': 'Logical document registry. Uniqueness guaranteed by title_hash_sha256',
         'schema': 'purgatory'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    classifier_code: Mapped[Optional[str]] = mapped_column(Text)
    doc_code: Mapped[Optional[str]] = mapped_column(Text)
    title_hash_sha256: Mapped[Optional[str]] = mapped_column(Text, comment='SHA-256 of (classifier_code + doc_code + normalized_title). Deduplication key.')
    status: Mapped[Optional[DocStatus]] = mapped_column(Enum(DocStatus, values_callable=lambda cls: [member.value for member in cls], name='doc_status', schema='purgatory'), server_default=text("'draft'::purgatory.doc_status"))
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    chunk_container_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    created_by: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    updated_by: Mapped[Optional[str]] = mapped_column(Text)

    classifier_registry_purgatory: Mapped[Optional['ClassifierRegistryPurgatory']] = relationship('ClassifierRegistryPurgatory', back_populates='documents_purgatory')
    chunk_containers_purgatory: Mapped['ChunkContainersPurgatory'] = relationship('ChunkContainersPurgatory', uselist=False, back_populates='document_purgatory')
    document_versions_purgatory: Mapped[list['DocumentVersionsPurgatory']] = relationship('DocumentVersionsPurgatory', back_populates='document_purgatory')
    status_history_purgatory: Mapped[list['StatusHistoryPurgatory']] = relationship('StatusHistoryPurgatory', back_populates='document_purgatory')


class ChunkContainersPurgatory(Base):
    __tablename__ = 'chunk_containers'
    __table_args__ = (
        ForeignKeyConstraint(['document_id'], ['purgatory.documents.id'], ondelete='CASCADE', name='chunk_containers_document_id_fkey'),
        PrimaryKeyConstraint('id', name='chunk_containers_pkey'),
        UniqueConstraint('document_id', name='chunk_containers_document_id_key'),
        Index('idx_containers_doc', 'document_id'),
        Index('idx_containers_validation', 'validation_status'),
        {'comment': 'Validated JSON manifests ready for Promotion Service ingestion',
         'schema': 'purgatory'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    version_hash: Mapped[str] = mapped_column(Text, nullable=False)
    json_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    validation_status: Mapped[Optional[ValidationStatus]] = mapped_column(Enum(ValidationStatus, values_callable=lambda cls: [member.value for member in cls], name='validation_status', schema='purgatory'), server_default=text("'pending'::purgatory.validation_status"))
    validation_errors: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    document_purgatory: Mapped['DocumentsPurgatory'] = relationship('DocumentsPurgatory', back_populates='chunk_containers_purgatory')


class DocumentVersionsPurgatory(Base):
    __tablename__ = 'document_versions'
    __table_args__ = (
        ForeignKeyConstraint(['document_id'], ['purgatory.documents.id'], ondelete='CASCADE', name='document_versions_document_id_fkey'),
        ForeignKeyConstraint(['format_code'], ['purgatory.format_registry.code'], name='document_versions_format_code_fkey'),
        PrimaryKeyConstraint('id', name='document_versions_pkey'),
        UniqueConstraint('content_hash_sha256', name='document_versions_content_hash_sha256_key'),
        Index('idx_versions_doc', 'document_id'),
        Index('idx_versions_hash', 'content_hash_sha256'),
        {'comment': 'Physical file representations using Content-Addressable Storage (CAS)',
         'schema': 'purgatory'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    source_filename: Mapped[str] = mapped_column(Text, nullable=False)
    format_code: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False, comment='S3 object key in CAS format: {doc_id}/v{n}/{content_hash}.{ext}')
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    content_hash_sha256: Mapped[Optional[str]] = mapped_column(Text, comment='SHA-256 of file content. CAS deduplication key.')
    uploaded_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    uploaded_by: Mapped[Optional[str]] = mapped_column(Text)

    document_purgatory: Mapped['DocumentsPurgatory'] = relationship('DocumentsPurgatory', back_populates='document_versions_purgatory')
    format_registry_purgatory: Mapped['FormatRegistryPurgatory'] = relationship('FormatRegistryPurgatory', back_populates='document_versions_purgatory')


class StatusHistoryPurgatory(Base):
    __tablename__ = 'status_history'
    __table_args__ = (
        ForeignKeyConstraint(['document_id'], ['purgatory.documents.id'], ondelete='CASCADE', name='status_history_document_id_fkey'),
        PrimaryKeyConstraint('id', name='status_history_pkey'),
        Index('idx_history_doc', 'document_id'),
        {'comment': 'Immutable audit trail of all document status transitions',
         'schema': 'purgatory'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    new_status: Mapped[DocStatus] = mapped_column(Enum(DocStatus, values_callable=lambda cls: [member.value for member in cls], name='doc_status', schema='purgatory'), nullable=False)
    old_status: Mapped[Optional[DocStatus]] = mapped_column(Enum(DocStatus, values_callable=lambda cls: [member.value for member in cls], name='doc_status', schema='purgatory'))
    comment: Mapped[Optional[dict]] = mapped_column(JSONB)
    changed_by: Mapped[Optional[str]] = mapped_column(Text)
    changed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    document_purgatory: Mapped['DocumentsPurgatory'] = relationship('DocumentsPurgatory', back_populates='status_history_purgatory')
