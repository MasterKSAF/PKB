from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ClassifierSchema(BaseModel):
    classifier_system: str
    code: str
    full_name: str
    description: Optional[str] = None
    status: Optional[str] = None
    parent_code: Optional[str] = None
    effective_date: Optional[date] = None
    replaced_by: Optional[str] = None
    children: Optional[list[ClassifierSchema]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        'extra': 'ignore',
        'populate_by_name': True,
        'from_attributes': True,
    }


class ClassificationInput(BaseModel):
    mks_oks_code: Optional[str] = None
    okstu_code: Optional[str] = None
    udk_code: Optional[str] = None

    model_config = {
        'extra': 'ignore',
        'from_attributes': True,
    }


class ClassifierValidateRequest(BaseModel):
    classification: ClassificationInput

    model_config = {
        'extra': 'ignore',
        'from_attributes': True,
    }
