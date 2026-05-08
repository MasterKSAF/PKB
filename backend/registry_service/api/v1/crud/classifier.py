from sqlalchemy.orm import Session
from ..models.classifier import ClassifierRegistry
from ..schemas.classifier import ClassifierRegistryCreate, ClassifierRegistryUpdate

def get_classifier(db: Session, code: str):
    return db.query(ClassifierRegistry).filter(ClassifierRegistry.code == code).first()

def get_classifiers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ClassifierRegistry).offset(skip).limit(limit).all()

def create_classifier(db: Session, classifier: ClassifierRegistryCreate):
    db_classifier = ClassifierRegistry(**classifier.model_dump())
    db.add(db_classifier)
    db.commit()
    db.refresh(db_classifier)
    return db_classifier

def update_classifier(db: Session, db_classifier: ClassifierRegistry, classifier_update: ClassifierRegistryUpdate):
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
