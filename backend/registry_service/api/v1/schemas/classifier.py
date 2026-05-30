from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ClassifierSchema(BaseModel):
    id: Optional[UUID]
    classifier_system: str
    code: str
    full_name: str
    description: Optional[str] = None
    status: Optional[str] = None
    parent_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
        'populate_by_name': True,
        'from_attributes': True,
    }
