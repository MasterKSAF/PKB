from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class TerminologySchema(BaseModel):
    id: Optional[int] = None
    raw_term: str
    standard_term: str
    normalized_value: str
    term_type: str
    is_blocked: Optional[bool] = False
    is_case_sensitive: Optional[bool] = False
    definition: Optional[str] = None
    synonyms: Optional[List[str]] = []
    related_docs: Optional[List[str]] = []
    scope: Optional[List[str]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
        'populate_by_name': True,
        'from_attributes': True,
    }
