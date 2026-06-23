from typing import Optional, List
from sqlalchemy.orm import Session
from api.v1.models.files import File

def get_file_by_id(db: Session, file_id: str) -> Optional[File]:
    return db.query(File).filter(File.file_id == file_id).first()

def get_files_by_document_id(db: Session, document_id: int) -> List[File]:
    # related_document_id is stored as string in the database
    return db.query(File).filter(File.related_document_id == str(document_id)).all()
