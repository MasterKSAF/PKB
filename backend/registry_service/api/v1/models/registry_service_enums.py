from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func, text
import uuid
from ..database import Base


class RegistryServiceEnums(Base):
    __tablename__ = 'rs_enums'
    __table_args__ = {'schema': 'registry'}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    enum_key = Column(String(128), nullable=False, index=True)
    enum_value = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<RegistryServiceEnums {self.enum_key}={self.enum_value}>"

    @classmethod
    def get_values_by_key(cls, db_session, key: str):
        """Return list of `enum_value` for a given `enum_key`.

        Args:
            db_session: SQLAlchemy Session
            key: enum_key to filter by

        Returns:
            list of strings
        """
        rows = db_session.query(cls.enum_value).filter(cls.enum_key == key).order_by(cls.enum_value).all()
        return [r[0] for r in rows]

    @classmethod
    def get_all_values(cls, db_session):
        """Return all enum values grouped by `enum_key` as a dict.

        Args:
            db_session: SQLAlchemy Session

        Returns:
            dict: { enum_key: [values...] }
        """
        rows = db_session.query(cls.enum_key, cls.enum_value).order_by(cls.enum_key, cls.enum_value).all()
        result = {}
        for k, v in rows:
            result.setdefault(k, []).append(v)
        return result
