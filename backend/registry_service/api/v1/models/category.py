from sqlalchemy import Column, String, Text, BigInteger, ForeignKey
from .base import Base

class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = {'schema': 'registry'}

    category_id = Column('category_id', BigInteger, primary_key=True, autoincrement=True)
    code = Column('code', Text, nullable=False, unique=True)
    name = Column('name', Text, nullable=False)

class DocumentCategory(Base):
    __tablename__ = 'document_categories'
    __table_args__ = {'schema': 'registry'}

    document_id = Column('document_id', BigInteger, ForeignKey('registry.documents.id', ondelete='CASCADE'), primary_key=True)
    category_id = Column('category_id', BigInteger, ForeignKey('registry.categories.category_id', ondelete='CASCADE'), primary_key=True)
