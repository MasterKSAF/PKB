from sqlalchemy.orm import Session
from ..models.classifier import ClassifierNode
from ..schemas.classifier import ClassifierNodeCreate, ClassifierNodeUpdate

def get_classifier(db: Session, code: str):
    return db.query(ClassifierNode).filter(ClassifierNode.code == code).first()

def get_classifiers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ClassifierNode).offset(skip).limit(limit).all()

def create_classifier(db: Session, classifier: ClassifierNodeCreate):
    db_classifier = ClassifierNode(**classifier.model_dump())
    db.add(db_classifier)
    db.commit()
    db.refresh(db_classifier)
    return db_classifier

def update_classifier(db: Session, db_classifier: ClassifierNode, classifier_update: ClassifierNodeUpdate):
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
