from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from api.v1.models import Document


def get_documents(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    doc_code: Optional[str] = None,
    processing_status: Optional[str] = None,
) -> tuple[List[Document], int]:
    """Retrieve documents with pagination and optional filters."""
    query = db.query(Document)

    if doc_code:
        query = query.filter(Document.doc_code.ilike(f'%{doc_code}%'))
    
    if processing_status:
        query = query.filter(Document.processing_status == processing_status)
    
    total = query.count()
    
    skip = (page - 1) * page_size
    documents = query.order_by(desc(Document.created_at)).offset(skip).limit(page_size).all()
    
    return documents, total


def get_document_by_id(db: Session, document_id: str) -> Optional[Document]:
    """Retrieve a single document by ID."""
    return db.query(Document).filter(Document.id == document_id).first()


def create_document(db: Session, doc_code: str, title: str, **kwargs) -> Document:
    """Create a new document."""
    document = Document(
        doc_code=doc_code,
        title=title,
        **kwargs
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def update_document(db: Session, document_id: str, **kwargs) -> Optional[Document]:
    """Update a document."""
    document = get_document_by_id(db, document_id)
    if not document:
        return None
    
    for key, value in kwargs.items():
        if value is not None and hasattr(document, key):
            setattr(document, key, value)
    
    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, document_id: str) -> bool:
    """Delete a document."""
    document = get_document_by_id(db, document_id)
    if not document:
        return False
    
    db.delete(document)
    db.commit()
    return True
