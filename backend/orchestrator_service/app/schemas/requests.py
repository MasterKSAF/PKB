"""
Pydantic request schemas for external service clients.

Each schema is used as ``request_model`` in ``ServiceClient.call()`` to
validate request bodies before they reach mock/HTTP layers.

This catches type mismatches at the earliest possible boundary.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
#  Registry Service
# ---------------------------------------------------------------------------

class CreateDraftRequest(BaseModel):
    """Request body for POST /registry/drafts."""

    file_key: str = Field(..., description="Ключ файла")
    document_key: str = Field(..., description="Ключ документа")
    created_by: str = Field(..., description="Кто создал (UUID пользователя)")
    file_hash_sha256: Optional[str] = Field(None, description="SHA-256 хэш файла")
    title_hash_sha256: Optional[str] = Field(None, description="SHA-256 хэш названия")
    title_key: Optional[str] = Field(None, description="Исходная строка конкатенации для title_hash_sha256 (DB-28)")
    metadata_fields: Optional[Dict[str, Any]] = Field(
        None, description="Метаданные из формы POST /drafts: source_type, doc_code, mks_oks_code и др."
    )


class UpdateDraftStatusRequest(BaseModel):
    """Request body for PATCH /registry/drafts/{id}/status."""

    status: str = Field(..., description="Новый статус")
    document_id: Optional[int] = Field(None, description="ID документа (после approve)")


class UpdateDocumentStatusRequest(BaseModel):
    """Request body for PATCH /registry/documents/{id}/status.

    Internal endpoint — only Orchestrator can call this.
    """

    status: str = Field(..., description="Новый статус документа")
    updated_by: Optional[str] = Field(None, description="Кто обновил")


class CheckUniquenessRequest(BaseModel):
    """Request body for POST /registry/documents/check-uniqueness."""

    file_hash_sha256: str = Field(..., description="SHA-256 хэш файла")
    title_hash_sha256: Optional[str] = Field(None, description="SHA-256 хэш названия")


# ---------------------------------------------------------------------------
#  OCR Service
# ---------------------------------------------------------------------------

class OcrProcessRequest(BaseModel):
    """Request body for POST /ocr/process."""

    file_key: str = Field(..., description="Ключ файла")
    draft_id: int = Field(..., description="ID черновика для привязки")
    mode: str = Field("full", description="Режим: preview | full")
    max_pages: Optional[int] = Field(None, description="Максимум страниц для preview")
    options: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные опции")


# ---------------------------------------------------------------------------
#  Parser Service
# ---------------------------------------------------------------------------

class ParserProcessRequest(BaseModel):
    """Request body for POST /parser/process (mode=preview|full)."""

    file_key: str = Field(..., description="Ключ файла")
    draft_id: int = Field(..., description="ID черновика для привязки")
    mode: str = Field("full", description="Режим: preview | full")
    max_pages: Optional[int] = Field(None, description="Максимум страниц для preview")


# ---------------------------------------------------------------------------
#  RAG (Vector Search) Service
# ---------------------------------------------------------------------------

class RagIndexRequest(BaseModel):
    """Request body for POST /rag/index."""

    document_id: str = Field(..., description="ID документа")
    chunks: List[Dict[str, Any]] = Field(..., description="Чанки для индексации")


class RagSearchRequest(BaseModel):
    """Request body for POST /rag/search."""

    query: str = Field(..., description="Поисковый запрос")
    top_k: int = Field(5, description="Количество результатов")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Фильтры поиска")
    search_type: str = Field("hybrid", description="Тип поиска (vector/hybrid/keyword)")


class RagGenerateRequest(BaseModel):
    """Request body for POST /rag/generate."""

    messages: List[Dict[str, str]] = Field(..., description="Сообщения для LLM")
    context_chunks: List[Dict[str, Any]] = Field(..., description="Контекстные чанки")
    model: Optional[str] = Field(None, description="Модель LLM")
    temperature: Optional[float] = Field(None, description="Температура генерации")
