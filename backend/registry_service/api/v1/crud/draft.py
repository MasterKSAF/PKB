from datetime import datetime, timezone
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.v1.models import Draft

def create_draft(db: Session, file_key: str, document_key: str, status: str, raw_data: Optional[dict], created_by: str) -> Draft:
    draft = Draft(
        file_key=file_key,
        document_key=document_key,
        status=status,
        raw_data=raw_data,
        created_by=created_by,
        created_at=func.now(),
        updated_at=func.now()
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

def get_drafts(db: Session, page: int = 1, page_size: int = 50, draft_id: Optional[int] = None, document_key: Optional[str] = None, status: Optional[str] = None) -> Tuple[List[Draft], int]:
    query = db.query(Draft)
    
    if draft_id is not None:
        query = query.filter(Draft.draft_id == draft_id)
    if document_key is not None:
        query = query.filter(Draft.document_key == document_key)
    if status is not None:
        query = query.filter(Draft.status == status)
        
    total = query.count()
    drafts = query.order_by(Draft.draft_id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return drafts, total

def get_draft_by_id(db: Session, draft_id: int) -> Optional[Draft]:
    return db.query(Draft).filter(Draft.draft_id == draft_id).first()

def update_draft_status(db: Session, draft_id: int, status: str, confidence: Optional[float] = None, preview_metadata: Optional[dict] = None, error_code: Optional[str] = None, error_message: Optional[str] = None, updated_by: Optional[str] = None) -> Tuple[Optional[Draft], Optional[str]]:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return None, None
        
    previous_status = draft.status
    draft.status = status
    if confidence is not None:
        draft.confidence = confidence
    if preview_metadata is not None:
        draft.preview_metadata = preview_metadata
    if error_code is not None:
        draft.error_code = error_code
    if error_message is not None:
        draft.error_message = error_message
    if updated_by is not None:
        draft.updated_by = updated_by
        
    draft.updated_at = func.now()
    db.commit()
    db.refresh(draft)
    return draft, previous_status

def update_draft_metadata(db: Session, draft_id: int, preview_metadata: dict, metadata_overrides: Optional[dict], updated_by: str) -> Optional[Draft]:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return None
        
    draft.preview_metadata = preview_metadata
    # Save metadata_overrides directly inside preview_metadata if present
    if metadata_overrides:
        if not isinstance(draft.preview_metadata, dict):
            draft.preview_metadata = {}
        draft.preview_metadata['metadata_overrides'] = metadata_overrides
        
    draft.updated_by = updated_by
    draft.updated_at = func.now()
    db.commit()
    db.refresh(draft)
    return draft

def save_draft_snapshot(db: Session, draft_id: int, preview_metadata: dict) -> Optional[Draft]:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return None
    draft.preview_metadata = preview_metadata
    draft.updated_at = func.now()
    db.commit()
    db.refresh(draft)
    return draft

def delete_draft(db: Session, draft_id: int) -> bool:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return False
    db.delete(draft)
    db.commit()
    return True

