from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FormatRegistrySchema(BaseModel):
    id: Optional[int] = None
    format_code: str
    mime_type: str
    parser_engine: str
    supported: Optional[bool] = True
    created_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
        'populate_by_name': True,
        'from_attributes': True,
    }
