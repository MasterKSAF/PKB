from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CategorySchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        'from_attributes': True,
        'extra': 'ignore',
    }

class CategoryCreateSchema(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    color: Optional[str] = None

    model_config = {
        'extra': 'ignore',
    }

class CategoryUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

    model_config = {
        'extra': 'ignore',
    }
