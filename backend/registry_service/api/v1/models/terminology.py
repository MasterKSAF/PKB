from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from .base import Base

class TerminologyEntry(Base):
    __tablename__ = "terminology_registry"

    term_id = Column(Integer, primary_key=True, index=True)
    term = Column(String(500), nullable=False)
    normalized_term = Column(String(500), nullable=False)
    context = Column(String(100), nullable=False, server_default="Общий")
    source = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('term', 'context', name='uq_terminology_term_context'),
    )
