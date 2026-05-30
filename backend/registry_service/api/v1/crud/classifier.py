from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from api.v1.models import Classifier


def get_classifiers(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    classifier_system: Optional[str] = None,
    status: Optional[str] = None,
    full_name: Optional[str] = None,
    parent_code: Optional[str] = None,
) -> tuple[List[Classifier], int]:
    query = db.query(Classifier)

    if classifier_system:
        query = query.filter(Classifier.classifier_system == classifier_system)

    if status:
        query = query.filter(Classifier.status == status)

    if full_name:
        query = query.filter(Classifier.full_name.ilike(f'%{full_name}%'))

    if parent_code:
        query = query.filter(Classifier.parent_code == parent_code)

    total = query.count()
    skip = (page - 1) * page_size
    classifiers = query.order_by(desc(Classifier.created_at)).offset(skip).limit(page_size).all()
    return classifiers, total


def get_classifier(db: Session, classifier_system: str, code: str) -> Optional[Classifier]:
    return db.query(Classifier).filter(
        Classifier.classifier_system == classifier_system,
        Classifier.code == code,
    ).first()


def create_classifier(
    db: Session,
    classifier_system: str,
    code: str,
    full_name: str,
    parent_code: Optional[str] = None,
    status: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs,
) -> Classifier:
    classifier = Classifier(
        classifier_system=classifier_system,
        code=code,
        full_name=full_name,
        parent_code=parent_code,
        status=status or 'active',
        description=description,
        **kwargs,
    )
    db.add(classifier)
    db.commit()
    db.refresh(classifier)
    return classifier


def update_classifier(db: Session, classifier_system: str, code: str, **kwargs) -> Optional[Classifier]:
    classifier = get_classifier(db, classifier_system, code)
    if not classifier:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(classifier, key):
            setattr(classifier, key, value)

    db.commit()
    db.refresh(classifier)
    return classifier


def delete_classifier(db: Session, classifier_system: str, code: str, force: bool = False) -> bool:
    classifier = get_classifier(db, classifier_system, code)
    if not classifier:
        return False

    children = db.query(Classifier).filter(Classifier.parent_code == classifier.code).count()
    if children and not force:
        raise ValueError('Classifier has dependent children and cannot be deleted without force')

    db.delete(classifier)
    db.commit()
    return True


def get_classifier_tree(
    db: Session,
    classifier_system: str,
    root_code: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Classifier]:
    query = db.query(Classifier).filter(Classifier.classifier_system == classifier_system)

    if root_code:
        query = query.filter(or_(Classifier.code == root_code, Classifier.parent_code == root_code))

    if search:
        query = query.filter(
            or_(
                Classifier.full_name.ilike(f'%{search}%'),
                Classifier.code.ilike(f'%{search}%'),
            )
        )

    return query.order_by(desc(Classifier.created_at)).all()
