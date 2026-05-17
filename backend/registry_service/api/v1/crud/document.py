from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import date
from ..models.document import DocumentsPurgatory, DocStatus
from ..schemas.document import DocumentsPurgatoryCreate, DocumentsPurgatoryUpdate

def get_document(db: Session, doc_id: UUID):
    return db.query(DocumentsPurgatory).filter(DocumentsPurgatory.id == doc_id).first()

def get_documents(db: Session, 
                  title: Optional[str] = None,
                  doc_code: Optional[str] = None,
                  source_type: Optional[str] = None,
                  mks_oks_code: Optional[str] = None,
                  okstu_code: Optional[str] = None,
                  status: Optional[str] = None,
                  era: Optional[str] = None,
                  validity_status: Optional[str] = None,
                  jurisdiction: Optional[str] = None,
                  issuing_body: Optional[str] = None,
                  date_from: Optional[date] = None,
                  date_to: Optional[date] = None,
                  skip: int = 0, limit: int = 100):
    query = db.query(DocumentsPurgatory)
    
    if title:
        query = query.filter(DocumentsPurgatory.title.ilike(f"%{title}%"))
    if doc_code:
        query = query.filter(DocumentsPurgatory.doc_code == doc_code)
    if source_type:
        query = query.filter(DocumentsPurgatory.source_type == source_type)
    if mks_oks_code:
        query = query.filter(DocumentsPurgatory.mks_oks_code == mks_oks_code)
    if okstu_code:
        query = query.filter(DocumentsPurgatory.okstu_code == okstu_code)
    if status:
        query = query.filter(DocumentsPurgatory.status == status)
    if era:
        query = query.filter(DocumentsPurgatory.era == era)
    if validity_status:
        query = query.filter(DocumentsPurgatory.validity_status == validity_status)
    if jurisdiction:
        query = query.filter(DocumentsPurgatory.jurisdiction == jurisdiction)
    if issuing_body:
        query = query.filter(DocumentsPurgatory.issuing_body == issuing_body)
    if date_from:
        query = query.filter(DocumentsPurgatory.created_at >= date_from)
    if date_to:
        query = query.filter(DocumentsPurgatory.created_at <= date_to)
        
    return query.offset(skip).limit(limit).all(), query.count()

def create_document(db: Session, document: DocumentsPurgatoryCreate):
    db_document = DocumentsPurgatory(
        title=document.title,
        doc_code=document.doc_code,
        source_type=document.source_type,
        era=document.era,
        validity_status=document.validity_status,
        jurisdiction=document.jurisdiction,
        issuing_body=document.issuing_body,
        classifier_system=document.classifier_system,
        mks_oks_code=document.mks_oks_code,
        okstu_code=document.okstu_code,
        classification_status=document.classification_status,
        successor_doc_id=document.successor_doc_id,
        predecessor_doc_id=document.predecessor_doc_id,
        metadata_=document.metadata,
        status=document.status if document.status is not None else DocStatus.DRAFT
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_document(db: Session, db_document: DocumentsPurgatory, document_update: DocumentsPurgatoryUpdate):
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
