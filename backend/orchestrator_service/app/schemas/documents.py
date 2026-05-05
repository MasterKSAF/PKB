"""
Pydantic schemas for Documents API.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document types."""
    NORMATIVE = "normative"
    ARCHIVAL_SCAN = "archival_scan"
    DRAWING = "drawing"
    SPECIFICATION = "specification"


class DocumentStatus(str, Enum):
    """Document processing status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class ReprocessMode(str, Enum):
    """Document reprocessing modes."""
    STANDARD = "standard"
    ENHANCED_PREPROCESS = "enhanced_preprocess"
    FALLBACK_OCR = "fallback_ocr"


class StepStatus(str, Enum):
    """Processing step status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class DocumentCreateResponse(BaseModel):
    """Response for document upload."""
    document_id: str
    status: DocumentStatus
    task_id: str
    created_at: datetime


class DocumentListItem(BaseModel):
    """Document item in list."""
    document_id: str
    filename: str
    document_type: DocumentType
    status: DocumentStatus
    pages_total: int
    pages_processed: int
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """Response for document list."""
    documents: List[DocumentListItem]
    total: int
    limit: int
    offset: int


class DocumentDetailResponse(BaseModel):
    """Document detail response."""
    document_id: str
    filename: str
    document_type: DocumentType
    status: DocumentStatus
    file_size: int
    pages_total: int
    pages_processed: int
    pages_failed: int
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class DocumentStatusSteps(BaseModel):
    """Processing steps status."""
    ocr: StepStatus
    layout_parsing: StepStatus
    indexing: StepStatus


class DocumentStatusResponse(BaseModel):
    """Document processing status response."""
    document_id: str
    status: DocumentStatus
    progress_percent: float
    steps: DocumentStatusSteps
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class DocumentDeleteResponse(BaseModel):
    """Document delete response."""
    document_id: str
    deleted_at: datetime


class ReprocessRequest(BaseModel):
    """Document reprocess request."""
    mode: ReprocessMode


class ReprocessResponse(BaseModel):
    """Document reprocess response."""
    document_id: str
    task_id: str
    status: str
    mode: ReprocessMode
    created_at: datetime


class ProcessingError(BaseModel):
    """Processing error item."""
    error_id: str
    document_id: str
    page_number: Optional[int] = None
    stage: str
    error_code: str
    error_message: str
    severity: str
    retry_attempt: int
    timestamp: datetime


class DocumentErrorsResponse(BaseModel):
    """Document errors response."""
    errors: List[ProcessingError]
    total: int


class DocumentFilters(BaseModel):
    """Query filters for document list."""
    status: Optional[DocumentStatus] = None
    type: Optional[DocumentType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    limit: int = 20
    offset: int = 0


class BlockCoordinates(BaseModel):
    """Block coordinates on page."""
    x: int
    y: int
    width: int
    height: int


class PageBlock(BaseModel):
    """Page block item."""
    block_id: str
    type: str
    coordinates: BlockCoordinates
    text: str
    highlighted: bool


class PageViewResponse(BaseModel):
    """Page view response."""
    image_url: str
    page_number: int
    width: int
    height: int
    blocks: List[PageBlock]


class PageBlockDetail(BaseModel):
    """Page block detail."""
    block_id: str
    type: str
    coordinates: BlockCoordinates
    text: str
    confidence: float
    table_data: Optional[List[List[str]]] = None


class PageTextResponse(BaseModel):
    """Page text response."""
    page_number: int
    full_text: str
    blocks: List[PageBlockDetail]


class SpecificationItem(BaseModel):
    """Specification item."""
    position: str
    name: str
    quantity: str
    dimensions: Optional[str] = None
    weight: Optional[str] = None
    material: Optional[str] = None
    note: Optional[str] = None


class DocumentParameters(BaseModel):
    """Document extracted parameters."""
    designation: Optional[str] = None
    title: Optional[str] = None
    materials: List[str] = []
    dimensions: List[str] = []
    references: List[str] = []
    specification_items: List[SpecificationItem] = []


class DocumentParametersResponse(BaseModel):
    """Document parameters response."""
    document_id: str
    document_type: DocumentType
    parameters: DocumentParameters
    extraction_confidence: float
    unconfirmed_fields: List[str]
    updated_at: datetime
