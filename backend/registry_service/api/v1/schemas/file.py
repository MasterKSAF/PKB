from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileSchema(BaseModel):
    file_id: str
    filename: str
    size: int
    mime_type: str
    url: str
    uploaded_at: Optional[datetime] = None
    related_document_id: Optional[str] = None
    storage_path: str

    model_config = {
        'extra': 'ignore',
    }
