from sqlalchemy import Column, String, DateTime

from .base import Base


class Export(Base):
    __tablename__ = 'exports'
    __table_args__ = {'schema': 'public'}

    export_id = Column('export_id', String, primary_key=True)
    document_id = Column('document_id', String, nullable=False)
    external_id = Column('external_id', String, nullable=False)
    status = Column('status', String, nullable=False)
    sent_at = Column('sent_at', DateTime)
    response_message = Column('response_message', String, nullable=False)
