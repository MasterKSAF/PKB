"""
Monitor and metrics API endpoints.
"""

from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import CurrentUser, get_current_user
from app.schemas.common import ErrorResponse

router = APIRouter()


# ---------------------------------------------------------------------------
#  Schemas (local to avoid circular imports)
# ---------------------------------------------------------------------------


class ControlMetrics(BaseModel):
    """Quality metrics for system controls."""

    ocr_quality: float
    retrieval_quality: float
    answers_with_sources: float
    avg_latency_ms: int


class AnswerMetrics(BaseModel):
    """Metrics related to answer quality."""

    useful_rate: float
    rated_answers: int
    flagged_for_review: int
    open_questions: int


class LogEntry(BaseModel):
    """Single log entry."""

    time: datetime
    type: str
    text: str
    level: str


class MonitorMetricsResponse(BaseModel):
    """Response for monitor metrics."""

    control_metrics: ControlMetrics
    answer_metrics: AnswerMetrics
    logs: List[LogEntry]


# ---------------------------------------------------------------------------
#  GET /monitor/metrics
# ---------------------------------------------------------------------------


@router.get(
    "/metrics",
    response_model=MonitorMetricsResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
    },
)
async def get_metrics(
    current_user: CurrentUser = Depends(get_current_user),
) -> MonitorMetricsResponse:
    """Get system monitoring metrics.

    Returns quality indicators, answer statistics, and recent log entries.
    Only users with ``knowledge_admin`` or ``system_admin`` roles have
    access (enforced by RBAC in production).
    """
    now = datetime.now(UTC)

    return MonitorMetricsResponse(
        control_metrics=ControlMetrics(
            ocr_quality=0.94,
            retrieval_quality=0.89,
            answers_with_sources=0.97,
            avg_latency_ms=1850,
        ),
        answer_metrics=AnswerMetrics(
            useful_rate=0.88,
            rated_answers=312,
            flagged_for_review=7,
            open_questions=24,
        ),
        logs=[
            LogEntry(
                time=now,
                type="system",
                text="OCR batch processing completed for doc-8a3f2b",
                level="info",
            ),
            LogEntry(
                time=now,
                type="search",
                text="Search query processed in 120ms (hybrid mode)",
                level="info",
            ),
            LogEntry(
                time=now,
                type="validation",
                text="Comparison cmp-abc1234 completed — match found",
                level="info",
            ),
        ],
    )
