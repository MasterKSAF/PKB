from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date

class ClassifierRegistryBase(BaseModel):
    parent_code: Optional[str] = None
    full_name: str
    status: Optional[str] = "active"
    effective_date: Optional[date] = None
    replaced_by: Optional[str] = None
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    language: Optional[str] = "ru"
    oks_code: Optional[str] = None
    doc_type: Optional[str] = None
    is_thematic: Optional[bool] = True
    external_id: Optional[str] = None

class ClassifierRegistryCreate(ClassifierRegistryBase):
    code: str

class ClassifierRegistryUpdate(BaseModel):
    parent_code: Optional[str] = None
    full_name: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[date] = None
    replaced_by: Optional[str] = None
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    language: Optional[str] = None
    oks_code: Optional[str] = None
    doc_type: Optional[str] = None
    is_thematic: Optional[bool] = None
    external_id: Optional[str] = None

class ClassifierRegistryResponse(ClassifierRegistryCreate):
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
