from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TerminologySchema(BaseModel):
    id: Optional[UUID]
    raw_term: str
    standard_term: str
    normalized_value: str
    term_type: str
    is_blocked: Optional[bool] = False
    definition: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
        'populate_by_name': True,
        'from_attributes': True,
    }
