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
    code: Optional[str] = None,
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

    if code:
        query = query.filter(Classifier.code.ilike(f'%{code}%'))

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
        if hasattr(classifier, key):
            setattr(classifier, key, value)

    db.commit()
    db.refresh(classifier)
    return classifier


def delete_classifier(db: Session, classifier_system: str, code: str, force: bool = False) -> bool:
    classifier = get_classifier(db, classifier_system, code)
    if not classifier:
        return False

    children = db.query(Classifier).filter(
        Classifier.classifier_system == classifier_system,
        Classifier.parent_code == classifier.code
    ).count()
    if children and not force:
        raise ValueError('HAS_CHILDREN')

    from api.v1.models.document import Document
    doc_count = 0
    if classifier_system == 'MKS':
        doc_count = db.query(Document).filter(Document.mks_oks_code == code).count()
    elif classifier_system == 'OKSTU':
        doc_count = db.query(Document).filter(Document.okstu_code == code).count()
    elif classifier_system == 'UDC':
        doc_count = db.query(Document).filter(Document.udc == code).count()
    elif classifier_system == 'EXTERNAL':
        doc_count = db.query(Document).filter(Document.classifier_code == code).count()
    
    if doc_count and not force:
        raise ValueError('HAS_DOCUMENTS')

    if force:
        # Nullify parent_code for direct children to avoid FK violation
        db.query(Classifier).filter(
            Classifier.classifier_system == classifier_system,
            Classifier.parent_code == classifier.code
        ).update({Classifier.parent_code: None}, synchronize_session=False)

        # Nullify document references
        if classifier_system == 'MKS':
            db.query(Document).filter(Document.mks_oks_code == code).update({Document.mks_oks_code: None}, synchronize_session=False)
        elif classifier_system == 'OKSTU':
            db.query(Document).filter(Document.okstu_code == code).update({Document.okstu_code: None}, synchronize_session=False)
        elif classifier_system == 'UDC':
            db.query(Document).filter(Document.udc == code).update({Document.udc: None}, synchronize_session=False)
        elif classifier_system == 'EXTERNAL':
            db.query(Document).filter(Document.classifier_code == code).update({Document.classifier_code: None}, synchronize_session=False)

    db.delete(classifier)
    db.commit()
    return True


def get_classifier_tree(
    db: Session,
    classifier_system: str,
    root_code: Optional[str] = None,
    search: Optional[str] = None,
    max_depth: int = 10,
    status: Optional[str] = None,
) -> List[Classifier]:
    # Query all nodes for the given system
    query = db.query(Classifier).filter(Classifier.classifier_system == classifier_system)
    if status:
        query = query.filter(Classifier.status == status)
    
    all_nodes = query.all()
    if not all_nodes:
        return []

    # Map nodes by code for easy access
    nodes_by_code = {node.code: node for node in all_nodes}
    
    # Initialize children list on all nodes
    for node in all_nodes:
        node.children = []

    # Determine which nodes to include in the pool
    included_codes = set(nodes_by_code.keys())
    if search:
        matching_codes = {
            code for code, node in nodes_by_code.items()
            if search.lower() in (node.full_name or "").lower() or search.lower() in (node.code or "").lower()
        }
        
        pool = set()
        for m_code in matching_codes:
            curr = m_code
            while curr in nodes_by_code:
                pool.add(curr)
                curr_node = nodes_by_code[curr]
                curr = curr_node.parent_code
                if curr == m_code or curr in pool:
                    break
            descendants = [m_code]
            while descendants:
                desc = descendants.pop()
                if desc in pool:
                    continue
                pool.add(desc)
                for child_code, child_node in nodes_by_code.items():
                    if child_node.parent_code == desc:
                        descendants.append(child_code)
        included_codes = pool

    # Build parent-child relationship map for the pool
    parent_to_children = {}
    for code in included_codes:
        node = nodes_by_code[code]
        parent = node.parent_code
        if parent:
            parent_to_children.setdefault(parent, []).append(node)

    max_depth_reached_flag = [False]

    # Recursive build function
    def build_tree(node, depth):
        children_nodes = parent_to_children.get(node.code, [])
        if depth >= max_depth:
            if children_nodes:
                max_depth_reached_flag[0] = True
            node.children = []
            return node
        children_nodes.sort(key=lambda x: x.code)
        node.children = []
        for child in children_nodes:
            node.children.append(build_tree(child, depth + 1))
        return node

    # Find root nodes
    roots = []
    if root_code:
        if root_code in nodes_by_code and root_code in included_codes:
            roots.append(nodes_by_code[root_code])
    else:
        for code in sorted(included_codes):
            node = nodes_by_code[code]
            if not node.parent_code or node.parent_code not in included_codes:
                roots.append(node)

    tree_roots = []
    for root in roots:
        tree_roots.append(build_tree(root, 1))

    return tree_roots, max_depth_reached_flag[0]


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
        pending_int = int(str(pending_id))
    except (ValueError, TypeError):
        return None
    return db.query(ClassifierPending).filter(ClassifierPending.id == pending_int).first()


def create_classifier_pending(
    db: Session,
    system: str,
    code: str,
    found_in_document_id: Optional[str] = None,
) -> ClassifierPending:
    document_int = None
    if found_in_document_id:
        try:
            document_int = int(str(found_in_document_id))
        except (ValueError, TypeError):
            document_int = None

    pending = ClassifierPending(
        system=system,
        code=code,
        found_in_document_id=document_int,
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
