from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ProjectResponse(BaseModel):
    project_id: int
    user_id: str
    code: str | None
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectListItem(BaseModel):
    project_id: int
    code: str | None
    name: str
    status: str
    created_at: datetime


class ProjectListMeta(BaseModel):
    total: int
    page: int
    page_size: int


class ProjectListResponse(BaseModel):
    items: list[ProjectListItem]
    meta: ProjectListMeta


class CreateProjectRequest(BaseModel):
    code: str
    name: str
    description: str | None = None
    status: str = "active"


class UpdateProjectRequest(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None


class DeleteProjectResponse(BaseModel):
    project_id: int
    deleted_at: datetime


class CreateSessionRequest(BaseModel):
    title: str | None = None
    project_id: int | None = None
    document_ids: list[int] = Field(default_factory=list)
    options: dict = Field(default_factory=dict)


class SessionResponse(BaseModel):
    session_id: int
    title: str | None
    user_id: str
    project_id: int | None
    document_ids: list[int]
    options: dict
    created_at: datetime
    updated_at: datetime


class SessionListMeta(BaseModel):
    total: int
    page: int
    page_size: int


class SessionListItem(BaseModel):
    session_id: int
    title: str | None
    project_id: int | None
    document_ids: list[int]
    last_message_preview: str | None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionListItem]
    meta: SessionListMeta


class UpdateSessionRequest(BaseModel):
    title: str | None = None
    project_id: int | None = None
    document_ids: list[int] | None = None


class DeleteSessionResponse(BaseModel):
    session_id: int
    deleted_at: datetime


class MessageAttachment(BaseModel):
    type: str
    text: str | None = None
    source_document_id: int | None = None
    source_page_number: int | None = None


class MessageOptions(BaseModel):
    search_in_session_docs: bool = True
    use_full_context: bool = True


class SendMessageRequest(BaseModel):
    content: str
    attachments: list[MessageAttachment] = Field(default_factory=list)
    options: MessageOptions = Field(default_factory=MessageOptions)


class SourceResponse(BaseModel):
    document_id: int
    document_title: str | None = None
    section_id: int | None = None
    page: int | None = None
    clause: str | None = None
    path: str | None = None
    section_title: str | None = None
    excerpt: str | None = None
    score: float | None = None
    confidence: float | None = None
    bbox: list | None = None
    content_hash: str | None = None
    page_preview_url: str | None = None
    document_url: str | None = None


class PendingMessageResponse(BaseModel):
    message_id: int
    session_id: int
    role: str
    status: str
    content: str
    timestamp: datetime


class MessageResponse(BaseModel):
    message_id: int
    session_id: int
    role: str
    status: str | None
    content: str | None
    message: str | None = None
    missing_fields: list[str] | None = None
    conflicts: list[dict] | None = None
    sources: list[SourceResponse] = Field(default_factory=list)
    model_used: str | None = None
    processing_time_ms: int | None = None
    warnings: list[str] = Field(default_factory=list)
    timestamp: datetime


class SessionMessagesResponse(BaseModel):
    session_id: int
    title: str | None
    project_id: int | None = None
    document_ids: list[int]
    messages: list[dict]
    has_more: bool


class ContextRequest(BaseModel):
    action: str
    params: dict = Field(default_factory=dict)


class ContextResponse(BaseModel):
    session_id: int
    action: str
    status: str
    message: str
    timestamp: datetime


class ExportRequest(BaseModel):
    format: str = "json"
    options: dict = Field(default_factory=dict)


class ExportResponse(BaseModel):
    export_id: int
    session_id: int | None
    format: str
    status: str
    url: str | None
    expires_at: datetime | None
    created_at: datetime


class AspectRating(BaseModel):
    aspect: str
    rating: int


class FeedbackRequest(BaseModel):
    # session-формат
    session_id: int | str | None = None
    message_id: int | str | None = None
    rating: int | str | None = None  # int 1-5 или "positive"/"negative"/"neutral"
    rating_status: str | None = None  # "positive" | "negative" | "neutral"
    comment: str | None = None
    aspects: list[AspectRating] | None = None
    # UI-формат
    answer_id: int | str | None = None
    useful: bool | None = None
    opened_citation_ids: list[str] | None = None


class FeedbackResponse(BaseModel):
    feedback_id: int
    saved: bool
    rating_status: str | None = None
    metrics_changed: dict


class ChatContext(BaseModel):
    project_id: int | None = None
    document_ids: list[int] = Field(default_factory=list)
    nsi_version: str | None = None


class ChatRequest(BaseModel):
    question: str
    session_id: int | None = None
    context: ChatContext | None = None


class CitationResponse(BaseModel):
    citation_id: str
    document_id: int
    document_title: str | None
    section: str | None
    page: int | None
    fragment: str | None
    page_preview_url: str | None
    document_url: str | None


class AnswerItem(BaseModel):
    number: int
    text: str
    citations: list[CitationResponse] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer_id: int
    session_id: int
    status: str
    message: str | None = None
    answer_items: list[AnswerItem] = Field(default_factory=list)
    missing_fields: list[str] | None = None
    conflicts: list[dict] | None = None
    latency_ms: int


class HistoryItem(BaseModel):
    history_id: int
    session_id: int
    created_at: datetime
    user_id: str
    user_name: str
    question: str
    answer_preview: str
    status: str
    source_count: int
    answer_id: int | None


class HistoryMeta(BaseModel):
    total: int
    page: int
    page_size: int


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    meta: HistoryMeta


class HistoryExportResponse(BaseModel):
    export_id: str
    format: str
    url: str
    created_at: datetime


class TextSearchRequest(BaseModel):
    text: str
    valid_at: str
    document_ids: list[int] | None = None
    top_k: int = Field(default=10, ge=1, le=100)
    filters: dict = Field(default_factory=dict)
    category_ids: list[int] | None = None
    options: dict = Field(default_factory=dict)


class TextSearchResult(BaseModel):
    section_id: int | None = None
    document_id: int
    document_title: str | None = None
    page: int
    content: str
    score: float
    document_type: str
    matched_subquery: str | None = None


class TextSearchAnalysis(BaseModel):
    normalized_query: str
    entities: list[dict]
    subqueries: list[str]


class TextSearchResponse(BaseModel):
    original_text: str
    analysis: TextSearchAnalysis
    results: list[TextSearchResult]
    total_found: int
    processing_time_ms: int
    enrichment_skipped: bool = False


class TextAskRequest(BaseModel):
    text: str
    document_ids: list[str] | None = None
    options: dict = Field(default_factory=dict)


class TextAskSource(BaseModel):
    document_id: int
    document_title: str | None = None
    page_number: int
    fragment_id: str
    text: str
    score: float


class TextAskResponse(BaseModel):
    original_text: str
    normalized_question: str
    answer: str
    sources: list[TextAskSource]
    disclaimer: str
    processing_time_ms: int
    model_used: str


class MessageSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MessageSearchMeta(BaseModel):
    total: int
    page: int
    page_size: int


class MessageSearchResponse(BaseModel):
    session_id: int
    results: list[dict]
    meta: MessageSearchMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
