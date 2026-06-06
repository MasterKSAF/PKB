from sqlalchemy import Column, String, BigInteger, DateTime, Text

from .base import Base


class File(Base):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'public'}

    file_id = Column('file_id', String, primary_key=True)
    filename = Column('filename', String, nullable=False)
    size = Column('size', BigInteger, nullable=False)
    mime_type = Column('mime_type', String, nullable=False)
    url = Column('url', String, nullable=False)
    uploaded_at = Column('uploaded_at', DateTime)
    related_document_id = Column('related_document_id', String)
    storage_path = Column('storage_path', String, nullable=False)
