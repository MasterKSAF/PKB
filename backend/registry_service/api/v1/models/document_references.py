from sqlalchemy import Column, Text, Date, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class DocumentReference(Base):
    __tablename__ = 'document_references'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', UUID(as_uuid=True), primary_key=True)
    source_document_id = Column('source_document_id', UUID(as_uuid=True), nullable=False)
    target_doc_code = Column('target_doc_code', Text, nullable=False)
    reference_type = Column('reference_type', Text)
    context = Column('context', Text)
    current_status = Column('current_status', Text)
    replaced_by = Column('replaced_by', Text)
    replacement_date = Column('replacement_date', Date)
    is_resolved = Column('is_resolved', Boolean)
    resolved_document_id = Column('resolved_document_id', UUID(as_uuid=True))
    created_at = Column('created_at', DateTime)
