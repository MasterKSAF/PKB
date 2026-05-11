from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

class TerminologyRegistryBase(BaseModel):
    term: str = Field(alias="raw_term")
    normalized_term: str = Field(alias="normalized_value")
    context: str = "Общий"
    source: Optional[str] = None

class TerminologyRegistryCreate(TerminologyRegistryBase):
    pass

class TerminologyRegistryUpdate(BaseModel):
    term: Optional[str] = None
    normalized_term: Optional[str] = None
    context: Optional[str] = None
    source: Optional[str] = None

class TerminologyRegistryResponse(TerminologyRegistryBase):
    term_id: UUID = Field(alias="id")
    created_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class TerminologyNormalizeResponse(BaseModel):
    term: str
    normalized_term: str
