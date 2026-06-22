from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentVersionSchema(BaseModel):
    id: str
    document_id: str
    version_number: Optional[int] = None
    file_hash_sha256: Optional[str] = None
    file_size_bytes: Optional[int] = None
    format_code: Optional[str] = None
    format_label: Optional[str] = None
    file_key: Optional[str] = None
    revision: Optional[int] = 1
    source_filename: Optional[str] = None
    file_path: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
    }
