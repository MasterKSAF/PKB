import uuid

from sqlalchemy import Column, String, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class ClassifierPending(Base):
    __tablename__ = 'classifier_pending'
    __table_args__ = (
        UniqueConstraint('system', 'code', name='unique_classifier_pending_system_code'),
        {'schema': 'registry'},
    )

    id = Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system = Column('system', String(20), nullable=False)
    code = Column('code', Text, nullable=False)
    found_in_document_id = Column('found_in_document_id', UUID(as_uuid=True))
    status = Column('status', String(20), nullable=False, default='new')
    admin_comment = Column('admin_comment', Text)
    created_at = Column('created_at', DateTime)
