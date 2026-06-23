from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentSchema(BaseModel):
    id: int
    doc_code: str
    title: str
    normalized_title: Optional[str] = None
    source_type: Optional[str] = None
    group_: Optional[str] = Field(None, alias='group')
    mks_oks_code: Optional[str] = None
    status: Optional[str] = None
    okstu_code: Optional[str] = None
    mks_name: Optional[str] = None
    okstu_name: Optional[str] = None
    total_versions: Optional[int] = None
    udk_code: Optional[str] = None
    era: Optional[str] = None
    validity_status: Optional[str] = None
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    adoption_date: Optional[date] = None
    effective_from: Optional[date] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    replaces: Optional[str] = None
    status_note: Optional[str] = None
    file_hash_sha256: Optional[str] = None
    title_hash_sha256: Optional[str] = None
    file_size_bytes: Optional[int] = None
    processing_status: Optional[str] = None
    chunk_count: Optional[int] = None
    successor_doc_id: Optional[int] = None
    predecessor_doc_id: Optional[int] = None
    draft_id: Optional[int] = None
    current_version_id: Optional[int] = None
    classifier_code: Optional[str] = None
    industry_code: Optional[str] = None
    enterprise_id: Optional[int] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    classification_status: Optional[dict] = {}
    metadata: Optional[dict] = Field(default={}, validation_alias='doc_metadata')
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    title_key: Optional[str] = None
    preview_snapshot: Optional[dict] = None

    model_config = {
        'extra': 'ignore',
        'populate_by_name': True,
        'from_attributes': True,
    }
