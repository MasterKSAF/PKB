from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, date

class ClassifierRegistryBase(BaseModel):
    parent_code: Optional[str] = None
    full_name: str
    doc_type: str = "OKS"
    jurisdiction: str = "RF"
    language: str = "ru"
    oks_code: Optional[str] = None
    is_thematic: bool = True
    status: Optional[str] = "active"
    effective_date: Optional[date] = None
    replaced_by: Optional[str] = None
    issuing_body: Optional[str] = None
    external_id: Optional[str] = None

class ClassifierRegistryCreate(ClassifierRegistryBase):
    code: str

class ClassifierRegistryUpdate(BaseModel):
    parent_code: Optional[str] = None
    full_name: Optional[str] = None
    doc_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    language: Optional[str] = None
    oks_code: Optional[str] = None
    is_thematic: Optional[bool] = None
    status: Optional[str] = None
    effective_date: Optional[date] = None
    replaced_by: Optional[str] = None
    issuing_body: Optional[str] = None
    external_id: Optional[str] = None

class ClassifierRegistryResponse(ClassifierRegistryBase):
    code: str
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ClassifierTreeResponse(ClassifierRegistryResponse):
    children: List['ClassifierTreeResponse'] = []

    model_config = ConfigDict(from_attributes=True)
