"""
Validation and comparison API endpoints.
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.schemas.validation import (
    CheckExportResponse,
    CheckItem,
    CheckRunResponse,
    CheckRunStatusResponse,
    CheckSource,
    CheckSummary,
    CompareBatchResponse,
    CompareInitResponse,
    CompareRequest,
    CompareResultResponse,
)
from app.services.validate_client import ValidationServiceClient

router = APIRouter()


@router.post(
    "/compare",
    response_model=CompareInitResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_comparison(request: CompareRequest):
    """Start normative and project document comparison."""
    comparison_id = f"cmp-{uuid.uuid4().hex[:7]}"

    # In real implementation, would queue async job
    # For now return immediate response
    return CompareInitResponse(
        comparison_id=comparison_id,
        status="processing",
        created_at=datetime.utcnow(),
    )


@router.get("/compare/{comparison_id}", response_model=CompareResultResponse)
async def get_comparison_result(comparison_id: str):
    """Get comparison result by ID."""
    validate_client = ValidationServiceClient()
    try:
        result = await validate_client.get_comparison(comparison_id)
        return CompareResultResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "COMPARISON_NOT_FOUND",
                    "message": str(e),
                    "details": {"comparison_id": comparison_id},
                }
            },
        )
    finally:
        await validate_client.close()


@router.post("/compare/batch", response_model=CompareBatchResponse)
async def batch_compare(pairs: List[dict]):
    """Batch comparison of fragment pairs."""
    validate_client = ValidationServiceClient()
    try:
        result = await validate_client.compare_batch(pairs)
        return CompareBatchResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BATCH_COMPARISON_ERROR",
                    "message": str(e),
                    "details": {},
                }
            },
        )
    finally:
        await validate_client.close()


@router.post(
    "/checks",
    response_model=CheckRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_check_run():
    """Start a new check run."""
    check_run_id = f"chk-{uuid.uuid4().hex[:7]}"

    # Mock data
    items = [
        CheckItem(
            check_item_id=f"ci-{uuid.uuid4().hex[:4]}",
            project="Проект А",
            section="Раздел 1",
            parameter="Толщина стены",
            project_value="200 мм",
            nsi_requirement="≥180 мм",
            nsi_document="СНиП 2.01.07-85",
            status="ok",
            comment=None,
            project_source=CheckSource(
                document_id="doc-proj-001",
                page=12,
                page_preview_url="/previews/doc-proj-001/p12.png",
                document_url="/documents/doc-proj-001",
            ),
            nsi_source=CheckSource(
                document_id="doc-norm-001",
                page=5,
                page_preview_url="/previews/doc-norm-001/p5.png",
                document_url="/documents/doc-norm-001",
            ),
        ),
        CheckItem(
            check_item_id=f"ci-{uuid.uuid4().hex[:4]}",
            project="Проект А",
            section="Раздел 2",
            parameter="Высота потолков",
            project_value="2.5 м",
            nsi_requirement="≥2.7 м",
            nsi_document="СНиП 2.08.01-89",
            status="warning",
            comment="Требуется дополнительная проверка",
            project_source=CheckSource(
                document_id="doc-proj-001",
                page=25,
                page_preview_url="/previews/doc-proj-001/p25.png",
                document_url="/documents/doc-proj-001",
            ),
            nsi_source=CheckSource(
                document_id="doc-norm-002",
                page=3,
                page_preview_url="/previews/doc-norm-002/p3.png",
                document_url="/documents/doc-norm-002",
            ),
        ),
    ]

    summary = CheckSummary(ok=1, warning=1, error=0)

    return CheckRunResponse(
        check_run_id=check_run_id,
        status="completed",
        summary=summary,
        items=items,
    )


@router.get("/checks/{check_run_id}", response_model=CheckRunStatusResponse)
async def get_check_run_status(check_run_id: str):
    """Get check run status."""
    return CheckRunStatusResponse(
        check_run_id=check_run_id,
        status="completed",
        progress_percent=100.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get("/checks/{check_run_id}/export", response_model=CheckExportResponse)
async def export_check_run(check_run_id: str):
    """Export check run results."""
    return CheckExportResponse(
        check_run_id=check_run_id,
        export_url=f"/exports/{check_run_id}/report.xlsx",
        format="xlsx",
        created_at=datetime.utcnow(),
    )
