"""Pydantic schemas — request/response models for API and clients."""

from app.schemas.requests import (
    CheckUniquenessRequest,
    CreateDraftRequest,
    OcrProcessRequest,
    ParserProcessRequest,
    RagBuildRequest,
    RagGenerateRequest,
    RagSearchRequest,
    UpdateDocumentStatusRequest,
    UpdateDraftStatusRequest,
)
from app.schemas.drafts import (
    DecideRequest,
    DecideResponse,
    DraftCreateResponse,
    DraftDetailResponse,
    DraftItem,
    DraftListResponse,
    DraftPreviewResponse,
    DraftPreviewStatusResponse,
    PreviewMetadata,
)
from app.schemas.tasks import (
    TaskListResponse,
    TaskListItem,
    TaskStatsResponse,
    TaskStatusResponse,
    TaskStepItem,
)

__all__ = [
    "CheckUniquenessRequest",
    "CreateDraftRequest",
    "OcrProcessRequest",
    "ParserProcessRequest",
    "RagBuildRequest",
    "RagGenerateRequest",
    "RagSearchRequest",
    "UpdateDocumentStatusRequest",
    "UpdateDraftStatusRequest",
    "DecideRequest",
    "DecideResponse",
    "DraftCreateResponse",
    "DraftDetailResponse",
    "DraftItem",
    "DraftListResponse",
    "DraftPreviewResponse",
    "DraftPreviewStatusResponse",
    "PreviewMetadata",
    "TaskListResponse",
    "TaskListItem",
    "TaskStatsResponse",
    "TaskStatusResponse",
    "TaskStepItem",
]
