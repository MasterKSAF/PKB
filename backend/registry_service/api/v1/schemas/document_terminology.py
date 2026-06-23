from typing import Optional
from pydantic import BaseModel

class DocumentTerminologySchema(BaseModel):
    term_id: int
    document_id: int
    term: str
    normalized_term: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None

    model_config = {
        'from_attributes': True,
        'extra': 'ignore',
    }
