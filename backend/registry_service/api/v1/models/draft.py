from sqlalchemy import Column, String, Text, BigInteger, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base

class Draft(Base):
    __tablename__ = 'drafts'
    __table_args__ = {'schema': 'registry'}

    draft_id = Column('draft_id', BigInteger, primary_key=True, autoincrement=True)
    registry_document_id = Column('registry_document_id', BigInteger)
    status = Column('status', String(50), nullable=False)
    preview_metadata = Column('preview_metadata', JSONB, default=dict, server_default='{}')
    source_draft_id = Column('source_draft_id', BigInteger)
    document_key = Column('document_key', Text)

    file_key = Column('file_key', Text)
    original_filename = Column('original_filename', Text)
    confidence = Column('confidence', Float)
    raw_data = Column('raw_data', JSONB)
    error_code = Column('error_code', Text)
    error_message = Column('error_message', Text)

    file_hash_sha256 = Column('file_hash_sha256', Text)
    title_hash_sha256 = Column('title_hash_sha256', Text)
    title_key = Column('title_key', Text)

    created_at = Column('created_at', DateTime)
    updated_at = Column('updated_at', DateTime)
    created_by = Column('created_by', Text)
    updated_by = Column('updated_by', Text)
