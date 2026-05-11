"""
Pydantic schemas for Documents API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


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
    COMPLETED = "completed"
    FAILED = "failed"
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


# --- POST /documents ---


class DocumentCreateResponse(BaseModel):
    """Response for document upload (202 Accepted)."""

    document_id: str
    status: DocumentStatus
    user_id: str
    task_id: str
    created_at: datetime


# --- GET /documents ---


class DocumentSummary(BaseModel):
    """Summary statistics for document list."""

    total: int
    ocr_completed: int
    indexed: int
    need_attention: int


class DocumentListItem(BaseModel):
    """Document item in list."""

    document_id: str
    title: str
    document_type: DocumentType
    source: str = "upload"
    version: int = 1
    pages: int
    ocr_status: str
    index_status: str
    user_id: str
    uploaded_by: str
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """Response for document list."""

    summary: DocumentSummary
    items: List[DocumentListItem]
    meta: PaginationMeta


# --- GET /documents/{doc_id} ---


class DocumentDetailMetadata(BaseModel):
    """Metadata for document detail."""

    project: Optional[str] = None
    author: Optional[str] = None


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
    user_id: str
    uploaded_by: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[DocumentDetailMetadata] = None


# --- GET /documents/{doc_id}/status ---


class StatusSteps(BaseModel):
    """Processing steps status."""

    ocr: StepStatus
    layout_parsing: StepStatus
    indexing: StepStatus


class OcrResult(BaseModel):
    """OCR processing result details."""

    pages_total: int
    pages_processed: int
    pages_failed: int
    low_confidence_pages: int
    avg_confidence: float


class IndexResult(BaseModel):
    """Indexing result details."""

    chunks_indexed: int
    status: str


class StatusError(BaseModel):
    """Error details in failed status."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class DocumentStatusProcessing(BaseModel):
    """Document status — processing variant."""

    document_id: str
    user_id: str
    status: str = "processing"
    progress_percent: float
    steps: StatusSteps
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class DocumentStatusCompleted(BaseModel):
    """Document status — completed variant."""

    document_id: str
    user_id: str
    status: str = "completed"
    progress_percent: float = 100.0
    steps: StatusSteps
    ocr_result: OcrResult
    index_result: IndexResult
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DocumentStatusFailed(BaseModel):
    """Document status — failed variant."""

    document_id: str
    user_id: str
    status: str = "failed"
    progress_percent: float
    steps: StatusSteps
    error: StatusError
    started_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


# Union type for status response
DocumentStatusResponse = (
    DocumentStatusProcessing | DocumentStatusCompleted | DocumentStatusFailed
)


# --- GET /documents/{doc_id}/file ---


class DocumentFileResponse(BaseModel):
    """Response for document file download."""

    document_id: str
    document_title: str
    content_type: str
    file_url: str


# --- GET /documents/{doc_id}/pages/{page_num}/preview ---


class PagePreviewResponse(BaseModel):
    """Response for page preview."""

    document_id: str
    document_title: str
    page: int
    content_type: str
    preview_url: str
    text: Optional[str] = None
    highlight: Optional[str] = None


# --- DELETE /documents/{doc_id} ---


class DocumentDeleteResponse(BaseModel):
    """Document delete response."""

    document_id: str
    deleted_at: datetime


# --- POST /documents/{doc_id}/reprocess ---


class ReprocessRequest(BaseModel):
    """Document reprocess request."""

    mode: ReprocessMode


class ReprocessResponse(BaseModel):
    """Document reprocess response."""

    mode: ReprocessMode
    document_id: str
    user_id: str
    task_id: str
    status: str
    created_at: datetime


# --- GET /documents/{doc_id}/errors ---


class ProcessingError(BaseModel):
    """Processing error item."""

    error_id: str
    document_id: str
    page: Optional[int] = None
    stage: str
    error_code: str
    error_message: str
    severity: str
    retry_attempt: int
    timestamp: datetime


class DocumentErrorsResponse(BaseModel):
    """Document errors response."""

    errors: List[ProcessingError]
    meta: PaginationMeta


# --- GET /documents/queue ---


class QueueItem(BaseModel):
    """Item in document processing queue."""

    document_id: str
    title: str
    document_type: DocumentType
    status: DocumentStatus
    progress_percent: float
    steps: StatusSteps
    user_id: str
    uploaded_by: str
    created_at: datetime
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class QueueMeta(BaseModel):
    """Queue metadata."""

    total_in_queue: int
    page: int = 1
    page_size: int = 50


class DocumentQueueResponse(BaseModel):
    """Response for document queue."""

    queue: List[QueueItem]
    meta: QueueMeta


# --- GET /documents/{doc_id}/pages ---


class PageInfo(BaseModel):
    """Page information."""

    page: int
    width: int
    height: int
    ocr_status: str
    confidence: float
    has_text_layer: bool


class DocumentPagesResponse(BaseModel):
    """Response for document pages list."""

    document_id: str
    pages_total: int
    pages: List[PageInfo]
    meta: PaginationMeta


# --- GET /documents/{doc_id}/pages/{page_num} ---


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
    highlighted: bool = False


class PageViewResponse(BaseModel):
    """Page view response."""

    image_url: str
    page: int
    width: int
    height: int
    blocks: List[PageBlock]


# --- GET /documents/{doc_id}/pages/{page_num}/text ---


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

    page: int
    full_text: str
    blocks: List[PageBlockDetail]


# --- GET /documents/{doc_id}/parameters ---


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
    unconfirmed_fields: List[str] = []
    updated_at: datetime
