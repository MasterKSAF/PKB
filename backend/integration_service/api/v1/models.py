from sqlalchemy import Column, String, DateTime, func, BigInteger
from api.v1.database import Base, engine

class FileRecord(Base):
    __tablename__ = "files"
    __table_args__ = {"schema": "public"}

    file_id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    size = Column(BigInteger, nullable=False)
    mime_type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=func.now())
    related_document_id = Column(String, nullable=True)
    storage_path = Column(String, nullable=False)

class ExportRecord(Base):
    __tablename__ = "exports"
    __table_args__ = {"schema": "public"}
    
    export_id = Column(String, primary_key=True, index=True)
    document_id = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=func.now())
    response_message = Column(String, nullable=False)

# Create tables if possible
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: could not create tables automatically: {e}")

