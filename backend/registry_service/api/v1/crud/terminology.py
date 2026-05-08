from sqlalchemy.orm import Session
from uuid import UUID
from ..models.terminology import TerminologyRegistry
from ..schemas.terminology import TerminologyRegistryCreate, TerminologyRegistryUpdate

def get_term(db: Session, term_id: UUID):
    return db.query(TerminologyRegistry).filter(TerminologyRegistry.id == term_id).first()

def get_terms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TerminologyRegistry).offset(skip).limit(limit).all()

def create_term(db: Session, term: TerminologyRegistryCreate):
    db_term = TerminologyRegistry(**term.model_dump())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term

def update_term(db: Session, db_term: TerminologyRegistry, term_update: TerminologyRegistryUpdate):
    update_data = term_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_term, key, value)
    db.commit()
    db.refresh(db_term)
    return db_term

def delete_term(db: Session, term_id: UUID):
    db_term = get_term(db, term_id)
    if db_term:
        db.delete(db_term)
        db.commit()
    return db_term
