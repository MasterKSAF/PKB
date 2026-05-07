from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class RegistryDocument(Base):
    __tablename__ = "registry_documents"

    doc_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    doc_number = Column(String(100), nullable=True)
    classifier_code = Column(String(50), ForeignKey("classifier_registry.code"), nullable=True)
    status = Column(String(20), nullable=False, server_default="draft")
    source = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    classifier = relationship("ClassifierNode", back_populates="documents")
