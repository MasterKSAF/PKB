from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class TerminologyEntryBase(BaseModel):
    term: str
    normalized_term: str
    context: str = "Общий"
    source: Optional[str] = None

class TerminologyEntryCreate(TerminologyEntryBase):
    pass

class TerminologyEntryUpdate(BaseModel):
    term: Optional[str] = None
    normalized_term: Optional[str] = None
    context: Optional[str] = None
    source: Optional[str] = None

class TerminologyEntryResponse(TerminologyEntryBase):
    term_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
