from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class FileResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    mime_type: str
    url: str
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DeleteFileResponse(BaseModel):
    file_id: str
    deleted_at: datetime

class ExportData(BaseModel):
    designation: Optional[str] = None
    title: Optional[str] = None
    materials: Optional[List[str]] = None
    dimensions: Optional[str] = None
    specification_items: Optional[List[Dict[str, Any]]] = None

class ExportRequest(BaseModel):
    document_id: str
    data: ExportData

class ExportResponse(BaseModel):
    export_id: str
    external_id: str
    status: str
    sent_at: datetime
    response_message: str
    
    model_config = ConfigDict(from_attributes=True)

class SystemStatus(BaseModel):
    api_name: str
    status: str
    last_checked: datetime
    latency_ms: int

class ExternalStatusResponse(BaseModel):
    systems: List[SystemStatus]
    
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = {}

class ErrorResponse(BaseModel):
    error: ErrorDetail
