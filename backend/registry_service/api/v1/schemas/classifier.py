from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, date

class ClassifierRegistryPurgatoryBase(BaseModel):
    parent_code: Optional[str] = None
    full_name: str
    status: Optional[str] = "active"
    effective_date: Optional[date] = None
    replaced_by: Optional[str] = None

class ClassifierRegistryPurgatoryCreate(ClassifierRegistryPurgatoryBase):
    classifier_system: str = "MKS"
    code: str

class ClassifierRegistryPurgatoryUpdate(BaseModel):
    parent_code: Optional[str] = None
    full_name: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[date] = None
    replaced_by: Optional[str] = None

class ClassifierRegistryPurgatoryResponse(ClassifierRegistryPurgatoryBase):
    classifier_system: str
    code: str
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ClassifierTreePurgatoryResponse(ClassifierRegistryPurgatoryResponse):
    children: List['ClassifierTreePurgatoryResponse'] = []

    model_config = ConfigDict(from_attributes=True)
