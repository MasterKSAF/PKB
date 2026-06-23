from typing import Optional, List
from sqlalchemy.orm import Session
from api.v1.models.document_versions import DocumentVersion

def get_versions_by_document_id(db: Session, document_id: int) -> List[DocumentVersion]:
    return db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).order_by(DocumentVersion.version_number.desc()).all()

def get_version_by_id(db: Session, version_id: int) -> Optional[DocumentVersion]:
    return db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
