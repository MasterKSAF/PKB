from sqlalchemy import Column, Text, Boolean, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class Terminology(Base):
    __tablename__ = 'terminology'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', BigInteger, primary_key=True, autoincrement=True)
    raw_term = Column('raw_term', Text, nullable=False, unique=True)
    standard_term = Column('standard_term', Text, nullable=False)
    normalized_value = Column('normalized_value', Text, nullable=False)
    term_type = Column('term_type', Text, nullable=False)
    is_blocked = Column('is_blocked', Boolean, default=False)
    is_case_sensitive = Column('is_case_sensitive', Boolean, default=False, nullable=False)
    definition = Column('definition', Text)
    synonyms = Column('synonyms', JSONB, default=list, server_default='[]')
    related_docs = Column('related_docs', JSONB, default=list, server_default='[]')
    scope = Column('scope', JSONB, default=list, server_default='[]')
    created_at = Column('created_at', DateTime)
    updated_at = Column('updated_at', DateTime)
