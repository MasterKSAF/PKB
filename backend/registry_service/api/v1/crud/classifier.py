from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from ..models.classifier import ClassifierRegistryPurgatory
from ..schemas.classifier import ClassifierRegistryCreate, ClassifierRegistryUpdate

def get_classifier(db: Session, code: str):
    return db.query(ClassifierRegistryPurgatory).filter(ClassifierRegistryPurgatory.code == code).first()

def get_classifiers(db: Session, 
                    code: Optional[str] = None,
                    full_name: Optional[str] = None,
                    doc_type: Optional[str] = None,
                    jurisdiction: Optional[str] = None,
                    language: Optional[str] = None,
                    is_thematic: Optional[bool] = None,
                    parent_code: Optional[str] = None,
                    skip: int = 0, limit: int = 100):
    query = db.query(ClassifierRegistryPurgatory)
    
    if code:
        query = query.filter(ClassifierRegistryPurgatory.code.ilike(f"%{code}%"))
    if full_name:
        query = query.filter(ClassifierRegistryPurgatory.full_name.ilike(f"%{full_name}%"))
    if doc_type:
        query = query.filter(ClassifierRegistryPurgatory.doc_type == doc_type)
    if jurisdiction:
        query = query.filter(ClassifierRegistryPurgatory.jurisdiction == jurisdiction)
    if language:
        query = query.filter(ClassifierRegistryPurgatory.language == language)
    if is_thematic is not None:
        query = query.filter(ClassifierRegistryPurgatory.is_thematic == is_thematic)
    if parent_code:
        query = query.filter(ClassifierRegistryPurgatory.parent_code == parent_code)
        
    return query.offset(skip).limit(limit).all(), query.count()

def get_classifier_tree(db: Session, root_code: Optional[str] = None, max_depth: int = 10, search: Optional[str] = None):
    # For a real tree, we might use CTEs, but for simplicity we fetch and build in memory or just fetch children
    query = db.query(ClassifierRegistryPurgatory)
    if root_code:
        query = query.filter(ClassifierRegistryPurgatory.parent_code == root_code)
    else:
        query = query.filter(ClassifierRegistryPurgatory.parent_code == None)
        
    if search:
        query = query.filter(ClassifierRegistryPurgatory.full_name.ilike(f"%{search}%"))
        
    roots = query.all()
    # Eagerly loading children using SQLAlchemy relationships would be better, but doing it in memory or returning the roots is a start
    return roots, len(roots)

def create_classifier(db: Session, classifier: ClassifierRegistryCreate):
    db_classifier = ClassifierRegistryPurgatory(**classifier.model_dump())
    db.add(db_classifier)
    db.commit()
    db.refresh(db_classifier)
    return db_classifier

def update_classifier(db: Session, db_classifier: ClassifierRegistryPurgatory, classifier_update: ClassifierRegistryUpdate):
    update_data = classifier_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_classifier, key, value)
    db.commit()
    db.refresh(db_classifier)
    return db_classifier

def delete_classifier(db: Session, code: str):
    db_classifier = get_classifier(db, code)
    if db_classifier:
        db.delete(db_classifier)
        db.commit()
    return db_classifier
