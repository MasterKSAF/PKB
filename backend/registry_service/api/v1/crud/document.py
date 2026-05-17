from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import date
from ..models.document import DocumentsPurgatory, DocStatus
from ..schemas.document import DocumentsCreate, DocumentsUpdate

def get_document(db: Session, doc_id: UUID):
    return db.query(DocumentsPurgatory).filter(DocumentsPurgatory.id == doc_id).first()

def get_documents(db: Session, 
                  title: Optional[str] = None,
                  doc_number: Optional[str] = None,
                  classifier_code: Optional[str] = None,
                  status: Optional[str] = None,
                  source: Optional[str] = None,
                  date_from: Optional[date] = None,
                  date_to: Optional[date] = None,
                  skip: int = 0, limit: int = 100):
    query = db.query(DocumentsPurgatory)
    
    if title:
        query = query.filter(DocumentsPurgatory.title.ilike(f"%{title}%"))
    if doc_number:
        query = query.filter(DocumentsPurgatory.doc_code == doc_number)
    if classifier_code:
        query = query.filter(DocumentsPurgatory.classifier_code == classifier_code)
    if status:
        query = query.filter(DocumentsPurgatory.status == status)
    if source:
        query = query.filter(DocumentsPurgatory.metadata_['source'].astext == source)
    if date_from:
        query = query.filter(DocumentsPurgatory.created_at >= date_from)
    if date_to:
        query = query.filter(DocumentsPurgatory.created_at <= date_to)
        
    return query.offset(skip).limit(limit).all(), query.count()

def create_document(db: Session, document: DocumentsCreate):
    meta = {"source": document.source, "notes": document.notes}
    db_document = DocumentsPurgatory(
        title=document.title,
        doc_code=document.doc_number,
        classifier_code=document.classifier_code,
        status=document.status or DocStatus.DRAFT,
        metadata_=meta
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_document(db: Session, db_document: DocumentsPurgatory, document_update: DocumentsUpdate):
    if document_update.title is not None:
        db_document.title = document_update.title
    if document_update.doc_number is not None:
        db_document.doc_code = document_update.doc_number
    if document_update.classifier_code is not None:
        db_document.classifier_code = document_update.classifier_code
    if document_update.status is not None:
        db_document.status = document_update.status
        
    meta = dict(db_document.metadata_ or {})
    if document_update.source is not None:
        meta["source"] = document_update.source
    if document_update.notes is not None:
        meta["notes"] = document_update.notes
    db_document.metadata_ = meta
    
    db.commit()
    db.refresh(db_document)
    return db_document

def delete_document(db: Session, doc_id: UUID):
    db_document = get_document(db, doc_id)
    if db_document:
        db.delete(db_document)
        db.commit()
    return db_document
