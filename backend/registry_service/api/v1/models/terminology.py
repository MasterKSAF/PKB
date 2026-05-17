from typing import Optional
import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Index, PrimaryKeyConstraint, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class TerminologyRegistryPurgatory(Base):
    __tablename__ = 'terminology_registry'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='terminology_registry_pkey'),
        UniqueConstraint('raw_term', name='terminology_registry_raw_term_key'),
        Index('idx_terminology_raw', 'raw_term'),
        Index('idx_terminology_standard', 'standard_term'),
        {'comment': 'Controlled vocabulary for title normalization and RAG glossary',
         'schema': 'purgatory'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    raw_term: Mapped[str] = mapped_column(Text, nullable=False)
    standard_term: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text, nullable=False)
    term_type: Mapped[Optional[str]] = mapped_column(Text, server_default=text("'term'::text"))
    is_case_sensitive: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    definition: Mapped[Optional[str]] = mapped_column(Text)
    synonyms: Mapped[Optional[dict]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    related_docs: Mapped[Optional[dict]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    scope: Mapped[Optional[dict]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    is_blocked: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
