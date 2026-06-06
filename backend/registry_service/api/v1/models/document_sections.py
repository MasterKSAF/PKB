from sqlalchemy import Column, Text, Integer, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class DocumentSection(Base):
    __tablename__ = 'document_sections'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', BigInteger, primary_key=True)
    document_id = Column('document_id', UUID(as_uuid=True), nullable=False)
    parent_id = Column('parent_id', BigInteger)
    clause = Column('clause', Text)
    title = Column('title', Text)
    level = Column('level', Integer)
    path = Column('path', Text)
    page = Column('page', Integer)
    bbox = Column('bbox', JSONB)
    type_ = Column('type', Text)
    content = Column('content', JSONB)
    created_at = Column('created_at', DateTime)
