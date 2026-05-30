import uuid

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class Classifier(Base):
    __tablename__ = 'classifiers'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classifier_system = Column('classifier_system', String(50), nullable=False)
    code = Column('code', Text, nullable=False)
    full_name = Column('full_name', Text, nullable=False)
    description = Column('description', Text)
    status = Column('status', String(50), default='active')
    parent_code = Column('parent_code', Text)
    created_at = Column('created_at', DateTime)
    updated_at = Column('updated_at', DateTime)
