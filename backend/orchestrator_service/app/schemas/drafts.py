"""
Pydantic schemas for Drafts API (POST /drafts, GET /drafts, etc.).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DraftCreateResponse(BaseModel):
    """Response for POST /drafts (202 Accepted)."""

    draft_id: int = Field(..., description="ID черновика в Registry")
    task_id: int = Field(..., description="ID задачи в Оркестраторе")
    status: str = Field("uploaded", description="Статус черновика")
    file_hash_sha256: str = Field(..., description="SHA-256 хэш файла")
    file_size_bytes: int = Field(..., description="Размер файла в байтах")
    is_duplicate_file: bool = Field(False, description="Файл является дубликатом")
    is_duplicate_document: bool = Field(
        False, description="Документ с таким бизнес-ключом уже существует"
    )
    title_hash_sha256: Optional[str] = Field(
        None, description="SHA-256 хэш названия (бизнес-ключ)"
    )
    title_key: Optional[str] = Field(
        None, description="Исходная строка конкатенации для title_hash_sha256 (DB-28)"
    )
    created_at: datetime = Field(..., description="Время создания")


class DraftItem(BaseModel):
    """Draft item in list response."""

    draft_id: int = Field(..., description="ID черновика")
    document_key: Optional[str] = Field(None, description="Ключ документа")
    status: str = Field(..., description="Статус черновика")
    file_key: Optional[str] = Field(None, description="Ключ файла")
    created_by: Optional[str] = Field(None, description="Кто создал")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")


class DraftListResponse(BaseModel):
    """Response for GET /drafts."""

    items: List[DraftItem] = Field(default_factory=list, description="Список черновиков")
    total: int = Field(0, description="Всего записей")
    page: int = Field(1, description="Текущая страница")
    page_size: int = Field(50, description="Записей на странице")


class DraftDetailResponse(BaseModel):
    """Full draft information."""

    draft_id: int = Field(..., description="ID черновика")
    document_key: Optional[str] = Field(None, description="Ключ документа")
    file_key: Optional[str] = Field(None, description="Ключ файла")
    status: str = Field(..., description="Статус черновика")
    document_id: Optional[int] = Field(None, description="ID документа после approve")
    version_id: Optional[int] = Field(None, description="ID версии документа")
    is_new_document: bool = Field(True, description="Создан новый документ (true) или новая версия (false)")
    created_by: Optional[str] = Field(None, description="Кто создал")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")


class PreviewMetadata(BaseModel):
    """Preview metadata extracted during preview phase (12 полей)."""

    doc_code: Optional[str] = Field(None, description="Обозначение документа")
    title: Optional[str] = Field(None, description="Название документа")
    document_type: Optional[str] = Field(None, description="Тип документа")
    source_type: Optional[str] = Field(None, description="Тип источника: GOST, GOST_R, OST, RD, TU, ISO, DNV, ASTM, OTHER")
    year: Optional[str] = Field(None, description="Год издания")
    revision: Optional[str] = Field(None, description="Номер редакции")
    era: Optional[str] = Field(None, description="Эпоха: USSR, CIS, RF, CURRENT")
    jurisdiction: Optional[str] = Field(None, description="Юрисдикция: RU, EU, US, NO, INTL")
    mks_oks_code: Optional[str] = Field(None, description="Код МКС/ОКС")
    okstu_code: Optional[str] = Field(None, description="Код ОКСТУ")
    issuing_body: Optional[str] = Field(None, description="Организация-издатель")
    udk_code: Optional[str] = Field(None, description="Код УДК")


class DraftPreviewResponse(BaseModel):
    """Preview metadata for a draft."""

    draft_id: int = Field(..., description="ID черновика")
    preview: PreviewMetadata = Field(default_factory=PreviewMetadata, description="Метаданные превью")


class DraftPreviewStatusResponse(BaseModel):
    """Preview status response (with longpoll support)."""

    draft_id: int = Field(..., description="ID черновика")
    task_id: int = Field(..., description="ID задачи")
    status: str = Field(..., description="Статус превью: processing, completed, failed")
    progress_percent: int = Field(0, description="Прогресс (0–100)")
    preview: Optional[PreviewMetadata] = Field(None, description="Метаданные превью")
    decision_required: bool = Field(False, description="Требуется решение пользователя")


class DecideRequest(BaseModel):
    """Decision request after preview.

    Внешние действия (UI): approve, reject
    Внутренние действия (pipeline): proceed, stop_duplicate, force_new_version
    """

    action: str = Field(..., description="Решение: approve, reject, proceed, stop_duplicate, force_new_version")
    comment: Optional[str] = Field(None, description="Комментарий пользователя")
    metadata_overrides: Optional[Dict[str, Any]] = Field(None, description="Переопределение полей метаданных перед approve")


class DecideResponse(BaseModel):
    """Decision response."""

    draft_id: int = Field(..., description="ID черновика")
    task_id: int = Field(..., description="ID задачи")
    document_id: Optional[int] = Field(None, description="ID созданного документа (после approve)")
    version_id: Optional[int] = Field(None, description="ID версии документа")
    is_new_document: bool = Field(False, description="Создан новый документ или версия")
    status: str = Field(..., description="Новый статус")
    action: str = Field(..., description="Принятое решение")
    message: str = Field(..., description="Сообщение")
