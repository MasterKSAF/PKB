from sqlalchemy.orm import Session
from ..models.document import RegistryDocument
from ..schemas.document import RegistryDocumentCreate, RegistryDocumentUpdate

def get_document(db: Session, doc_id: int):
    return db.query(RegistryDocument).filter(RegistryDocument.doc_id == doc_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RegistryDocument).offset(skip).limit(limit).all()

def create_document(db: Session, document: RegistryDocumentCreate):
    db_document = RegistryDocument(**document.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_document(db: Session, db_document: RegistryDocument, document_update: RegistryDocumentUpdate):
    update_data = document_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_document, key, value)
    db.commit()
    db.refresh(db_document)
    return db_document

def delete_document(db: Session, doc_id: int):
    db_document = get_document(db, doc_id)
    if db_document:
        db.delete(db_document)
        db.commit()
    return db_document
