from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentSchema(BaseModel):
    id: str
    doc_code: str
    title: str
    normalized_title: Optional[str] = None
    source_type: Optional[str] = None
    group_: Optional[str] = Field(None, alias='group')
    mks_oks_code: Optional[str] = None
    okstu_code: Optional[str] = None
    udc: Optional[str] = None
    era: Optional[str] = None
    validity_status: Optional[str] = None
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    adoption_date: Optional[date] = None
    effective_from: Optional[date] = None
    replaces: Optional[str] = None
    status_note: Optional[str] = None
    file_hash_sha256: Optional[str] = None
    title_hash_sha256: Optional[str] = None
    file_size_bytes: Optional[int] = None
    processing_status: Optional[str] = None
    chunk_count: Optional[int] = None
    successor_doc_id: Optional[str] = None
    predecessor_doc_id: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
        'populate_by_name': True,
    }
