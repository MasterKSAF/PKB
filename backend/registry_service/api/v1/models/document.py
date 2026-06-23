import uuid

from sqlalchemy import Column, String, Text, BigInteger, Integer, Boolean, Date, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class Document(Base):
    __tablename__ = 'documents'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', BigInteger, primary_key=True, autoincrement=True)
    doc_code = Column('doc_code', Text, nullable=False)
    title = Column('title', Text, nullable=False)
    normalized_title = Column('normalized_title', Text)
    source_type = Column('source_type', String(50))
    group_ = Column('group', String(50))
    mks_oks_code = Column('mks_oks_code', Text)
    okstu_code = Column('okstu_code', Text)
    udk_code = Column('udk_code', Text)
    from datetime import date
    valid_from = Column('valid_from', Date, nullable=False, default=date(1970, 1, 1))
    valid_until = Column('valid_until', Date, nullable=False, default=date(2999, 12, 31))
    deleted_at = Column('deleted_at', DateTime(timezone=True))
    title_key = Column('title_key', Text, unique=True)
    draft_id = Column('draft_id', BigInteger)
    preview_snapshot = Column('preview_snapshot', JSONB)
    current_version_id = Column('current_version_id', BigInteger)
    era = Column('era', String(50))
    validity_status = Column('validity_status', String(50))
    status = Column('status', String(50))
    jurisdiction = Column('jurisdiction', String(50))
    issuing_body = Column('issuing_body', Text)
    adoption_date = Column('adoption_date', Date)
    effective_from = Column('effective_from', Date)
    replaces = Column('replaces', Text)
    status_note = Column('status_note', Text)
    file_hash_sha256 = Column('file_hash_sha256', Text)
    title_hash_sha256 = Column('title_hash_sha256', Text)
    file_size_bytes = Column('file_size_bytes', BigInteger)
    processing_status = Column('processing_status', String(50))
    chunk_count = Column('chunk_count', Integer)
    successor_doc_id = Column('successor_doc_id', BigInteger)
    predecessor_doc_id = Column('predecessor_doc_id', BigInteger)
    classifier_code = Column('classifier_code', Text, nullable=True)
    industry_code = Column('industry_code', Text, nullable=True)
    enterprise_id = Column('enterprise_id', BigInteger, nullable=True)
    created_by = Column('created_by', Text)
    updated_by = Column('updated_by', Text)
    classification_status = Column('classification_status', JSONB, default=dict, server_default='{}')
    doc_metadata = Column('metadata', JSONB, default=dict, server_default='{}')
    created_at = Column('created_at', DateTime)
    updated_at = Column('updated_at', DateTime)
