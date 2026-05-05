"""
Documents API endpoints.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.schemas.documents import (
    DocumentCreateResponse,
    DocumentDetailResponse,
    DocumentErrorsResponse,
    DocumentFilters,
    DocumentListItem,
    DocumentListResponse,
    DocumentDeleteResponse,
    DocumentParametersResponse,
    DocumentStatusResponse,
    DocumentStatusSteps,
    PageTextResponse,
    PageViewResponse,
    ProcessingError,
    ReprocessRequest,
    ReprocessResponse,
    StepStatus,
)
from app.schemas.common import ErrorResponse
from app.services.rag_client import RAGServiceClient
from app.services.ocr_client import OCRServiceClient
from app.services.integration_client import IntegrationServiceClient
from app.services.validate_client import ValidationServiceClient

router = APIRouter()


@router.post(
    "/",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Неподдерживаемый формат/размер"},
        422: {"model": ErrorResponse, "description": "Поврежденный файл"},
    }
)
async def upload_document(
    file: UploadFile = File(..., description="Бинарный файл (PDF, PNG, JPG, TIFF)"),
    document_type: str = Form(..., description="Тип документа: normative, archival_scan, drawing, specification"),
    metadata: Optional[str] = Form(None, description="JSON-строка с метаданными"),
):
    """Upload document to processing queue."""
    # Validate file type
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/tiff"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": 400,
                    "code_name": "BAD_REQUEST",
                    "message": "Неподдерживаемый формат файла",
                    "details": {"allowed_types": allowed_types}
                }
            }
        )
    
    # Generate IDs
    document_id = f"doc-{uuid.uuid4().hex[:7]}"
    task_id = f"task-ocr-{uuid.uuid4().hex[:6]}"
    
    # Upload to integration service
    integration_client = IntegrationServiceClient()
    try:
        content = await file.read()
        await integration_client.upload_file(
            file_data=content,
            filename=file.filename,
            related_document_id=document_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await integration_client.close()
    
    return DocumentCreateResponse(
        document_id=document_id,
        status="queued",
        task_id=task_id,
        created_at=datetime.utcnow()
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    type: Optional[str] = Query(None, description="Фильтр по типу документа"),
    date_from: Optional[datetime] = Query(None, description="Дата начала (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Дата окончания"),
    search: Optional[str] = Query(None, description="Поиск по имени файла"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List documents with filtering."""
    # Mock data for now - in real implementation would query database
    documents = [
        DocumentListItem(
            document_id="doc-8a3f2b",
            filename="21900M2_spec.pdf",
            document_type="specification",
            status=status or "processing",
            pages_total=12,
            pages_processed=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    
    return DocumentListResponse(
        documents=documents,
        total=1,
        limit=limit,
        offset=offset
    )


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: str):
    """Get document details."""
    return DocumentDetailResponse(
        document_id=doc_id,
        filename="21900M2_spec.pdf",
        document_type="specification",
        status="processed",
        file_size=2048576,
        pages_total=12,
        pages_processed=12,
        pages_failed=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={"project": "21900M2", "author": "Иванов"}
    )


@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(doc_id: str):
    """Get document processing progress."""
    return DocumentStatusResponse(
        document_id=doc_id,
        status="processing",
        progress_percent=41.7,
        steps=DocumentStatusSteps(
            ocr=StepStatus.IN_PROGRESS,
            layout_parsing=StepStatus.PENDING,
            indexing=StepStatus.PENDING
        ),
        started_at=datetime.utcnow(),
        estimated_completion=datetime.utcnow()
    )


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(doc_id: str):
    """Delete document and related data."""
    # Delete from index
    rag_client = RAGServiceClient()
    try:
        await rag_client.delete_index(doc_id)
    except Exception:
        pass  # Ignore errors for non-indexed documents
    finally:
        await rag_client.close()
    
    return DocumentDeleteResponse(
        document_id=doc_id,
        deleted_at=datetime.utcnow()
    )


@router.post("/{doc_id}/reprocess", response_model=ReprocessResponse)
async def reprocess_document(doc_id: str, request: ReprocessRequest):
    """Reprocess document."""
    task_id = f"task-ocr-{uuid.uuid4().hex[:6]}"
    
    return ReprocessResponse(
        document_id=doc_id,
        task_id=task_id,
        status="reprocessing_queued",
        mode=request.mode,
        created_at=datetime.utcnow()
    )


@router.get("/{doc_id}/errors", response_model=DocumentErrorsResponse)
async def get_document_errors(
    doc_id: str,
    stage: Optional[str] = Query(None, description="Этап: upload, ocr, parsing, indexing, generation"),
    severity: Optional[str] = Query(None, description="Уровень: warning, error"),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
):
    """Get document processing errors log."""
    errors = [
        ProcessingError(
            error_id="err-001",
            document_id=doc_id,
            page_number=5,
            stage=stage or "ocr",
            error_code="LOW_CONFIDENCE",
            error_message="Качество распознавания страницы ниже порога (confidence=0.62)",
            severity=severity or "warning",
            retry_attempt=0,
            timestamp=datetime.utcnow()
        )
    ] if not stage or stage == "ocr" else []
    
    return DocumentErrorsResponse(
        errors=errors,
        total=len(errors)
    )


@router.get("/{doc_id}/pages/{page_num}", response_model=PageViewResponse)
async def get_page_view(
    doc_id: str,
    page_num: int,
    highlight: Optional[str] = Query(None, description="ID блока для подсветки"),
):
    """Get page image with block highlighting."""
    from app.schemas.documents import BlockCoordinates, PageBlock
    
    return PageViewResponse(
        image_url=f"/files/page-img/{doc_id}_{page_num}.png",
        page_number=page_num,
        width=2480,
        height=3508,
        blocks=[
            PageBlock(
                block_id="blk-001",
                type="title_block",
                coordinates=BlockCoordinates(x=200, y=100, width=800, height=50),
                text="Спецификация 21900M2.362135.0903",
                highlighted=False
            ),
            PageBlock(
                block_id=highlight or "blk-002",
                type="table",
                coordinates=BlockCoordinates(x=150, y=200, width=1800, height=600),
                text="...",
                highlighted=highlight is not None
            )
        ]
    )


@router.get("/{doc_id}/pages/{page_num}/text", response_model=PageTextResponse)
async def get_page_text(doc_id: str, page_num: int):
    """Get page text layer and structure."""
    from app.schemas.documents import BlockCoordinates, PageBlockDetail
    
    return PageTextResponse(
        page_number=page_num,
        full_text="Спецификация...\nПоз. 1 Кница...",
        blocks=[
            PageBlockDetail(
                block_id="blk-001",
                type="title_block",
                coordinates=BlockCoordinates(x=200, y=100, width=800, height=50),
                text="Спецификация 21900M2.362135.0903",
                confidence=0.98
            ),
            PageBlockDetail(
                block_id="blk-002",
                type="table",
                coordinates=BlockCoordinates(x=150, y=200, width=1800, height=600),
                text="Поз.|Наименование|Кол.|Масса|Материал",
                confidence=0.92,
                table_data=[
                    ["Поз.", "Наименование", "Кол.", "Масса", "Материал"],
                    ["1", "Кница", "2", "0.5", "сталь 09Г2С"]
                ]
            )
        ]
    )


@router.get("/{doc_id}/parameters", response_model=DocumentParametersResponse)
async def get_document_parameters(doc_id: str):
    """Get extracted structured parameters from document."""
    from app.schemas.documents import DocumentParameters, SpecificationItem
    
    # Try to get from validation service
    validate_client = ValidationServiceClient()
    try:
        result = await validate_client.extract_parameters(
            document_id=doc_id,
            document_type="specification"
        )
        return DocumentParametersResponse(**result)
    except Exception:
        # Return mock data
        return DocumentParametersResponse(
            document_id=doc_id,
            document_type="specification",
            parameters=DocumentParameters(
                designation="21900M2.362135.0903",
                title="Секция 0903",
                materials=["сталь 09Г2С", "алюминий АМг5"],
                dimensions=["1200x800x6", "L=2500"],
                references=["21900M2.362135.0901СБ", "21900M2.362135.0902СБ"],
                specification_items=[
                    SpecificationItem(
                        position="1",
                        name="Кница",
                        quantity="2",
                        dimensions="10x200x300",
                        weight="0.5",
                        material="сталь 09Г2С",
                        note=""
                    )
                ]
            ),
            extraction_confidence=0.89,
            unconfirmed_fields=["dimensions позиции 3"],
            updated_at=datetime.utcnow()
        )
    finally:
        await validate_client.close()
