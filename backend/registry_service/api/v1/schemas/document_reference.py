from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DocumentReferenceSchema(BaseModel):
    id: str
    source_document_id: str
    target_doc_code: str
    reference_type: Optional[str] = None
    context: Optional[str] = None
    current_status: Optional[str] = None
    replaced_by: Optional[str] = None
    replacement_date: Optional[date] = None
    is_resolved: Optional[bool] = None
    resolved_document_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
    }
