import uuid

from sqlalchemy import Column, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class Terminology(Base):
    __tablename__ = 'terminology'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_term = Column('raw_term', Text, nullable=False)
    standard_term = Column('standard_term', Text, nullable=False)
    normalized_value = Column('normalized_value', Text, nullable=False)
    term_type = Column('term_type', Text, nullable=False)
    is_blocked = Column('is_blocked', Boolean, default=False)
    definition = Column('definition', Text)
    created_at = Column('created_at', DateTime)
    updated_at = Column('updated_at', DateTime)
