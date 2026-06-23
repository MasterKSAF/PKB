import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.v1.models import Document, DocumentHistory, DocumentReference, DocumentSection

_BIGINT_FIELDS = ('successor_doc_id', 'predecessor_doc_id', 'draft_id', 'current_version_id')


def _coerce_int_fields(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    if 'metadata' in kwargs:
        kwargs['doc_metadata'] = kwargs.pop('metadata')
    if 'valid_until' in kwargs and kwargs['valid_until'] is None:
        from datetime import date
        kwargs['valid_until'] = date(9999, 12, 31)
    for key in _BIGINT_FIELDS:
        value = kwargs.get(key)
        if value is not None:
            try:
                kwargs[key] = int(str(value))
            except (ValueError, TypeError):
                kwargs[key] = None
    return kwargs


def populate_document_extra_fields(db: Session, documents: List[Document]) -> None:
    if not documents:
        return
        
    doc_ids = [d.id for d in documents]
    mks_codes = {d.mks_oks_code for d in documents if d.mks_oks_code}
    okstu_codes = {d.okstu_code for d in documents if d.okstu_code}
    
    # Batch query classifiers
    from api.v1.models import Classifier
    mks_names = {}
    if mks_codes:
        mks_rows = db.query(Classifier.code, Classifier.full_name).filter(
            Classifier.classifier_system == 'MKS',
            Classifier.code.in_(mks_codes)
        ).all()
        mks_names = {r.code: r.full_name for r in mks_rows}
        
    okstu_names = {}
    if okstu_codes:
        okstu_rows = db.query(Classifier.code, Classifier.full_name).filter(
            Classifier.classifier_system == 'OKSTU',
            Classifier.code.in_(okstu_codes)
        ).all()
        okstu_names = {r.code: r.full_name for r in okstu_rows}
        
    # Batch query document versions count
    from api.v1.models import DocumentVersion
    from sqlalchemy import func
    version_counts = {}
    if doc_ids:
        version_rows = db.query(
            DocumentVersion.document_id,
            func.count(DocumentVersion.id)
        ).filter(
            DocumentVersion.document_id.in_(doc_ids)
        ).group_by(
            DocumentVersion.document_id
        ).all()
        version_counts = {r[0]: r[1] for r in version_rows}
        
    for doc in documents:
        doc.mks_name = mks_names.get(doc.mks_oks_code) if doc.mks_oks_code else None
        doc.okstu_name = okstu_names.get(doc.okstu_code) if doc.okstu_code else None
        doc.total_versions = version_counts.get(doc.id, 0)


def get_documents(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    doc_code: Optional[str] = None,
    title: Optional[str] = None,
    status: Optional[str] = None,
    mks_oks_code: Optional[str] = None,
    source_type: Optional[str] = None,
    okstu_code: Optional[str] = None,
    era: Optional[str] = None,
    validity_status: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    issuing_body: Optional[str] = None,
    title_hash_sha256: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    valid_at: Optional[datetime] = None,
) -> tuple[List[Document], int]:
    """Retrieve documents with pagination and optional filters."""
    query = db.query(Document)

    if doc_code:
        query = query.filter(Document.doc_code.ilike(f'%{doc_code}%'))

    if title:
        query = query.filter(Document.title.ilike(f'%{title}%'))

    if status:
        query = query.filter(Document.status == status)

    if mks_oks_code:
        query = query.filter(Document.mks_oks_code == mks_oks_code)

    if source_type:
        query = query.filter(Document.source_type == source_type)

    if okstu_code:
        query = query.filter(Document.okstu_code == okstu_code)

    if era:
        query = query.filter(Document.era == era)

    if validity_status:
        query = query.filter(Document.validity_status == validity_status)

    if jurisdiction:
        query = query.filter(Document.jurisdiction == jurisdiction)

    if issuing_body:
        query = query.filter(Document.issuing_body.ilike(f'%{issuing_body}%'))

    if title_hash_sha256:
        query = query.filter(Document.title_hash_sha256 == title_hash_sha256)

    if date_from:
        query = query.filter(Document.created_at >= date_from)

    if date_to:
        query = query.filter(Document.created_at <= date_to)

    if valid_at:
        query = query.filter(Document.valid_from <= valid_at.date(), Document.valid_until >= valid_at.date())

    total = query.count()
    
    skip = (page - 1) * page_size
    documents = query.order_by(desc(Document.created_at)).offset(skip).limit(page_size).all()
    populate_document_extra_fields(db, documents)
    
    return documents, total


def get_document_by_id(db: Session, document_id: str) -> Optional[Document]:
    """Retrieve a single document by ID."""
    try:
        document_int = int(str(document_id))
    except (ValueError, TypeError):
        return None
    doc = db.query(Document).filter(Document.id == document_int).first()
    if doc:
        populate_document_extra_fields(db, [doc])
    return doc


def create_document(db: Session, doc_code: str, title: str, **kwargs) -> Document:
    """Create a new document."""
    if not kwargs.get('title_hash_sha256'):
        norm_title = kwargs.get('normalized_title') or (title or '').strip().lower()
        kwargs['title_hash_sha256'] = compute_title_hash_sha256(
            kwargs.get('era'),
            kwargs.get('source_type'),
            kwargs.get('mks_oks_code'),
            kwargs.get('okstu_code'),
            doc_code,
            norm_title
        )
    document = Document(
        doc_code=doc_code,
        title=title,
        **_coerce_int_fields(kwargs),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    populate_document_extra_fields(db, [document])
    check_and_quarantine_classifiers(db, document)
    return document


def update_document(db: Session, document_id: str, **kwargs) -> Optional[Document]:
    """Update a document."""
    document = get_document_by_id(db, document_id)
    if not document:
        return None
    
    key_fields = {'era', 'source_type', 'mks_oks_code', 'okstu_code', 'doc_code', 'title'}
    if any(k in kwargs for k in key_fields):
        doc_code = kwargs.get('doc_code', document.doc_code)
        title = kwargs.get('title', document.title)
        era = kwargs.get('era', document.era)
        source_type = kwargs.get('source_type', document.source_type)
        mks = kwargs.get('mks_oks_code', document.mks_oks_code)
        okstu = kwargs.get('okstu_code', document.okstu_code)
        norm_title = kwargs.get('normalized_title', document.normalized_title or (title or '').strip().lower())
        kwargs['title_hash_sha256'] = compute_title_hash_sha256(era, source_type, mks, okstu, doc_code, norm_title)

    for key, value in _coerce_int_fields(kwargs).items():
        if value is not None and hasattr(document, key):
            setattr(document, key, value)
    
    db.commit()
    db.refresh(document)
    populate_document_extra_fields(db, [document])
    check_and_quarantine_classifiers(db, document)
    return document


def delete_document(db: Session, document_id: str) -> bool:
    """Delete a document."""
    document = get_document_by_id(db, document_id)
    if not document:
        return False
    
    db.delete(document)
    db.commit()
    return True


def compute_title_hash_sha256(
    era: Optional[str],
    source_type: Optional[str],
    mks_oks_code: Optional[str],
    okstu_code: Optional[str],
    doc_code: Optional[str],
    normalized_title: Optional[str],
) -> str:
    payload = '|'.join([
        era or '',
        source_type or '',
        mks_oks_code or '',
        okstu_code or '',
        doc_code or '',
        normalized_title or '',
    ])
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def check_document_uniqueness(
    db: Session,
    title: str,
    doc_code: Optional[str] = None,
    era: Optional[str] = None,
    source_type: Optional[str] = None,
    file_size_bytes: Optional[int] = None,
) -> Dict[str, Any]:
    normalized_title = (title or '').strip().lower()
    title_hash = compute_title_hash_sha256(
        era, source_type, None, None, doc_code, normalized_title,
    )

    hash_query = db.query(Document)
    if file_size_bytes is not None:
        lower = int(file_size_bytes * 0.995)
        upper = int(file_size_bytes * 1.005)
        hash_query = hash_query.filter(
            Document.file_size_bytes.isnot(None),
            Document.file_size_bytes >= lower,
            Document.file_size_bytes <= upper,
        )

    hash_matches = hash_query.filter(Document.title_hash_sha256 == title_hash).all()
    code_matches: List[Document] = []
    if doc_code and era:
        code_matches = db.query(Document).filter(
            Document.doc_code == doc_code,
            Document.era == era,
        ).all()

    seen_ids = set()
    candidates: List[Dict[str, Any]] = []
    duplicate_statuses = {'registry', 'indexed', 'approved', 'processing'}

    for document in hash_matches + code_matches:
        if document.id in seen_ids:
            continue
        seen_ids.add(document.id)
        similarity = 1.0 if document.title_hash_sha256 == title_hash else 0.9
        candidates.append({
            'document_id': str(document.id),
            'title': document.title,
            'doc_code': document.doc_code,
            'similarity': similarity,
            'status': document.status,
            'file_size_bytes': document.file_size_bytes,
        })

    is_duplicate = any(c.get('status') in duplicate_statuses for c in candidates)

    return {
        'is_duplicate': is_duplicate,
        'is_duplicate_file': False,
        'candidates': candidates,
        'file_hash_sha256': None,
        'title_hash_sha256': title_hash,
        'file_size_bytes': file_size_bytes,
        'checked_at': datetime.now(timezone.utc).isoformat(),
    }


def get_document_history(db: Session, document_id: str) -> List[DocumentHistory]:
    try:
        document_int = int(str(document_id))
    except (ValueError, TypeError):
        return []
    return (
        db.query(DocumentHistory)
        .filter(DocumentHistory.document_id == document_int)
        .order_by(DocumentHistory.event_at.asc())
        .all()
    )


def _succession_entry(document: Document, relation: str, depth: int) -> Dict[str, Any]:
    return {
        'id': document.id,
        'title': document.title,
        'doc_code': document.doc_code,
        'era': document.era,
        'relation': relation,
        'depth': depth,
    }


def get_document_succession(db: Session, document: Document) -> Dict[str, Any]:
    chain: List[Dict[str, Any]] = []

    predecessors: List[Document] = []
    current: Optional[Document] = document
    while current and current.predecessor_doc_id:
        parent = db.query(Document).filter(Document.id == current.predecessor_doc_id).first()
        if not parent:
            break
        predecessors.insert(0, parent)
        current = parent

    for index, pred in enumerate(predecessors):
        depth = index - len(predecessors)
        chain.append(_succession_entry(pred, 'predecessor', depth))

    chain.append(_succession_entry(document, 'self', 0))

    current = document
    depth = 1
    while current and current.successor_doc_id:
        successor = db.query(Document).filter(Document.id == current.successor_doc_id).first()
        if not successor:
            break
        chain.append(_succession_entry(successor, 'successor', depth))
        depth += 1
        current = successor

    return {
        'document_id': document.id,
        'title': document.title,
        'chain': chain,
    }


def _section_to_rag(section: DocumentSection) -> Dict[str, Any]:
    return {
        'section_id': section.id,
        'document_id': section.document_id,
        'parent_id': section.parent_id,
        'clause': section.clause,
        'title': section.title,
        'level': section.level,
        'path': str(section.path) if section.path is not None else None,
        'page': section.page,
        'type': section.type_,
        'content': section.content,
        'created_at': section.created_at.isoformat() if section.created_at else None,
    }


def _reference_to_rag(reference: DocumentReference) -> Dict[str, Any]:
    return {
        'id': reference.id,
        'source_document_id': reference.source_document_id,
        'target_doc_code': reference.target_doc_code,
        'reference_type': reference.reference_type,
        'context': reference.context,
        'current_status': reference.current_status,
        'replaced_by': reference.replaced_by,
        'replacement_date': reference.replacement_date.isoformat() if reference.replacement_date else None,
        'is_resolved': reference.is_resolved,
        'resolved_document_id': reference.resolved_document_id,
        'created_at': reference.created_at.isoformat() if reference.created_at else None,
    }


def get_document_sections_bundle(db: Session, document: Document) -> Dict[str, Any]:
    populate_document_extra_fields(db, [document])
    document_uuid = document.id
    sections = (
        db.query(DocumentSection)
        .filter(DocumentSection.document_id == document_uuid)
        .order_by(DocumentSection.id.asc())
        .all()
    )
    references = (
        db.query(DocumentReference)
        .filter(DocumentReference.source_document_id == document_uuid)
        .order_by(DocumentReference.created_at.asc())
        .all()
    )

    from api.v1.models import Terminology
    from sqlalchemy import cast, Text, or_
    doc_code = document.doc_code
    terms_query = db.query(Terminology)
    conds = [cast(Terminology.related_docs, Text).ilike(f'%"{doc_code}"%')]
    if db.bind.dialect.name == "postgresql":
        conds.append(Terminology.related_docs.has_key(doc_code))
    related_terms = terms_query.filter(or_(*conds)).all()

    terminology_payload = [
        {
            'term': term.standard_term,
            'definition': term.definition,
            'source_clause': None,
            'normalized_term': term.normalized_value,
        }
        for term in related_terms
    ]

    document_payload = {
        'id': document.id,
        'doc_code': document.doc_code,
        'title': document.title,
        'normalized_title': document.normalized_title,
        'source_type': document.source_type,
        'group': document.group_,
        'era': document.era,
        'validity_status': document.validity_status,
        'status': document.status,
        'jurisdiction': document.jurisdiction,
        'issuing_body': document.issuing_body,
        'mks_oks_code': document.mks_oks_code,
        'okstu_code': document.okstu_code,
        'mks_name': document.mks_name,
        'okstu_name': document.okstu_name,
        'total_versions': document.total_versions,
        'udk_code': document.udk_code,
        'successor_doc_id': document.successor_doc_id,
        'predecessor_doc_id': document.predecessor_doc_id,
        'created_at': document.created_at.isoformat() if document.created_at else None,
        'updated_at': document.updated_at.isoformat() if document.updated_at else None,
    }

    return {
        'document': document_payload,
        'sections': [_section_to_rag(section) for section in sections],
        'terminology': terminology_payload,
        'references': [_reference_to_rag(reference) for reference in references],
    }


def parse_history_comment(comment: Optional[str]) -> Any:
    if not comment:
        return None
    try:
        return json.loads(comment)
    except (json.JSONDecodeError, TypeError):
        return comment


def create_pipeline_document(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    doc_data = payload.get('document', {})
    metadata = doc_data.get('metadata', {})
    
    title = metadata.get('title')
    doc_code = metadata.get('doc_code')
    if not title or not doc_code:
        raise ValueError("title and doc_code are required in document metadata")
        
    title_hash = metadata.get('title_hash_sha256')
    if not title_hash:
        title_hash = compute_title_hash_sha256(
            metadata.get('era'),
            metadata.get('source_type'),
            metadata.get('mks_oks_code'),
            metadata.get('okstu_code'),
            doc_code,
            metadata.get('normalized_title') or (title or '').strip().lower()
        )
        
    # Check if duplicate document already exists
    existing = db.query(Document).filter(Document.title_hash_sha256 == title_hash).first()
    if existing:
        raise ValueError("DUPLICATE_DOCUMENT")
        
    # Create the Document
    doc_kwargs = {
        'normalized_title': metadata.get('normalized_title'),
        'source_type': metadata.get('source_type'),
        'group_': metadata.get('group'),
        'mks_oks_code': metadata.get('mks_oks_code'),
        'okstu_code': metadata.get('okstu_code'),
        'udk_code': metadata.get('udc'),
        'era': metadata.get('era'),
        'validity_status': metadata.get('validity_status'),
        'status': metadata.get('status', 'uploaded'),
        'jurisdiction': metadata.get('jurisdiction'),
        'issuing_body': metadata.get('issuing_body'),
        'file_hash_sha256': doc_data.get('source', {}).get('file_hash_sha256') if doc_data.get('source') else None,
        'title_hash_sha256': title_hash,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }
    
    doc = create_document(db, doc_code=doc_code, title=title, **doc_kwargs)
    
    # Save physical version
    source_data = doc_data.get('source', {})
    if source_data:
        from api.v1.models import DocumentVersion
        db_ver = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            file_hash_sha256=source_data.get('file_hash_sha256'),
            file_size_bytes=source_data.get('page_count') or 0,
            file_key=source_data.get('file_name'),
            created_at=datetime.now(timezone.utc)
        )
        db.add(db_ver)
        db.flush()
    
    # Save content sections
    content_list = doc_data.get('content', [])
    sections_response = []
    
    for idx, sec in enumerate(content_list):
        db_sec = DocumentSection(
            document_id=doc.id,
            clause=sec.get('clause'),
            title=sec.get('title'),
            level=sec.get('level'),
            path=sec.get('path'),
            page=sec.get('page'),
            bbox=sec.get('bbox'),
            type_=sec.get('type'),
            content=sec.get('content'),
            created_at=datetime.now(timezone.utc)
        )
        db.add(db_sec)
        db.flush()
        
        sections_response.append({
            "section_id": db_sec.id,
            "type": db_sec.type_,
            "clause": db_sec.clause,
            "path": db_sec.path,
            "page": db_sec.page
        })
        
    # Save terminology
    terminology_list = doc_data.get('terminology', [])
    for term in terminology_list:
        raw_t = term.get('term')
        norm_t = term.get('normalized_term')
        definition = term.get('definition')
        if raw_t:
            from api.v1.crud.terminology import get_terminology_by_raw_term, create_terminology
            existing_t = get_terminology_by_raw_term(db, raw_t)
            if not existing_t:
                create_terminology(
                    db,
                    raw_term=raw_t,
                    standard_term=raw_t,
                    normalized_value=norm_t or raw_t.lower(),
                    term_type='term',
                    definition=definition,
                    related_docs=[doc.doc_code]
                )
            else:
                current_docs = list(existing_t.related_docs or [])
                if doc.doc_code not in current_docs:
                    current_docs.append(doc.doc_code)
                    existing_t.related_docs = current_docs
                    db.flush()
                
    # Save references
    references_list = doc_data.get('references', [])
    for ref in references_list:
        db_ref = DocumentReference(
            source_document_id=doc.id,
            target_doc_code=ref.get('target_doc_code'),
            reference_type=ref.get('type'),
            context=ref.get('context'),
            current_status=ref.get('current_status'),
            replaced_by=ref.get('replaced_by'),
            is_resolved=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(db_ref)
        
    db.commit()
    
    return {
        "document_id": doc.id,
        "version_id": f"v1-{doc.id}",
        "sections": sections_response,
        "registry": {
            "document_id": doc.id,
            "version_id": f"v1-{doc.id}",
            "sections_count": len(sections_response),
            "references_count": len(references_list),
            "created_at": doc.created_at.isoformat() if doc.created_at else datetime.now(timezone.utc).isoformat()
        }
    }


def update_document_status(
    db: Session,
    document_id: str,
    status: str,
    comment: Optional[str] = None,
    changed_by: Optional[str] = None,
) -> Optional[tuple[Document, DocumentHistory, Optional[str]]]:
    document = get_document_by_id(db, document_id)
    if not document:
        return None

    old_status = document.status

    VALID_STATUSES = {
        'draft', 'uploaded', 'validating', 'processing', 'review_required',
        'ready_for_promotion', 'approved', 'failed', 'archived'
    }

    if status not in VALID_STATUSES:
        raise ValueError("INVALID_STATUS")

    VALID_TRANSITIONS = {
        None: {'draft', 'uploaded', 'validating', 'processing', 'review_required', 'ready_for_promotion', 'approved', 'failed', 'archived'},
        'draft': {'uploaded', 'failed', 'archived'},
        'uploaded': {'validating', 'failed', 'archived'},
        'validating': {'processing', 'review_required', 'ready_for_promotion', 'failed', 'archived'},
        'processing': {'validating', 'review_required', 'ready_for_promotion', 'approved', 'failed', 'archived'},
        'review_required': {'approved', 'validating', 'failed', 'archived'},
        'ready_for_promotion': {'approved', 'failed', 'archived'},
        'approved': {'archived', 'failed'},
        'failed': {'uploaded', 'draft', 'archived'},
        'archived': {'draft', 'uploaded'}
    }

    allowed = VALID_TRANSITIONS.get(old_status, set())
    if status not in allowed:
        raise ValueError("INVALID_TRANSITION")

    document.status = status
    document.updated_at = datetime.now(timezone.utc)
    if changed_by:
        document.updated_by = changed_by

    comment_json = None
    if comment:
        comment_json = json.dumps({"reason": comment})

    history = DocumentHistory(
        document_id=document.id,
        event_type="status_change",
        old_status=old_status,
        new_status=status,
        comment=comment_json,
        changed_by=changed_by,
        event_at=datetime.now(timezone.utc)
    )
    db.add(history)
    db.commit()
    db.refresh(document)
    populate_document_extra_fields(db, [document])
    db.refresh(history)

    return document, history, old_status


def check_and_quarantine_classifiers(db: Session, document: Document):
    """Check classification codes on the document and add them to pending quarantine if missing."""
    from api.v1.crud.classifier import get_classifier, create_classifier_pending
    from api.v1.models import ClassifierPending

    # 1. Check mks_oks_code
    if document.mks_oks_code:
        exists = get_classifier(db, 'MKS', document.mks_oks_code)
        if not exists:
            already_pending = db.query(ClassifierPending).filter(
                ClassifierPending.system == 'MKS',
                ClassifierPending.code == document.mks_oks_code
            ).first()
            if not already_pending:
                create_classifier_pending(db, system='MKS', code=document.mks_oks_code, found_in_document_id=str(document.id))

    # 2. Check okstu_code
    if document.okstu_code:
        exists = get_classifier(db, 'OKSTU', document.okstu_code)
        if not exists:
            already_pending = db.query(ClassifierPending).filter(
                ClassifierPending.system == 'OKSTU',
                ClassifierPending.code == document.okstu_code
            ).first()
            if not already_pending:
                create_classifier_pending(db, system='OKSTU', code=document.okstu_code, found_in_document_id=str(document.id))

    # 3. Check udk_code
    if document.udk_code:
        exists = get_classifier(db, 'UDC', document.udk_code)
        if not exists:
            already_pending = db.query(ClassifierPending).filter(
                ClassifierPending.system == 'UDC',
                ClassifierPending.code == document.udk_code
            ).first()
            if not already_pending:
                create_classifier_pending(db, system='UDC', code=document.udk_code, found_in_document_id=str(document.id))



