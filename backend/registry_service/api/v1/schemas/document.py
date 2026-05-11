from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from api.v1.models.document import DocStatus

class DocumentsBase(BaseModel):
    title: str
    doc_number: Optional[str] = Field(None, alias="doc_code")
    classifier_code: Optional[str] = None
    status: Optional[DocStatus] = DocStatus.DRAFT
    source: Optional[str] = None
    notes: Optional[str] = None

class DocumentsCreate(DocumentsBase):
    pass

class DocumentsUpdate(BaseModel):
    title: Optional[str] = None
    doc_number: Optional[str] = None
    classifier_code: Optional[str] = None
    status: Optional[DocStatus] = None
    source: Optional[str] = None
    notes: Optional[str] = None

class DocumentsStatusUpdate(BaseModel):
    status: DocStatus

class DocumentsResponse(DocumentsBase):
    doc_id: UUID = Field(alias="id")
    classifier_name: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
