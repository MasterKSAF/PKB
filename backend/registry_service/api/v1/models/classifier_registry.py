from sqlalchemy import Column, String, Text, BigInteger, Boolean
from .base import Base

class ClassifierRegistry(Base):
    __tablename__ = 'classifier_registry'
    __table_args__ = {'schema': 'registry'}

    classifier_id = Column('classifier_id', BigInteger, primary_key=True, autoincrement=True)
    code = Column('code', Text, nullable=False)
    name = Column('name', Text, nullable=False)
    parent_id = Column('parent_id', BigInteger)
    type_ = Column('type', String(20), nullable=False)  # mks, oks, okstu, udk
    is_active = Column('is_active', Boolean, default=True, nullable=False)
