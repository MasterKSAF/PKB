from typing import Optional
from pydantic import BaseModel

class ClassifierRegistrySchema(BaseModel):
    id: int
    registry_id: str
    name: str
    version: Optional[str] = None
    status: Optional[str] = None
    
    model_config = {
        'from_attributes': True,
        'extra': 'ignore',
    }
