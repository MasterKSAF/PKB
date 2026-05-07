from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ClassifierNodeBase(BaseModel):
    parent_code: Optional[str] = None
    full_name: str
    doc_type: str = "OKS"
    jurisdiction: str = "RF"
    language: str = "ru"
    oks_code: Optional[str] = None
    is_thematic: bool = True

class ClassifierNodeCreate(ClassifierNodeBase):
    code: str

class ClassifierNodeUpdate(BaseModel):
    parent_code: Optional[str] = None
    full_name: Optional[str] = None
    doc_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    language: Optional[str] = None
    oks_code: Optional[str] = None
    is_thematic: Optional[bool] = None

class ClassifierNodeResponse(ClassifierNodeCreate):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
