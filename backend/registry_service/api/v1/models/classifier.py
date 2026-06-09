from sqlalchemy import Column, String, Text, DateTime, Date

from .base import Base


class Classifier(Base):
    __tablename__ = 'classifiers'
    __table_args__ = {'schema': 'registry'}

    classifier_system = Column('classifier_system', String(50), primary_key=True, nullable=False)
    code = Column('code', Text, primary_key=True, nullable=False)
    full_name = Column('full_name', Text, nullable=False)
    description = Column('description', Text)
    status = Column('status', String(50), default='active')
    parent_code = Column('parent_code', Text)
    effective_date = Column('effective_date', Date, nullable=True)
    replaced_by = Column('replaced_by', Text, nullable=True)
    created_at = Column('created_at', DateTime)
    updated_at = Column('updated_at', DateTime)
