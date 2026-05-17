from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from ..models.classifier import ClassifierRegistryPurgatory
from ..schemas.classifier import ClassifierRegistryPurgatoryCreate, ClassifierRegistryPurgatoryUpdate

def get_classifier(db: Session, classifier_system: str, code: str):
    return db.query(ClassifierRegistryPurgatory).filter(
        ClassifierRegistryPurgatory.classifier_system == classifier_system,
        ClassifierRegistryPurgatory.code == code
    ).first()

def get_classifiers(db: Session, 
                    classifier_system: Optional[str] = None,
                    code: Optional[str] = None,
                    full_name: Optional[str] = None,
                    status: Optional[str] = None,
                    parent_code: Optional[str] = None,
                    skip: int = 0, limit: int = 100):
    query = db.query(ClassifierRegistryPurgatory)
    
    if classifier_system:
        query = query.filter(ClassifierRegistryPurgatory.classifier_system == classifier_system)
    if code:
        query = query.filter(ClassifierRegistryPurgatory.code.ilike(f"%{code}%"))
    if full_name:
        query = query.filter(ClassifierRegistryPurgatory.full_name.ilike(f"%{full_name}%"))
    if status:
        query = query.filter(ClassifierRegistryPurgatory.status == status)
    if parent_code:
        query = query.filter(ClassifierRegistryPurgatory.parent_code == parent_code)
        
    return query.offset(skip).limit(limit).all(), query.count()

def get_classifier_tree(db: Session, classifier_system: Optional[str] = None, root_code: Optional[str] = None, max_depth: int = 10, search: Optional[str] = None):
    query = db.query(ClassifierRegistryPurgatory)
    
    if classifier_system:
        query = query.filter(ClassifierRegistryPurgatory.classifier_system == classifier_system)
    
    if root_code:
        query = query.filter(ClassifierRegistryPurgatory.parent_code == root_code)
    else:
        query = query.filter(ClassifierRegistryPurgatory.parent_code == None)
        
    if search:
        query = query.filter(ClassifierRegistryPurgatory.full_name.ilike(f"%{search}%"))
        
    roots = query.all()
    return roots, len(roots)

def create_classifier(db: Session, classifier: ClassifierRegistryPurgatoryCreate):
    db_classifier = ClassifierRegistryPurgatory(**classifier.model_dump())
    db.add(db_classifier)
    db.commit()
    db.refresh(db_classifier)
    return db_classifier

def update_classifier(db: Session, db_classifier: ClassifierRegistryPurgatory, classifier_update: ClassifierRegistryPurgatoryUpdate):
    update_data = classifier_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_classifier, key, value)
    db.commit()
    db.refresh(db_classifier)
    return db_classifier

def delete_classifier(db: Session, classifier_system: str, code: str):
    db_classifier = get_classifier(db, classifier_system, code)
    if db_classifier:
        db.delete(db_classifier)
        db.commit()
    return db_classifier
