from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class ClassifierNode(Base):
    __tablename__ = "classifier_registry"

    code = Column(String(50), primary_key=True, index=True)
    parent_code = Column(String(50), ForeignKey("classifier_registry.code"), nullable=True)
    full_name = Column(String(500), nullable=False)
    doc_type = Column(String(20), nullable=False, server_default="OKS")
    jurisdiction = Column(String(10), nullable=False, server_default="RF")
    language = Column(String(5), nullable=False, server_default="ru")
    oks_code = Column(String(20), nullable=True)
    is_thematic = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    parent = relationship("ClassifierNode", remote_side=[code], backref="children")
    documents = relationship("RegistryDocument", back_populates="classifier")
