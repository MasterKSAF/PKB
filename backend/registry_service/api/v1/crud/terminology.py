from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from ..models.terminology import TerminologyRegistryPurgatory
from ..schemas.terminology import TerminologyRegistryPurgatoryCreate, TerminologyRegistryPurgatoryUpdate

def get_term(db: Session, term_id: UUID):
    return db.query(TerminologyRegistryPurgatory).filter(TerminologyRegistryPurgatory.id == term_id).first()

def get_terms(db: Session, 
              raw_term: Optional[str] = None,
              normalized_term: Optional[str] = None,
              term_type: Optional[str] = None,
              is_blocked: Optional[bool] = None,
              skip: int = 0, limit: int = 100):
    query = db.query(TerminologyRegistryPurgatory)
    
    if raw_term:
        query = query.filter(TerminologyRegistryPurgatory.raw_term.ilike(f"%{raw_term}%"))
    if normalized_term:
        query = query.filter(TerminologyRegistryPurgatory.normalized_value == normalized_term)
    if term_type:
        query = query.filter(TerminologyRegistryPurgatory.term_type == term_type)
    if is_blocked is not None:
        query = query.filter(TerminologyRegistryPurgatory.is_blocked == is_blocked)
        
    return query.offset(skip).limit(limit).all(), query.count()

def normalize_term(db: Session, term: str):
    return db.query(TerminologyRegistryPurgatory).filter(TerminologyRegistryPurgatory.raw_term == term).first()

def create_term(db: Session, term: TerminologyRegistryPurgatoryCreate):
    db_term = TerminologyRegistryPurgatory(
        raw_term=term.raw_term,
        standard_term=term.standard_term,
        normalized_value=term.normalized_value,
        term_type=term.term_type,
        is_case_sensitive=term.is_case_sensitive,
        definition=term.definition,
        synonyms=term.synonyms,
        related_docs=term.related_docs,
        scope=term.scope,
        is_blocked=term.is_blocked
    )
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term

def update_term(db: Session, db_term: TerminologyRegistryPurgatory, term_update: TerminologyRegistryPurgatoryUpdate, is_patch: bool = False):
    if is_patch:
        update_data = term_update
    else:
        update_data = term_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_term, field, value)
    db.commit()
    db.refresh(db_term)
    return db_term

def delete_term(db: Session, term_id: UUID):
    db_term = get_term(db, term_id)
    if db_term:
        db.delete(db_term)
        db.commit()
    return db_term
