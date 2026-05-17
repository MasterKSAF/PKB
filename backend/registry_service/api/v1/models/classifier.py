from typing import Optional
import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKeyConstraint, Index, PrimaryKeyConstraint, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class ClassifierRegistryPurgatory(Base):
    __tablename__ = 'classifier_registry'
    __table_args__ = (
        ForeignKeyConstraint(['classifier_system', 'parent_code'], ['purgatory.classifier_registry.classifier_system', 'purgatory.classifier_registry.code'], name='classifier_registry_parent_code_fkey'),
        PrimaryKeyConstraint('classifier_system', 'code', name='classifier_registry_pkey'),
        Index('idx_classifier_system', 'classifier_system'),
        Index('idx_classifier_parent', 'parent_code'),
        {'comment': 'Hierarchical document classification (GOST/OST/ISO/DIN) with OKS mapping',
         'schema': 'purgatory'}
    )

    classifier_system: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text("'MKS'::text"))
    code: Mapped[str] = mapped_column(Text, primary_key=True)
    parent_code: Mapped[Optional[str]] = mapped_column(Text)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(Text, server_default=text("'active'::text"))
    effective_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    replaced_by: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    classifier_registry_purgatory: Mapped[Optional['ClassifierRegistryPurgatory']] = relationship(
        'ClassifierRegistryPurgatory',
        remote_side=[code],
        foreign_keys='[ClassifierRegistryPurgatory.parent_code]',
        back_populates='classifier_registry_reverse_purgatory'
    )
    classifier_registry_reverse_purgatory: Mapped[list['ClassifierRegistryPurgatory']] = relationship(
        'ClassifierRegistryPurgatory',
        foreign_keys='[ClassifierRegistryPurgatory.parent_code]',
        back_populates='classifier_registry_purgatory'
    )
    documents_mks_purgatory: Mapped[list['DocumentsPurgatory']] = relationship(
        'DocumentsPurgatory',
        foreign_keys='[DocumentsPurgatory.classifier_system, DocumentsPurgatory.mks_oks_code]',
        back_populates='mks_classifier_purgatory',
        overlaps='documents_okstu_purgatory'
    )
    documents_okstu_purgatory: Mapped[list['DocumentsPurgatory']] = relationship(
        'DocumentsPurgatory',
        foreign_keys='[DocumentsPurgatory.classifier_system, DocumentsPurgatory.okstu_code]',
        back_populates='okstu_classifier_purgatory',
        overlaps='documents_mks_purgatory'
    )
