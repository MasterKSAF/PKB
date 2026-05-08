from sqlalchemy.orm import Session
from uuid import UUID
from ..models.document import Documents
from ..schemas.document import DocumentsCreate, DocumentsUpdate

def get_document(db: Session, doc_id: UUID):
    return db.query(Documents).filter(Documents.id == doc_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Documents).offset(skip).limit(limit).all()

def create_document(db: Session, document: DocumentsCreate):
    db_document = Documents(**document.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_document(db: Session, db_document: Documents, document_update: DocumentsUpdate):
    update_data = document_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_document, key, value)
    db.commit()
    db.refresh(db_document)
    return db_document

def delete_document(db: Session, doc_id: UUID):
    db_document = get_document(db, doc_id)
    if db_document:
        db.delete(db_document)
        db.commit()
    return db_document
