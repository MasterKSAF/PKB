import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.v1.models import Document, DocumentHistory, DocumentReference, DocumentSection

_UUID_FIELDS = ('successor_doc_id', 'predecessor_doc_id')


def _coerce_uuid_fields(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    for key in _UUID_FIELDS:
        value = kwargs.get(key)
        if value is not None:
            kwargs[key] = uuid.UUID(str(value))
    return kwargs


def get_documents(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    doc_code: Optional[str] = None,
    title: Optional[str] = None,
    status: Optional[str] = None,
    mks_oks_code: Optional[str] = None,
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

    total = query.count()
    
    skip = (page - 1) * page_size
    documents = query.order_by(desc(Document.created_at)).offset(skip).limit(page_size).all()
    
    return documents, total


def get_document_by_id(db: Session, document_id: str) -> Optional[Document]:
    """Retrieve a single document by ID."""
    try:
        document_uuid = uuid.UUID(str(document_id))
    except (ValueError, TypeError):
        return None
    return db.query(Document).filter(Document.id == document_uuid).first()


def create_document(db: Session, doc_code: str, title: str, **kwargs) -> Document:
    """Create a new document."""
    document = Document(
        doc_code=doc_code,
        title=title,
        **_coerce_uuid_fields(kwargs),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def update_document(db: Session, document_id: str, **kwargs) -> Optional[Document]:
    """Update a document."""
    document = get_document_by_id(db, document_id)
    if not document:
        return None
    
    for key, value in _coerce_uuid_fields(kwargs).items():
        if value is not None and hasattr(document, key):
            setattr(document, key, value)
    
    db.commit()
    db.refresh(document)
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
    document_uuid = uuid.UUID(str(document_id))
    return (
        db.query(DocumentHistory)
        .filter(DocumentHistory.document_id == document_uuid)
        .order_by(DocumentHistory.event_at.asc())
        .all()
    )


def _succession_entry(document: Document, relation: str, depth: int) -> Dict[str, Any]:
    return {
        'id': str(document.id),
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
        'document_id': str(document.id),
        'title': document.title,
        'chain': chain,
    }


def _section_to_rag(section: DocumentSection) -> Dict[str, Any]:
    return {
        'section_id': section.id,
        'document_id': str(section.document_id),
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
        'id': str(reference.id),
        'source_document_id': str(reference.source_document_id),
        'target_doc_code': reference.target_doc_code,
        'reference_type': reference.reference_type,
        'context': reference.context,
        'current_status': reference.current_status,
        'replaced_by': reference.replaced_by,
        'replacement_date': reference.replacement_date.isoformat() if reference.replacement_date else None,
        'is_resolved': reference.is_resolved,
        'resolved_document_id': str(reference.resolved_document_id) if reference.resolved_document_id else None,
        'created_at': reference.created_at.isoformat() if reference.created_at else None,
    }


def get_document_sections_bundle(db: Session, document: Document) -> Dict[str, Any]:
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

    document_payload = {
        'id': str(document.id),
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
        'udc': document.udc,
        'successor_doc_id': str(document.successor_doc_id) if document.successor_doc_id else None,
        'predecessor_doc_id': str(document.predecessor_doc_id) if document.predecessor_doc_id else None,
        'created_at': document.created_at.isoformat() if document.created_at else None,
        'updated_at': document.updated_at.isoformat() if document.updated_at else None,
    }

    return {
        'document': document_payload,
        'sections': [_section_to_rag(section) for section in sections],
        'terminology': [],
        'references': [_reference_to_rag(reference) for reference in references],
    }


def parse_history_comment(comment: Optional[str]) -> Any:
    if not comment:
        return None
    try:
        return json.loads(comment)
    except (json.JSONDecodeError, TypeError):
        return comment
