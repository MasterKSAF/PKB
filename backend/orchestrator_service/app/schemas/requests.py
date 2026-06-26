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
    status: str = Field("uploaded", description="Статус черновика")
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

    title: str = Field(..., description="Название документа для проверки уникальности")
    doc_code: Optional[str] = Field(None, description="Регистрационный номер")
    era: Optional[str] = Field(None, description="Эпоха: USSR, CIS, RF, CURRENT")
    source_type: Optional[str] = Field(None, description="Тип источника: GOST, GOST_R, OST, RD, TU, ISO, DNV, ASTM, OTHER")
    file_size_bytes: Optional[int] = Field(None, description="Размер файла в байтах")


# ---------------------------------------------------------------------------
#  OCR Service
# ---------------------------------------------------------------------------

class OcrProcessRequest(BaseModel):
    """Request body for POST /ocr/process."""

    task_id: int = Field(..., description="ID задачи оркестратора")
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

    task_id: int = Field(..., description="ID задачи оркестратора")
    file_key: str = Field(..., description="Ключ файла")
    draft_id: int = Field(..., description="ID черновика для привязки")
    mode: str = Field("full", description="Режим: preview | full")
    max_pages: Optional[int] = Field(None, description="Максимум страниц для preview")


# ---------------------------------------------------------------------------
#  RAG (Vector Search) Service — RS-6/RS-7 контракты (20.06)
# ---------------------------------------------------------------------------

class RagBuildRequest(BaseModel):
    """Request body for POST /rag/build.

    Соответствует спецификации rag_builder_service_api.md (RS-6/RS-7):
    - document_id + sections[] (типизированная структура секций)
    - section_id стабилен, старый индекс удаляется перед переиндексацией
    - chunk_id — технический retrieval ID, не用于 цитирования
    """

    document_id: str = Field(..., description="ID документа в Registry")
    sections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Секции документа для индексации: section_id, parent_id, clause, title, level, path, page (1-based), bbox (0..1), type, content",
    )
    protected_spans: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Защищённые span'ы: {section_id, start_offset, end_offset}",
    )
    options: Optional[Dict[str, Any]] = Field(
        None,
        description="Параметры индексации: strategy (semantic_1024)",
    )


class RagBuildResponse(BaseModel):
    """Response from POST /rag/build (202 Accepted)."""

    document_id: str = Field(..., description="ID документа")
    task_id: Optional[str] = Field(None, description="ID задачи")
    indexing_txn_id: Optional[str] = Field(None, description="ID транзакции индексации")
    status: str = Field("indexing", description="Статус: indexing")


class RagSearchRequest(BaseModel):
    """Request body for POST /rag/search.

    RS-6: только query + valid_at + filters.
    search_type, top_k, rerank, version_id — ТОЛЬКО из app_settings.
    """

    query: str = Field(..., description="Поисковый запрос")
    valid_at: Optional[str] = Field(
        None, description="Дата, на которую документы active (YYYY-MM-DD)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Фильтры: document_type[], category_ids[], document_ids[]",
    )


class RagGenerateRequest(BaseModel):
    """Request body for POST /rag/generate."""

    messages: List[Dict[str, str]] = Field(..., description="Сообщения для LLM")
    context_chunks: List[Dict[str, Any]] = Field(..., description="Контекстные чанки")
    model: Optional[str] = Field(None, description="Модель LLM")
    temperature: Optional[float] = Field(None, description="Температура генерации")
