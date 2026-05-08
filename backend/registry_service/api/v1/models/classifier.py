from typing import Optional
import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKeyConstraint, Index, PrimaryKeyConstraint, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class ClassifierRegistry(Base):
    __tablename__ = 'classifier_registry'
    __table_args__ = (
        ForeignKeyConstraint(['parent_code'], ['purgatory.classifier_registry.code'], name='classifier_registry_parent_code_fkey'),
        PrimaryKeyConstraint('code', name='classifier_registry_pkey'),
        Index('idx_classifier_jurisdiction', 'jurisdiction', 'doc_type'),
        Index('idx_classifier_oks', 'oks_code'),
        Index('idx_classifier_parent', 'parent_code'),
        {'comment': 'Hierarchical document classification (GOST/OST/ISO/DIN) with OKS mapping',
         'schema': 'purgatory'}
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    parent_code: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(Text, server_default=text("'active'::text"))
    effective_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    replaced_by: Mapped[Optional[str]] = mapped_column(Text)
    jurisdiction: Mapped[Optional[str]] = mapped_column(Text)
    issuing_body: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(Text, server_default=text("'ru'::text"))
    oks_code: Mapped[Optional[str]] = mapped_column(Text)
    doc_type: Mapped[Optional[str]] = mapped_column(Text)
    is_thematic: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    external_id: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    classifier_registry: Mapped[Optional['ClassifierRegistry']] = relationship('ClassifierRegistry', remote_side=[code], back_populates='classifier_registry_reverse')
    classifier_registry_reverse: Mapped[list['ClassifierRegistry']] = relationship('ClassifierRegistry', remote_side=[parent_code], back_populates='classifier_registry')
    documents: Mapped[list['Documents']] = relationship('Documents', back_populates='classifier_registry')
