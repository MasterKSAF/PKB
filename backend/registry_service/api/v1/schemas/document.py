from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class RegistryDocumentBase(BaseModel):
    title: str
    doc_number: Optional[str] = None
    classifier_code: Optional[str] = None
    status: str = "draft"
    source: Optional[str] = None
    notes: Optional[str] = None

class RegistryDocumentCreate(RegistryDocumentBase):
    pass

class RegistryDocumentUpdate(BaseModel):
    title: Optional[str] = None
    doc_number: Optional[str] = None
    classifier_code: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None

class RegistryDocumentResponse(RegistryDocumentBase):
    doc_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
