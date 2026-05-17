from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, List
from datetime import datetime
from uuid import UUID

class TerminologyRegistryPurgatoryBase(BaseModel):
    raw_term: str
    standard_term: str
    normalized_value: str
    term_type: Optional[str] = "term"
    is_case_sensitive: Optional[bool] = False
    definition: Optional[str] = None
    synonyms: Optional[List[str]] = []
    related_docs: Optional[List[str]] = []
    scope: Optional[List[str]] = []
    is_blocked: Optional[bool] = False

class TerminologyRegistryPurgatoryCreate(TerminologyRegistryPurgatoryBase):
    pass

class TerminologyRegistryPurgatoryUpdate(BaseModel):
    raw_term: Optional[str] = None
    standard_term: Optional[str] = None
    normalized_value: Optional[str] = None
    term_type: Optional[str] = None
    is_case_sensitive: Optional[bool] = None
    definition: Optional[str] = None
    synonyms: Optional[List[str]] = None
    related_docs: Optional[List[str]] = None
    scope: Optional[List[str]] = None
    is_blocked: Optional[bool] = None

class TerminologyRegistryPurgatoryResponse(TerminologyRegistryPurgatoryBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class TerminologyRegistryPurgatoryNormalizeResponse(BaseModel):
    raw_term: str
    standard_term: str
    normalized_value: str
    term_type: Optional[str] = None
    is_blocked: Optional[bool] = False
