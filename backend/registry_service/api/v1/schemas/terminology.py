from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID

class TerminologyRegistryBase(BaseModel):
    raw_term: str
    standard_term: str
    normalized_value: str
    term_type: Optional[str] = "term"
    is_case_sensitive: Optional[bool] = False
    definition: Optional[str] = None
    synonyms: Optional[Any] = []
    related_docs: Optional[Any] = []
    scope: Optional[Any] = []
    is_blocked: Optional[bool] = False

class TerminologyRegistryCreate(TerminologyRegistryBase):
    pass

class TerminologyRegistryUpdate(BaseModel):
    raw_term: Optional[str] = None
    standard_term: Optional[str] = None
    normalized_value: Optional[str] = None
    term_type: Optional[str] = None
    is_case_sensitive: Optional[bool] = None
    definition: Optional[str] = None
    synonyms: Optional[Any] = None
    related_docs: Optional[Any] = None
    scope: Optional[Any] = None
    is_blocked: Optional[bool] = None

class TerminologyRegistryResponse(TerminologyRegistryBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
