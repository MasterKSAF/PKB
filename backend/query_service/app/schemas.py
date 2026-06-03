from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field



class SessionOptions(BaseModel):
    model: str | None = None
    temperature: float | None = None
    max_context_messages: int | None = None
    system_prompt_override: str | None = None


class CreateSessionRequest(BaseModel):
    title: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    options: SessionOptions = Field(default_factory=SessionOptions)


class SessionResponse(BaseModel):
    session_id: str
    title: str | None
    user_id: str
    document_ids: list[str]
    options: dict
    message_count: int
    created_at: datetime
    updated_at: datetime


class SessionListMeta(BaseModel):
    total: int
    page: int
    page_size: int


class SessionListItem(BaseModel):
    session_id: str
    title: str | None
    document_ids: list[str]
    message_count: int
    last_message_preview: str | None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionListItem]
    meta: SessionListMeta


class UpdateSessionRequest(BaseModel):
    title: str | None = None
    document_ids: list[str] | None = None


class DeleteSessionResponse(BaseModel):
    session_id: str
    deleted_at: datetime



class MessageAttachment(BaseModel):
    type: str
    text: str | None = None
    source_document_id: str | None = None
    source_page_number: int | None = None


class MessageOptions(BaseModel):
    search_in_session_docs: bool = True
    use_full_context: bool = True


class SendMessageRequest(BaseModel):
    content: str
    attachments: list[MessageAttachment] = Field(default_factory=list)
    options: MessageOptions = Field(default_factory=MessageOptions)


class SourceResponse(BaseModel):
    document_id: str
    document_title: str | None
    page_number: int | None
    fragment_id: str | None
    text: str | None
    score: float | None


class PendingMessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    status: str
    content: str
    timestamp: datetime


class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    status: str | None
    content: str | None
    message: str | None = None
    missing_fields: list[str] | None = None
    conflicts: list[dict] | None = None
    sources: list[SourceResponse] = Field(default_factory=list)
    model_used: str | None = None
    processing_time_ms: int | None = None
    timestamp: datetime


class SessionMessagesResponse(BaseModel):
    session_id: str
    title: str | None
    document_ids: list[str]
    messages: list[dict]
    has_more: bool



class ContextRequest(BaseModel):
    action: str
    params: dict = Field(default_factory=dict)


class ContextResponse(BaseModel):
    session_id: str
    action: str
    status: str
    message: str
    timestamp: datetime



class ExportRequest(BaseModel):
    format: str = "json"
    options: dict = Field(default_factory=dict)


class ExportResponse(BaseModel):
    export_id: str
    session_id: str | None
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
    session_id: str | None = None
    message_id: str | None = None
    rating: str | None = None
    comment: str | None = None
    aspects: list[AspectRating] | None = None
    # UI-формат
    answer_id: str | None = None
    useful: bool | None = None
    opened_citation_ids: list[str] | None = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    saved: bool
    metrics_changed: dict



class ChatContext(BaseModel):
    project_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    nsi_version: str | None = None


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    context: ChatContext | None = None


class CitationResponse(BaseModel):
    citation_id: str
    document_id: str
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
    answer_id: str
    session_id: str
    status: str
    message: str | None = None
    answer_items: list[AnswerItem] = Field(default_factory=list)
    missing_fields: list[str] | None = None
    conflicts: list[dict] | None = None
    latency_ms: int



class HistoryItem(BaseModel):
    history_id: str
    session_id: str
    created_at: datetime
    user_id: str
    user_name: str
    question: str
    answer_preview: str
    status: str
    source_count: int
    answer_id: str | None


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
    document_ids: list[str] | None = None
    top_k: int = 10
    filters: dict = Field(default_factory=dict)
    options: dict = Field(default_factory=dict)


class TextSearchResult(BaseModel):
    section_id: int | None = None
    document_id: str
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


class TextAskRequest(BaseModel):
    text: str
    document_ids: list[str] | None = None
    options: dict = Field(default_factory=dict)


class TextAskSource(BaseModel):
    document_id: str
    document_title: str | None
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



class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
