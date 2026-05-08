from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from ..models.terminology import TerminologyRegistry
from ..schemas.terminology import TerminologyRegistryCreate, TerminologyRegistryUpdate

def get_term(db: Session, term_id: UUID):
    return db.query(TerminologyRegistry).filter(TerminologyRegistry.id == term_id).first()

def get_terms(db: Session, 
              term: Optional[str] = None,
              normalized_term: Optional[str] = None,
              context: Optional[str] = None,
              source: Optional[str] = None,
              skip: int = 0, limit: int = 100):
    query = db.query(TerminologyRegistry)
    
    if term:
        query = query.filter(TerminologyRegistry.raw_term.ilike(f"%{term}%"))
    if normalized_term:
        query = query.filter(TerminologyRegistry.normalized_value == normalized_term)
    if context:
        query = query.filter(TerminologyRegistry.scope['context'].astext == context)
    if source:
        query = query.filter(TerminologyRegistry.scope['source'].astext == source)
        
    return query.offset(skip).limit(limit).all(), query.count()

def get_term_by_raw_and_context(db: Session, raw_term: str, context: str):
    return db.query(TerminologyRegistry).filter(
        TerminologyRegistry.raw_term == raw_term,
        TerminologyRegistry.scope['context'].astext == context
    ).first()

def normalize_term(db: Session, term: str, context: Optional[str] = None):
    query = db.query(TerminologyRegistry).filter(TerminologyRegistry.raw_term == term)
    if context:
        query = query.filter(TerminologyRegistry.scope['context'].astext == context)
    return query.first()

def create_term(db: Session, term: TerminologyRegistryCreate):
    scope_data = {"context": term.context, "source": term.source}
    db_term = TerminologyRegistry(
        raw_term=term.term,
        standard_term=term.normalized_term,
        normalized_value=term.normalized_term,
        scope=scope_data
    )
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term

def update_term(db: Session, db_term: TerminologyRegistry, term_update: TerminologyRegistryUpdate):
    if term_update.term is not None:
        db_term.raw_term = term_update.term
    if term_update.normalized_term is not None:
        db_term.standard_term = term_update.normalized_term
        db_term.normalized_value = term_update.normalized_term
        
    scope = db_term.scope or {}
    if term_update.context is not None:
        scope["context"] = term_update.context
    if term_update.source is not None:
        scope["source"] = term_update.source
    db_term.scope = scope
    
    db.commit()
    db.refresh(db_term)
    return db_term

def delete_term(db: Session, term_id: UUID):
    db_term = get_term(db, term_id)
    if db_term:
        db.delete(db_term)
        db.commit()
    return db_term
