"""
Validation and comparison API endpoints.
"""
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException

from app.schemas.validation import (
    CompareBatchResponse,
    CompareInitResponse,
    CompareRequest,
    CompareResultResponse,
    MatchStatus,
    NormativeBlock,
    ProjectBlock,
    SourceReference,
)
from app.services.validate_client import ValidationServiceClient

router = APIRouter()


@router.post("/compare", response_model=CompareInitResponse)
async def start_comparison(request: CompareRequest):
    """Start normative and project document comparison."""
    comparison_id = f"cmp-{uuid.uuid4().hex[:7]}"
    
    # In real implementation, would queue async job
    # For now return immediate response
    return CompareInitResponse(
        comparison_id=comparison_id,
        status="processing",
        created_at=datetime.utcnow()
    )


@router.get("/compare/{comparison_id}", response_model=CompareResultResponse)
async def get_comparison_result(comparison_id: str):
    """Get comparison result by ID."""
    validate_client = ValidationServiceClient()
    try:
        result = await validate_client.get_comparison(comparison_id)
        return CompareResultResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await validate_client.close()
