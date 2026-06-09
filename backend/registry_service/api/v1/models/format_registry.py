from sqlalchemy import Column, Text, Boolean, DateTime, BigInteger
from datetime import datetime, timezone

from .base import Base


class FormatRegistry(Base):
    __tablename__ = 'format_registry'
    __table_args__ = {'schema': 'registry'}

    id = Column('id', BigInteger, primary_key=True, autoincrement=True)
    format_code = Column('format_code', Text, unique=True, nullable=False)
    mime_type = Column('mime_type', Text, nullable=False)
    parser_engine = Column('parser_engine', Text, nullable=False)
    supported = Column('supported', Boolean, default=True, nullable=False)
    created_at = Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

