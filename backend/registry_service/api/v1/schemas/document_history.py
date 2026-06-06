from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class DocumentHistorySchema(BaseModel):
    id: str
    document_id: str
    event_type: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    comment: Optional[str] = None
    changed_by: Optional[str] = None
    document_snapshot: Optional[Dict[str, Any]] = None
    event_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
    }
