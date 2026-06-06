from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DocumentSectionSchema(BaseModel):
    id: int
    document_id: str
    parent_id: Optional[int] = None
    clause: Optional[str] = None
    title: Optional[str] = None
    level: Optional[int] = None
    path: Optional[str] = None
    page: Optional[int] = None
    bbox: Optional[Dict[str, Any]] = None
    type_: Optional[str] = Field(None, alias='type')
    content: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
        'populate_by_name': True,
    }
