from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class DraftSchema(BaseModel):
    draft_id: int
    registry_document_id: Optional[int] = None
    status: str
    preview_metadata: Optional[dict] = None
    source_draft_id: Optional[int] = None
    document_key: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    model_config = {
        'from_attributes': True,
        'extra': 'ignore',
    }
