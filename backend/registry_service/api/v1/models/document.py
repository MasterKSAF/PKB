import uuid

from sqlalchemy import Column, String, Text, BigInteger, Integer, Boolean, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class Document(Base):
    __tablename__ = 'documents'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_code = Column('doc_code', Text, nullable=False)
    title = Column('title', Text, nullable=False)
    normalized_title = Column('normalized_title', Text)
    source_type = Column('source_type', String(50))
    group_ = Column('group', String(50))
    mks_oks_code = Column('mks_oks_code', Text)
    okstu_code = Column('okstu_code', Text)
    udc = Column('udc', Text)
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
    successor_doc_id = Column('successor_doc_id', UUID(as_uuid=True))
    predecessor_doc_id = Column('predecessor_doc_id', UUID(as_uuid=True))
    created_by = Column('created_by', Text)
    updated_by = Column('updated_by', Text)
    created_at = Column('created_at', DateTime)
    updated_at = Column('updated_at', DateTime)
