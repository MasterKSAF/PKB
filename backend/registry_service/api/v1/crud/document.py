import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.v1.models import Document, DocumentHistory, DocumentReference, DocumentSection
from api.v1.models.draft import Draft

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
    first_version_files = {}
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

        # Batch query source_filename from first version of each document
        from sqlalchemy import func, select
        min_version_subq = db.query(
            func.min(DocumentVersion.id).label('min_id')
        ).filter(
            DocumentVersion.document_id.in_(doc_ids),
            DocumentVersion.source_filename.isnot(None),
            DocumentVersion.source_filename != ''
        ).group_by(
            DocumentVersion.document_id
        ).subquery()
        file_rows = db.query(
            DocumentVersion.document_id,
            DocumentVersion.source_filename
        ).filter(
            DocumentVersion.id.in_(select(min_version_subq.c.min_id))
        ).all()
        first_version_files = {r.document_id: r.source_filename for r in file_rows}

    for doc in documents:
        doc.mks_name = mks_names.get(doc.mks_oks_code) if doc.mks_oks_code else None
        doc.okstu_name = okstu_names.get(doc.okstu_code) if doc.okstu_code else None
        doc.total_versions = version_counts.get(doc.id, 0)
        doc.file_name = first_version_files.get(doc.id)


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


def create_document(db: Session, doc_code: str, title: str, commit: bool = True, **kwargs) -> Document:
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
    if commit:
        db.commit()
        db.refresh(document)
    else:
        db.flush()

    # Issue 2.3: Link document with file and create document version if draft_id is set
    if document.draft_id:
        from api.v1.models import Draft, File, DocumentVersion
        draft = db.query(Draft).filter(Draft.draft_id == document.draft_id).first()
        if draft and draft.file_key:
            filename = draft.original_filename
            file_size = 0
            file_hash = None
            
            if draft.raw_data and isinstance(draft.raw_data, dict):
                source = draft.raw_data.get('document', {}).get('source', {})
                filename = filename or source.get('file_name')
                file_size = source.get('file_size_bytes') or source.get('page_count') or 0
                file_hash = source.get('file_hash_sha256')
                
            if not filename:
                filename = draft.file_key or f"doc_{document.id}.pdf"
                
            # Create or update File record
            file_rec = db.query(File).filter(File.file_id == draft.file_key).first()
            if file_rec:
                file_rec.related_document_id = str(document.id)
            else:
                file_rec = File(
                    file_id=draft.file_key,
                    filename=filename,
                    size=file_size,
                    mime_type="application/pdf",
                    url=f"/files/{draft.file_key}",
                    uploaded_at=draft.created_at or datetime.now(timezone.utc),
                    storage_path=draft.file_key,
                    related_document_id=str(document.id)
                )
                db.add(file_rec)
                
            # Create DocumentVersion if it doesn't exist
            existing_ver = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document.id,
                DocumentVersion.version_number == 1
            ).first()
            if not existing_ver:
                db_ver = DocumentVersion(
                    document_id=document.id,
                    version_number=1,
                    file_hash_sha256=file_hash,
                    file_size_bytes=file_size,
                    file_key=draft.file_key,
                    source_filename=filename,
                    file_path=draft.file_key,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(db_ver)

            # Create DocumentSection records for OCR flat blocks (Issue 2.2)
            if draft.raw_data and isinstance(draft.raw_data, dict):
                blocks = draft.raw_data.get('document', {}).get('block', [])
                if blocks:
                    from api.v1.models import DocumentSection
                    # Only insert flat blocks if no sections currently exist to avoid duplication
                    existing_sec = db.query(DocumentSection).filter(DocumentSection.document_id == document.id).first()
                    if not existing_sec:
                        for block in blocks:
                            db_sec = DocumentSection(
                                document_id=document.id,
                                clause=None,
                                title=None,
                                level=None,
                                path=None,
                                page=block.get('page'),
                                bbox=block.get('bbox'),
                                type_=block.get('type'),
                                content={"text": block.get('content') or ""},
                                created_at=datetime.now(timezone.utc)
                            )
                            db.add(db_sec)
            
            if commit:
                db.commit()
                db.refresh(document)
            else:
                db.flush()

    populate_document_extra_fields(db, [document])
    check_and_quarantine_classifiers(db, document, commit=commit)
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
    file_hash_sha256: Optional[str] = None,
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

    # Проверяем Drafts с таким же document_key (file_hash)
    # Активные черновики (в обработке) — блокируем 409
    draft_in_progress = None
    existing_draft_id = None
    existing_document_id = None
    if file_hash_sha256:
        active_statuses = ('uploaded', 'previewing', 'ready_for_approve', 'validation')
        draft_in_progress = db.query(Draft).filter(
            Draft.document_key == file_hash_sha256,
            Draft.status.in_(active_statuses),
        ).first()
        if draft_in_progress:
            existing_draft_id = draft_in_progress.draft_id

        # Проверяем терминальные черновики (уже принят/discarded)
        # и Documents с таким же file_hash_sha256
        if not draft_in_progress:
            existing_doc_by_hash = db.query(Document).filter(
                Document.file_hash_sha256 == file_hash_sha256,
            ).first()
            if existing_doc_by_hash:
                existing_document_id = existing_doc_by_hash.id
            else:
                # Fallback: проверяем черновики с терминальным статусом
                terminal_draft = db.query(Draft).filter(
                    Draft.document_key == file_hash_sha256,
                    Draft.status.in_(('approved', 'discarded', 'failed')),
                    Draft.registry_document_id.isnot(None),
                ).first()
                if terminal_draft:
                    existing_document_id = terminal_draft.registry_document_id

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
    is_duplicate_file = draft_in_progress is not None
    is_duplicate_document = existing_document_id is not None

    return {
        'is_duplicate': is_duplicate,
        'is_duplicate_file': is_duplicate_file,
        'is_duplicate_document': is_duplicate_document,
        'existing_draft_id': existing_draft_id,
        'existing_document_id': existing_document_id,
        'candidates': candidates,
        'file_hash_sha256': file_hash_sha256,
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
    
    content_list = doc_data.get('content') or doc_data.get('sections') or []
    references_list = doc_data.get('references', [])

    # ─── UPSERT: если передан document_id — обновляем существующий документ ───
    existing_doc_id = payload.get('document_id')
    if existing_doc_id:
        doc = db.query(Document).filter(Document.id == existing_doc_id).first()
        if doc:
            # Обновляем поля документа (только если переданы)
            if title:
                doc.title = title
            if doc_code:
                doc.doc_code = doc_code
            if metadata.get('normalized_title'):
                doc.normalized_title = metadata['normalized_title']
            if metadata.get('source_type'):
                doc.source_type = metadata['source_type']
            if metadata.get('era'):
                doc.era = metadata['era']
            if metadata.get('jurisdiction'):
                doc.jurisdiction = metadata['jurisdiction']
            if metadata.get('issuing_body'):
                doc.issuing_body = metadata['issuing_body']
            if metadata.get('validity_status'):
                doc.validity_status = metadata['validity_status']
            if metadata.get('status'):
                doc.status = metadata['status']
            # Обновляем doc_metadata: сохраняем существующее, мержим новое quality
            existing_meta = dict(doc.doc_metadata or {})
            if 'quality' in metadata:
                existing_meta['quality'] = metadata['quality']
            doc.doc_metadata = existing_meta
            doc.updated_at = datetime.now(timezone.utc)
            db.flush()

            # ...
            # Удаляем старые sections только если есть новые на замену
            if content_list:
                db.query(DocumentSection).filter(
                    DocumentSection.document_id == doc.id
                ).delete()
                db.flush()

            # ...
            # Удаляем старые references только если есть новые
            if references_list:
                db.query(DocumentReference).filter(
                    DocumentReference.source_document_id == doc.id
                ).delete()
                db.flush()

            new_document_created = False
        else:
            new_document_created = True
    else:
        new_document_created = True

    # ─── CREATE: если upsert не сработал, создаём новый документ ───
    if new_document_created:
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
            
        # Check if duplicate document already exists (by title_hash)
        existing = db.query(Document).filter(Document.title_hash_sha256 == title_hash).first()
        if existing:
            raise ValueError("DUPLICATE_DOCUMENT")
            
        # Check if duplicate by file_hash_sha256 (if hash is non-empty)
        file_hash_raw = doc_data.get('source', {}).get('file_hash_sha256') if doc_data.get('source') else None
        if file_hash_raw and file_hash_raw.strip():
            existing_file = db.query(Document).filter(Document.file_hash_sha256 == file_hash_raw.strip()).first()
            if existing_file:
                raise ValueError("DUPLICATE_DOCUMENT")
            
        doc_kwargs = {
            'normalized_title': metadata.get('normalized_title'),
            'source_type': metadata.get('source_type'),
            'group_': metadata.get('group'),
            'mks_oks_code': metadata.get('mks_oks_code'),
            'draft_id': payload.get('draft_id') or payload.get('source_draft_id') or metadata.get('draft_id') or doc_data.get('draft_id'),
            'okstu_code': metadata.get('okstu_code'),
            'udk_code': metadata.get('udc'),
            'era': metadata.get('era'),
            'validity_status': metadata.get('validity_status'),
            'status': metadata.get('status', 'uploaded'),
            'jurisdiction': metadata.get('jurisdiction'),
            'issuing_body': metadata.get('issuing_body'),
            'file_hash_sha256': file_hash_raw.strip() if file_hash_raw and file_hash_raw.strip() else None,
            'title_hash_sha256': title_hash,
            'title_key': metadata.get('title_key'),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
        }
        # Сохраняем весь metadata (включая quality) в doc_metadata JSONB
        if metadata:
            doc_kwargs['metadata'] = dict(metadata)
        
        doc = create_document(db, doc_code=doc_code, title=title, commit=False, **doc_kwargs)
        
        # Save physical version
        source_data = doc_data.get('source', {})
        if source_data:
            from api.v1.models import DocumentVersion
            existing_ver = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == doc.id,
                DocumentVersion.version_number == 1
            ).first()
            if not existing_ver:
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

    # ─── Save content sections (общие для upsert и create) ───
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
                try:
                    with db.begin_nested():
                        existing_t = create_terminology(
                            db,
                            raw_term=raw_t,
                            standard_term=raw_t,
                            normalized_value=norm_t or raw_t.lower(),
                            term_type='term',
                            definition=definition,
                            related_docs=[doc.doc_code],
                            commit=False
                        )
                except Exception:
                    existing_t = get_terminology_by_raw_term(db, raw_t)
            
            if existing_t:
                current_docs = list(existing_t.related_docs or [])
                if doc.doc_code not in current_docs:
                    current_docs.append(doc.doc_code)
                    existing_t.related_docs = current_docs
                    db.flush()
                
    # Save references
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


def check_and_quarantine_classifiers(db: Session, document: Document, commit: bool = True):
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
                try:
                    with db.begin_nested():
                        create_classifier_pending(db, system='MKS', code=document.mks_oks_code, found_in_document_id=str(document.id), commit=commit)
                except Exception:
                    pass

    # 2. Check okstu_code
    if document.okstu_code:
        exists = get_classifier(db, 'OKSTU', document.okstu_code)
        if not exists:
            already_pending = db.query(ClassifierPending).filter(
                ClassifierPending.system == 'OKSTU',
                ClassifierPending.code == document.okstu_code
            ).first()
            if not already_pending:
                try:
                    with db.begin_nested():
                        create_classifier_pending(db, system='OKSTU', code=document.okstu_code, found_in_document_id=str(document.id), commit=commit)
                except Exception:
                    pass

    # 3. Check udk_code
    if document.udk_code:
        exists = get_classifier(db, 'UDC', document.udk_code)
        if not exists:
            already_pending = db.query(ClassifierPending).filter(
                ClassifierPending.system == 'UDC',
                ClassifierPending.code == document.udk_code
            ).first()
            if not already_pending:
                try:
                    with db.begin_nested():
                        create_classifier_pending(db, system='UDC', code=document.udk_code, found_in_document_id=str(document.id), commit=commit)
                except Exception:
                    pass


def get_document_parameters(db: Session, document_id: int) -> List[Dict[str, Any]]:
    """Retrieve all parameters (formulas) extracted from document sections."""
    sections = (
        db.query(DocumentSection)
        .filter(DocumentSection.document_id == document_id, DocumentSection.type_ == 'formula')
        .order_by(DocumentSection.id.asc())
        .all()
    )
    parameters = []
    for sec in sections:
        if isinstance(sec.content, dict) and 'parameters' in sec.content:
            sec_params = sec.content['parameters']
            if isinstance(sec_params, list):
                for p in sec_params:
                    if isinstance(p, dict):
                        param_copy = dict(p)
                        param_copy['source_clause'] = sec.clause
                        param_copy['source_page'] = sec.page
                        parameters.append(param_copy)
    return parameters


def get_document_pages_count(db: Session, document_id: int) -> int:
    """Retrieve total count of pages in a document."""
    from sqlalchemy import func
    from api.v1.models import DocumentVersion

    max_page = db.query(func.max(DocumentSection.page)).filter(DocumentSection.document_id == document_id).scalar() or 0
    version = db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).order_by(DocumentVersion.version_number.desc()).first()
    pages_total = max(max_page, version.file_size_bytes if (version and version.file_size_bytes) else 0)
    return max(pages_total, 1)


def get_page_blocks(db: Session, document_id: int, page_num: int) -> List[Dict[str, Any]]:
    """Retrieve and map document sections on a specific page as blocks."""
    sections = (
        db.query(DocumentSection)
        .filter(DocumentSection.document_id == document_id, DocumentSection.page == page_num)
        .order_by(DocumentSection.id.asc())
        .all()
    )
    blocks = []
    for idx, sec in enumerate(sections, 1):
        if isinstance(sec.content, dict):
            text_content = render_section_content_to_md(sec.type_, sec.content)
        else:
            text_content = str(sec.content or "")

        blocks.append({
            "number": idx,
            "type": sec.type_,
            "bbox": sec.bbox,
            "content": text_content,
            "confidence": 0.95
        })
    return blocks


def render_section_content_to_md(sec_type: str, content: Any) -> str:
    """Helper to render a document section's JSON content to markdown.
    Handles fallback GFM table construction, lists, images, and formulas dynamically.
    """
    if not isinstance(content, dict):
        return str(content or "")
        
    if sec_type == "text":
        return content.get("markdown") or content.get("text") or ""
    elif sec_type == "textBlock":
        block = content.get("block") or []
        return "\n\n".join(block)
    elif sec_type == "headerFooter":
        return content.get("text") or ""
    elif sec_type == "table":
        #
        # TABLE
        #
        # if "markdown" in content and content["markdown"]:
        #     return content["markdown"]
        # if not content.get("columns") and not content.get("rows"):
        #     return content.get("text") or content.get("markdown") or ""

        """
        Parsing table data
        """

        row_data, data_rows = [], []
        raw_rows = content.get("rows")

        for i in range(0, len(raw_rows)):
            row = raw_rows[i]
            if row.get("type", "") == "table row":
                for k in range(0, len(row["cells"])):
                    cell_block = row["cells"][k].get("block") or row["cells"][k].get("kids") or []
                    cells_text = cell_block[0]["content"] if cell_block else ""
                    row_data.append(cells_text)
            data_rows.append(row_data)
            row_data = []
        rows = data_rows


        caption = content.get("caption") or ""
        # rows = content.get("rows") or []
        columns = content.get("columns") or []      # column headers

        footnotes = content.get("footnotes") or []
        image_key = content.get("image_key")
        
        col_count = len(columns)
        if rows:
            col_count = max(col_count, max(len(row) for row in rows))
        if col_count == 0:
            col_count = 1
        
        padded_columns = list(columns)
        while len(padded_columns) < col_count:
            padded_columns.append("")
        
        tbl_parts = []
        if caption:
            tbl_parts.append(caption)
        
        header_line = "| " + " | ".join(padded_columns) + " |"
        delimiters = "| " + " | ".join([":---"] * col_count) + " |"
        tbl_parts.append(header_line)
        tbl_parts.append(delimiters)
        
        for row in rows:
            padded_row = list(row)
            while len(padded_row) < col_count:
                padded_row.append(None)
            row_str = "| " + " | ".join([str(val) if val is not None else " " for val in padded_row]) + " |"
            tbl_parts.append(row_str)
            
        for fn in footnotes:
            tbl_parts.append(f"\\* {fn}")
            
        tbl_md = "\n".join(tbl_parts)
        if image_key:
            tbl_md += f"\n\n![{caption or 'table'}](/api/v1/files/{image_key})"
        return tbl_md

        # EOF TABLE

    elif sec_type == "list":
        items = content.get("items") or []
        return "\n".join([f"* {item}" for item in items])
    elif sec_type == "image":
        caption = content.get("caption") or ""
        image_key = content.get("image_key") or ""
        description = content.get("description") or ""
        img_parts = []
        if image_key:
            img_parts.append(f"![{caption}](/api/v1/files/{image_key})")
        if caption or description:
            sep = " — " if (caption and description) else ""
            img_parts.append(f"*{caption}{sep}{description}*")
        return "\n".join(img_parts)
    elif sec_type == "formula":
        latex = content.get("latex") or ""
        meaning = content.get("meaning") or ""
        image_key = content.get("image_key")
        f_parts = []
        if latex:
            f_parts.append(f"$${latex}$$")
        if meaning:
            f_parts.append(f"*Физический смысл: {meaning}*")
        f_md = "\n".join(f_parts)
        if image_key:
            f_md += f"\n\n![Формула: {latex}](/api/v1/files/{image_key})"
        return f_md
    else:
        return str(content)


def get_page_blocks_md(db: Session, document_id: int, page_num: int) -> List[Dict[str, Any]]:
    """Retrieve and map document sections on a specific page as blocks with Markdown content."""
    sections = (
        db.query(DocumentSection)
        .filter(DocumentSection.document_id == document_id, DocumentSection.page == page_num)
        .order_by(DocumentSection.id.asc())
        .all()
    )
    blocks = []
    for idx, sec in enumerate(sections, 1):
        md_content = render_section_content_to_md(sec.type_, sec.content)
        blocks.append({
            "number": idx,
            "id": sec.id,
            "section_id": sec.id,
            "parent_id": sec.parent_id,
            "clause": sec.clause,
            "title": sec.title,
            "level": sec.level,
            "path": str(sec.path) if sec.path is not None else None,
            "type": sec.type_,
            "bbox": sec.bbox,
            "content": md_content,
            "confidence": 0
        })
    return blocks


def convert_markdown_to_html(md: str, type_: str = None) -> str:
    """Helper to convert a markdown string (especially tables) into simple HTML."""
    if not md:
        return ""
    lines = [line.strip() for line in md.strip().split("\n")]
    if type_ == "table" or (len(lines) >= 3 and any("|" in l for l in lines)):
        html_lines = ["<table>"]
        has_tbody = False
        for i, line in enumerate(lines):
            if not line.strip() or (i == 1 and all(c in "-:| \t" for c in line if c != "|")):
                continue
            cells = [cell.strip() for cell in line.split("|")]
            if line.startswith("|"):
                cells = cells[1:]
            if line.endswith("|"):
                cells = cells[:-1]
            if not cells:
                continue
            
            if i == 0:
                html_lines.append("  <thead>")
                html_lines.append("    <tr>")
                for cell in cells:
                    html_lines.append(f"      <th>{cell}</th>")
                html_lines.append("    </tr>")
                html_lines.append("  </thead>")
            else:
                if not has_tbody:
                    html_lines.append("  <tbody>")
                    has_tbody = True
                html_lines.append("    <tr>")
                for cell in cells:
                    html_lines.append(f"      <td>{cell}</td>")
                html_lines.append("    </tr>")
        if has_tbody:
            html_lines.append("  </tbody>")
        html_lines.append("</table>")
        return "\n".join(html_lines)
    
    if md.strip().startswith("<") and md.strip().endswith(">"):
        return md
    return f"<p>{md}</p>"


def get_page_blocks_html(db: Session, document_id: int, page_num: int) -> List[Dict[str, Any]]:
    """Retrieve and map document sections on a specific page as blocks with HTML content."""
    sections = (
        db.query(DocumentSection)
        .filter(DocumentSection.document_id == document_id, DocumentSection.page == page_num)
        .order_by(DocumentSection.id.asc())
        .all()
    )
    blocks = []
    for idx, sec in enumerate(sections, 1):
        html_content = ""
        if isinstance(sec.content, dict):
            if "html" in sec.content and sec.content["html"]:
                html_content = sec.content["html"]
            else:
                raw_markdown = render_section_content_to_md(sec.type_, sec.content)
                html_content = convert_markdown_to_html(raw_markdown, sec.type_)
        else:
            html_content = convert_markdown_to_html(str(sec.content or ""), sec.type_)

        blocks.append({
            "number": idx,
            "id": sec.id,
            "section_id": sec.id,
            "parent_id": sec.parent_id,
            "clause": sec.clause,
            "title": sec.title,
            "level": sec.level,
            "path": str(sec.path) if sec.path is not None else None,
            "type": sec.type_,
            "bbox": sec.bbox,
            "content": html_content,
            "confidence": 0
        })
    return blocks


def get_page_blocks_raw(db: Session, document_id: int, page_num: int) -> List[Dict[str, Any]]:
    """Retrieve and map document sections on a specific page as blocks with raw JSONB content."""
    sections = (
        db.query(DocumentSection)
        .filter(DocumentSection.document_id == document_id, DocumentSection.page == page_num)
        .order_by(DocumentSection.id.asc())
        .all()
    )
    blocks = []
    for idx, sec in enumerate(sections, 1):
        blocks.append({
            "number": idx,
            "id": sec.id,
            "section_id": sec.id,
            "parent_id": sec.parent_id,
            "clause": sec.clause,
            "title": sec.title,
            "level": sec.level,
            "path": str(sec.path) if sec.path is not None else None,
            "type": sec.type_,
            "bbox": sec.bbox,
            "content": sec.content,
            "confidence": 0
        })
    return blocks


def get_page_content_md_str(db: Session, document_id: int, page_num: int) -> str:
    sections = (
        db.query(DocumentSection)
        .filter(DocumentSection.document_id == document_id, DocumentSection.page == page_num)
        .order_by(DocumentSection.id.asc())
        .all()
    )
    if not sections:
        return ""
    
    parts = []
    for sec in sections:
        md_content = render_section_content_to_md(sec.type_, sec.content)
        if not md_content:
            continue
            
        if sec.type_ in ("text", "textBlock"):
            parts.append(f"\n\n{md_content}")
        elif sec.type_ == "headerFooter":
            parts.append(f"\n\n*{md_content}*")
        else:
            parts.append(md_content)
            
    return "\n".join(parts)


def get_page_content_html_str(db: Session, document_id: int, page_num: int) -> str:
    sections = (
        db.query(DocumentSection)
        .filter(DocumentSection.document_id == document_id, DocumentSection.page == page_num)
        .order_by(DocumentSection.id.asc())
        .all()
    )
    if not sections:
        return ""
        
    parts = []
    for sec in sections:
        sec_type = sec.type_
        content = sec.content
        if not isinstance(content, dict):
            parts.append(f'<p data-type="{sec_type}">{str(content or "")}</p>')
            continue
            
        if sec_type == "text":
            text = content.get("html") or content.get("markdown") or content.get("text") or ""
            if text.startswith("<p"):
                parts.append(text)
            else:
                parts.append(f'<p data-type="text">{text}</p>')
        elif sec_type == "textBlock":
            block = content.get("block") or []
            block_htmls = [f"  <p>{item}</p>" for item in block]
            block_str = "\n".join(block_htmls)
            parts.append(f'<section data-type="textBlock">\n{block_str}\n</section>')
        elif sec_type == "headerFooter":
            text = content.get("text") or ""
            parts.append(f'<header data-type="headerFooter" class="header-footer">\n  <span>{text}</span>\n</header>')
        elif sec_type == "table":
            if "html" in content and content["html"]:
                tbl_html = content["html"]
                if tbl_html.startswith("<table") and 'data-type="table"' not in tbl_html:
                    tbl_html = tbl_html.replace("<table", '<table data-type="table"', 1)
                parts.append(tbl_html)
            elif "markdown" in content and content["markdown"]:
                tbl_html = convert_markdown_to_html(content["markdown"], "table")
                if tbl_html.startswith("<table") and 'data-type="table"' not in tbl_html:
                    tbl_html = tbl_html.replace("<table", '<table data-type="table"', 1)
                parts.append(tbl_html)
            else:
                caption = content.get("caption") or ""
                columns = content.get("columns") or []
                rows = content.get("rows") or []
                footnotes = content.get("footnotes") or []
                image_key = content.get("image_key")
                
                col_count = len(columns)
                if rows:
                    col_count = max(col_count, max(len(row) for row in rows))
                if col_count == 0:
                    col_count = 1
                
                tbl_parts = [f'<table data-type="table">']
                if caption:
                    tbl_parts.append(f'  <caption>{caption}</caption>')
                    
                tbl_parts.append('  <thead>')
                header_cells = []
                for idx in range(col_count):
                    col_val = columns[idx] if idx < len(columns) else ""
                    header_cells.append(f'<th>{col_val}</th>')
                tbl_parts.append('    <tr>' + "".join(header_cells) + '</tr>')
                tbl_parts.append('  </thead>')
                    
                if rows:
                    tbl_parts.append('  <tbody>')
                    for row in rows:
                        row_cells = []
                        for idx in range(col_count):
                            val = row[idx] if idx < len(row) else None
                            if val is None or str(val).strip() == "":
                                row_cells.append('<td>&nbsp;</td>')
                            else:
                                row_cells.append(f'<td>{val}</td>')
                        tbl_parts.append('    <tr>' + "".join(row_cells) + '</tr>')
                    tbl_parts.append('  </tbody>')
                    
                if footnotes or image_key:
                    tbl_parts.append('  <tfoot>')
                    for fn in footnotes:
                        tbl_parts.append(f'    <tr><td colspan="{col_count}">{fn}</td></tr>')
                    if image_key:
                        tbl_parts.append(f'    <tr><td colspan="{col_count}">Источник: <a href="/api/v1/files/{image_key}">Изображение источника</a></td></tr>')
                    tbl_parts.append('  </tfoot>')
                    
                tbl_parts.append('</table>')
                parts.append("\n".join(tbl_parts))
        elif sec_type == "list":
            items = content.get("items") or []
            list_items = [f"  <li>{item}</li>" for item in items]
            list_str = "\n".join(list_items)
            parts.append(f'<ul data-type="list">\n{list_str}\n</ul>')
        elif sec_type == "image":
            caption = content.get("caption") or ""
            image_key = content.get("image_key") or ""
            description = content.get("description") or ""
            
            img_parts = [f'<div data-type="image">', '  <figure>']
            if image_key:
                img_parts.append(f'    <img src="/api/v1/files/{image_key}" alt="{caption}">')
            if caption:
                img_parts.append(f'    <figcaption>{caption}</figcaption>')
            img_parts.append('  </figure>')
            if description:
                img_parts.append(f'  <p>{description}</p>')
            img_parts.append('</div>')
            parts.append("\n".join(img_parts))
        elif sec_type == "formula":
            latex = content.get("latex") or ""
            meaning = content.get("meaning") or ""
            image_key = content.get("image_key")
            
            f_parts = [f'<section data-type="formula" class="formula-container">']
            if latex:
                f_parts.append(f'  <span class="latex">$${latex}$$</span>')
            if meaning:
                f_parts.append(f'  <p><em>Физический смысл: {meaning}</em></p>')
            if image_key:
                f_parts.append('  <figure>')
                f_parts.append(f'    <img src="/api/v1/files/{image_key}" alt="{meaning or "formula"}">')
                f_parts.append('  </figure>')
            f_parts.append('</section>')
            parts.append("\n".join(f_parts))
        else:
            parts.append(f'<p data-type="{sec_type}">{str(content)}</p>')
            
    return "\n".join(parts)

