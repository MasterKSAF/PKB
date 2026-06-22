from sqlalchemy import Column, Integer, Text, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class DocumentVersion(Base):
    __tablename__ = 'document_versions'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', BigInteger, primary_key=True, autoincrement=True)
    document_id = Column('document_id', BigInteger, nullable=False)
    version_number = Column('version_number', Integer)
    file_hash_sha256 = Column('file_hash_sha256', Text)
    file_size_bytes = Column('file_size_bytes', BigInteger)
    format_code = Column('format_code', Text)
    format_label = Column('format_label', Text)
    file_key = Column('file_key', Text)
    created_by = Column('created_by', Text)
    created_at = Column('created_at', DateTime)
    revision = Column('revision', Integer, nullable=False, default=1)
    source_filename = Column('source_filename', Text)
    file_path = Column('file_path', Text)
    updated_at = Column('updated_at', DateTime)
