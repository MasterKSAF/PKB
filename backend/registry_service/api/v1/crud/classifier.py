import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from api.v1.models import Classifier, ClassifierPending


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


def _classifier_lookup_status(db: Session, classifier_system: str, code: Optional[str]) -> str:
    if not code:
        return 'NOT_USED'
    if get_classifier(db, classifier_system, code):
        return 'CONFIRMED'
    return 'NOT_FOUND'


def validate_classification(db: Session, classification: Dict[str, Any]) -> Dict[str, Any]:
    mks_code = classification.get('mks_oks_code')
    okstu_code = classification.get('okstu_code')
    udk_code = classification.get('udk_code')

    mks_status = _classifier_lookup_status(db, 'MKS', mks_code)
    okstu_status = _classifier_lookup_status(db, 'OKSTU', okstu_code)
    udk_valid = bool(udk_code) and _classifier_lookup_status(db, 'UDC', udk_code) == 'CONFIRMED'

    mks_display_name = None
    if mks_code and mks_status == 'CONFIRMED':
        classifier = get_classifier(db, 'MKS', mks_code)
        mks_display_name = classifier.full_name if classifier else None

    checked_statuses = []
    if mks_code:
        checked_statuses.append(mks_status)
    if okstu_code:
        checked_statuses.append(okstu_status)

    if not checked_statuses and not udk_code:
        overall_status = 'invalid'
    elif checked_statuses and all(status == 'CONFIRMED' for status in checked_statuses):
        overall_status = 'valid'
    elif not checked_statuses and udk_code:
        overall_status = 'valid' if udk_valid else 'invalid'
    else:
        overall_status = 'invalid'

    if udk_code and not udk_valid:
        overall_status = 'invalid'

    return {
        'mks_status': mks_status,
        'mks_display_name': mks_display_name,
        'okstu_status': okstu_status,
        'udk_valid': udk_valid,
        'overall_status': overall_status,
    }


def get_classifier_pending(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    system: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[List[ClassifierPending], int]:
    query = db.query(ClassifierPending)
    if system:
        query = query.filter(ClassifierPending.system == system)
    if status:
        query = query.filter(ClassifierPending.status == status)

    total = query.count()
    skip = (page - 1) * page_size
    items = query.order_by(desc(ClassifierPending.created_at)).offset(skip).limit(page_size).all()
    return items, total


def get_classifier_pending_by_id(db: Session, pending_id: str) -> Optional[ClassifierPending]:
    try:
        pending_uuid = uuid.UUID(str(pending_id))
    except (ValueError, TypeError):
        return None
    return db.query(ClassifierPending).filter(ClassifierPending.id == pending_uuid).first()


def create_classifier_pending(
    db: Session,
    system: str,
    code: str,
    found_in_document_id: Optional[str] = None,
) -> ClassifierPending:
    document_uuid = None
    if found_in_document_id:
        try:
            document_uuid = uuid.UUID(str(found_in_document_id))
        except (ValueError, TypeError):
            document_uuid = None

    pending = ClassifierPending(
        system=system,
        code=code,
        found_in_document_id=document_uuid,
        status='new',
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)
    return pending


def accept_classifier_pending(
    db: Session,
    pending: ClassifierPending,
    full_name: str,
    parent_code: Optional[str] = None,
    admin_comment: Optional[str] = None,
) -> tuple[Classifier, ClassifierPending]:
    existing = get_classifier(db, pending.system, pending.code)
    if not existing:
        create_classifier(
            db,
            classifier_system=pending.system,
            code=pending.code,
            full_name=full_name,
            parent_code=parent_code,
            status='active',
        )

    pending.status = 'mapped'
    if admin_comment:
        pending.admin_comment = admin_comment
    db.commit()
    db.refresh(pending)
    classifier = get_classifier(db, pending.system, pending.code)
    return classifier, pending


def reject_classifier_pending(
    db: Session,
    pending: ClassifierPending,
    admin_comment: Optional[str] = None,
) -> ClassifierPending:
    pending.status = 'rejected'
    if admin_comment:
        pending.admin_comment = admin_comment
    db.commit()
    db.refresh(pending)
    return pending
