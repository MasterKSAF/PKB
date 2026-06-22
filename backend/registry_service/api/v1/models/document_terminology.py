from sqlalchemy import Column, String, Text, BigInteger, ForeignKey
from .base import Base

class DocumentTerminology(Base):
    __tablename__ = 'document_terminology'
    __table_args__ = {'schema': 'registry'}

    term_id = Column('term_id', BigInteger, primary_key=True, autoincrement=True)
    document_id = Column('document_id', BigInteger, ForeignKey('registry.documents.id', ondelete='CASCADE'), nullable=False)
    term = Column('term', Text, nullable=False)
    normalized_term = Column('normalized_term', Text, nullable=False)
    category = Column('category', Text)
    language = Column('language', String(10))
