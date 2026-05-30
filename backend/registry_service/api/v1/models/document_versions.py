from sqlalchemy import Column, Integer, Text, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class DocumentVersion(Base):
    __tablename__ = 'document_versions'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', UUID(as_uuid=True), primary_key=True)
    document_id = Column('document_id', UUID(as_uuid=True), nullable=False)
    version_number = Column('version_number', Integer)
    file_hash_sha256 = Column('file_hash_sha256', Text)
    file_size_bytes = Column('file_size_bytes', BigInteger)
    format_code = Column('format_code', Text)
    format_label = Column('format_label', Text)
    file_key = Column('file_key', Text)
    uploaded_by = Column('uploaded_by', Text)
    uploaded_at = Column('uploaded_at', DateTime)
