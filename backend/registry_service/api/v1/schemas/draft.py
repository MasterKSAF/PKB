from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, computed_field

class DraftSchema(BaseModel):
    id: int = Field(validation_alias='draft_id')
    registry_document_id: Optional[int] = None
    status: str
    preview_metadata: Optional[dict] = None
    source_draft_id: Optional[int] = None
    document_key: Optional[str] = None
    file_key: Optional[str] = None
    original_filename: Optional[str] = None
    confidence: Optional[float] = None
    raw_data: Optional[Any] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @computed_field
    @property
    def display_name(self) -> Optional[str]:
        if self.original_filename:
            return self.original_filename
        if isinstance(self.preview_metadata, dict):
            title = self.preview_metadata.get('title')
            if isinstance(title, str) and title.strip():
                return title.strip()
        return None

    model_config = {
        'from_attributes': True,
        'extra': 'ignore',
        'populate_by_name': True,
    }

class DraftCreate(BaseModel):
    file_key: str
    document_key: str
    original_filename: Optional[str] = None
    status: str
    raw_data: Optional[dict] = None
    created_by: str

class DraftUpdateStatus(BaseModel):
    status: str
    confidence: Optional[float] = None
    preview_metadata: Optional[dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    updated_by: Optional[str] = None

class DraftUpdateMetadata(BaseModel):
    preview_metadata: dict
    metadata_overrides: Optional[dict] = None
    updated_by: str

class DraftSnapshotCreate(BaseModel):
    preview_metadata: dict

