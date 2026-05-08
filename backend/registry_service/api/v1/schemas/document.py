from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from api.v1.models.document import DocStatus

class DocumentsBase(BaseModel):
    title: str
    classifier_code: Optional[str] = None
    doc_code: Optional[str] = None
    title_hash_sha256: Optional[str] = None
    status: Optional[DocStatus] = DocStatus.DRAFT
    metadata_: Optional[Any] = Field(default_factory=dict, alias="metadata")
    chunk_container_id: Optional[UUID] = None

class DocumentsCreate(DocumentsBase):
    pass

class DocumentsUpdate(BaseModel):
    title: Optional[str] = None
    classifier_code: Optional[str] = None
    doc_code: Optional[str] = None
    title_hash_sha256: Optional[str] = None
    status: Optional[DocStatus] = None
    metadata_: Optional[Any] = Field(None, alias="metadata")
    chunk_container_id: Optional[UUID] = None

class DocumentsResponse(DocumentsBase):
    id: UUID
    created_at: Optional[datetime]
    created_by: Optional[str]
    updated_at: Optional[datetime]
    updated_by: Optional[str]

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
