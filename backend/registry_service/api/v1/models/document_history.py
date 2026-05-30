from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class DocumentHistory(Base):
    __tablename__ = 'document_history'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', UUID(as_uuid=True), primary_key=True)
    document_id = Column('document_id', UUID(as_uuid=True), nullable=False)
    event_type = Column('event_type', Text)
    old_status = Column('old_status', Text)
    new_status = Column('new_status', Text)
    comment = Column('comment', Text)
    changed_by = Column('changed_by', Text)
    document_snapshot = Column('document_snapshot', JSONB)
    event_at = Column('event_at', DateTime)
