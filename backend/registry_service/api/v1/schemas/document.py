from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from api.v1.models.document import DocStatus

class DocumentsPurgatoryBase(BaseModel):
    title: str
    doc_code: Optional[str] = None
    source_type: Optional[str] = None
    era: Optional[str] = None
    validity_status: Optional[str] = None
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    classifier_system: Optional[str] = "MKS"
    mks_oks_code: Optional[str] = None
    okstu_code: Optional[str] = None
    classification_status: Optional[dict] = None
    successor_doc_id: Optional[UUID] = None
    predecessor_doc_id: Optional[UUID] = None
    metadata: Optional[dict] = Field(default=None, alias='metadata_')
    status: Optional[DocStatus] = None

    model_config = ConfigDict(populate_by_name=True)

class DocumentsPurgatoryCreate(DocumentsPurgatoryBase):
    pass

class DocumentsPurgatoryUpdate(BaseModel):
    title: Optional[str] = None
    doc_code: Optional[str] = None
    source_type: Optional[str] = None
    era: Optional[str] = None
    validity_status: Optional[str] = None
    jurisdiction: Optional[str] = None
    issuing_body: Optional[str] = None
    classifier_system: Optional[str] = None
    mks_oks_code: Optional[str] = None
    okstu_code: Optional[str] = None
    classification_status: Optional[dict] = None
    successor_doc_id: Optional[UUID] = None
    predecessor_doc_id: Optional[UUID] = None
    metadata: Optional[dict] = Field(default=None, alias='metadata_')
    status: Optional[DocStatus] = None

    model_config = ConfigDict(populate_by_name=True)

class DocumentsPurgatoryStatusUpdate(BaseModel):
    status: DocStatus
    comment: Optional[str] = None
    changed_by: Optional[str] = None

class DocumentsPurgatoryResponse(DocumentsPurgatoryBase):
    id: UUID
    mks_name: Optional[str] = None
    okstu_name: Optional[str] = None
    title_hash_sha256: Optional[str] = None
    status: Optional[DocStatus] = None
    total_versions: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: Optional[datetime]
    created_by: Optional[str] = None
    updated_at: Optional[datetime]
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
