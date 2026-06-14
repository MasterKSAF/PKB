# src/rag_builder/models/responses.py
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    error: str | None = None


class IndexResponse(BaseModel):
    status: str
    document_id: int
    document_version_id: int
    chunks_count: int