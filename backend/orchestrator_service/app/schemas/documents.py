"""
Pydantic schemas for Documents, Tasks, Pages, Versions, History API.

Matches the orchestrator_service_api.md specification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


# ---------------------------------------------------------------------------
#  Enums
# ---------------------------------------------------------------------------


class SourceType(str, Enum):
    """Source type (type of normative/technical document)."""

    GOST = "GOST"
    GOST_R = "GOST_R"
    OST = "OST"
    RD = "RD"
    TU = "TU"
    ISO = "ISO"
    DNV = "DNV"
    ASTM = "ASTM"
    OTHER = "OTHER"


class DocumentStatus(str, Enum):
    """Document processing status (FSM states)."""

    UPLOADED = "uploaded"
    PREVIEWING = "previewing"
    AWAITING_DECISION = "awaiting_decision"
    PARSING = "parsing"
    VALIDATION = "validation"
    REVIEW_REQUIRED = "review_required"
    READY_FOR_PROMOTION = "ready_for_promotion"
    APPROVED = "approved"
    FAILED = "failed"
    ARCHIVED = "archived"


class Era(str, Enum):
    """Document era."""

    USSR = "USSR"
    CIS = "CIS"
    RF = "RF"
    CURRENT = "CURRENT"


class Jurisdiction(str, Enum):
    """Document jurisdiction."""

    RU = "RU"
    EU = "EU"
    US = "US"
    NO = "NO"
    INTL = "INTL"


class ValidityStatus(str, Enum):
    """Document validity status."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"
    HISTORICAL = "historical"
    DRAFT = "draft"


class ClassificationConfidence(str, Enum):
    """Classification status values."""

    CONFIRMED = "CONFIRMED"
    NOT_USED = "NOT_USED"
    SUSPECTED = "SUSPECTED"
    EXTRACTED = "EXTRACTED"


class DecisionAction(str, Enum):
    """Decision actions after preview."""

    PROCEED = "proceed"
    STOP_DUPLICATE = "stop_duplicate"
    FORCE_NEW_VERSION = "force_new_version"


# Alias for backward compatibility with endpoint imports
DecideAction = DecisionAction


class ReprocessMode(str, Enum):
    """Document reprocessing modes."""

    FULL = "full"
    OCR_ONLY = "ocr_only"
    CHUNKING_ONLY = "chunking_only"
    VALIDATION_ONLY = "validation_only"
    REINDEX = "reindex"


class StepStatusEnum(str, Enum):
    """Processing step status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    BLOCKED = "blocked"


class PipelineStatusEnum(str, Enum):
    """Aggregated pipeline status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


# ---------------------------------------------------------------------------
#  POST /documents  — upload
# ---------------------------------------------------------------------------


class DocumentCreateResponse(BaseModel):
    """Response for document upload (202 Accepted)."""

    task_id: int = Field(..., description="ID задачи (временный идентификатор)")
    version_id: str = Field(..., description="UUID версии файла")
    status: str = Field("uploaded", description="Статус: uploaded")
    file_hash_sha256: str = Field(..., description="SHA-256 хэш файла")
    file_size_bytes: int = Field(..., description="Размер файла в байтах")
    is_duplicate_file: bool = Field(False, description="Файл является дубликатом")
    is_duplicate_document: bool = Field(
        False, description="Документ с таким бизнес-ключом уже существует"
    )
    title_hash_sha256: Optional[str] = Field(
        None, description="SHA-256 хэш названия (бизнес-ключ)"
    )
    created_at: datetime = Field(..., description="Время создания")


# ---------------------------------------------------------------------------
#  POST /tasks/{task_id}/preview
# ---------------------------------------------------------------------------


class TaskPreviewResponse(BaseModel):
    """Response for starting preview phase (202 Accepted)."""

    task_id: int = Field(..., description="ID задачи превью")
    status: str = Field("previewing", description="Статус: previewing")
    estimated_completion: Optional[datetime] = Field(
        None, description="Предполагаемое время завершения"
    )


class DuplicateCandidate(BaseModel):
    """Duplicate candidate found during preview."""

    document_id: str = Field(..., description="UUID найденного дубликата")
    doc_code: Optional[str] = Field(None, description="Обозначение документа-дубликата")
    title: Optional[str] = Field(None, description="Название документа-дубликата")
    similarity: float = Field(..., description="Коэффициент схожести (0..1)")


class PreviewMetadata(BaseModel):
    """Preview metadata extracted during preview phase."""

    doc_code: Optional[str] = Field(None, description="Обозначение документа")
    title: Optional[str] = Field(None, description="Название документа")
    document_type: Optional[str] = Field(None, description="Тип документа")
    year: Optional[str] = Field(None, description="Год издания")
    revision: Optional[str] = Field(None, description="Номер редакции")


class TaskPreviewStatusResponse(BaseModel):
    """Preview status response (completed / processing / failed)."""

    document_id: Optional[str] = Field(None, description="UUID документа")
    status: str = Field(..., description="Статус превью: pending, processing, completed, failed")
    ocr_parser_status: Optional[str] = Field(
        None, description="Статус сервиса распознавания"
    )
    converter_validator_status: Optional[str] = Field(
        None, description="Статус converter-validator"
    )
    preview: Optional[PreviewMetadata] = Field(None, description="Метаданные превью")
    duplicates: List[DuplicateCandidate] = Field(
        default_factory=list, description="Найденные дубликаты"
    )
    decision_required: bool = Field(
        False, description="Требуется решение пользователя"
    )


# ---------------------------------------------------------------------------
#  POST /tasks/{task_id}/decide
# ---------------------------------------------------------------------------


class DecideRequest(BaseModel):
    """Decision request after preview."""

    action: DecisionAction = Field(..., description="Решение: proceed, stop_duplicate, force_new_version")
    comment: Optional[str] = Field(None, description="Комментарий пользователя")


class DecideResponse(BaseModel):
    """Decision response (202 Accepted)."""

    document_id: str = Field(..., description="UUID документа")
    status: str = Field(..., description="Статус: proceeding, stopped, forcing")
    action: DecisionAction = Field(..., description="Принятое решение")
    message: str = Field(..., description="Сообщение")


# ---------------------------------------------------------------------------
#  POST /documents/{doc_id}/versions  +  GET /documents/{doc_id}/versions
# ---------------------------------------------------------------------------


class VersionCreateResponse(BaseModel):
    """Response for creating a new version (202 Accepted)."""

    document_id: str = Field(..., description="UUID документа")
    version_id: str = Field(..., description="UUID новой версии")
    version_number: int = Field(..., description="Номер версии")
    status: str = Field("uploaded", description="Статус загрузки")
    task_id: int = Field(..., description="ID задачи обработки")
    file_hash_sha256: str = Field(..., description="SHA-256 хэш файла")
    is_duplicate_file: bool = Field(False, description="Файл является дубликатом")
    created_at: datetime = Field(..., description="Время создания")


class VersionItem(BaseModel):
    """Single version item."""

    version_id: str = Field(..., description="UUID версии")
    version_number: int = Field(..., description="Номер версии")
    format_code: str = Field(..., description="Код формата (pdf_digital, pdf_scanned, tiff, etc.)")
    format_label: str = Field(..., description="Название формата")
    file_key: str = Field(..., description="CAS-путь к файлу")
    file_hash_sha256: str = Field(..., description="SHA-256 хэш файла")
    size_bytes: int = Field(..., description="Размер в байтах")
    uploaded_at: datetime = Field(..., description="Время загрузки")
    uploaded_by: str = Field(..., description="Кто загрузил")


class VersionMeta(BaseModel):
    """Versions metadata."""

    total: int = Field(0, description="Общее количество версий")


class VersionsListResponse(BaseModel):
    """Response for GET /documents/{doc_id}/versions."""

    document_id: str = Field(..., description="UUID документа")
    versions: List[VersionItem] = Field(default_factory=list, description="Список версий")
    meta: VersionMeta = Field(default_factory=VersionMeta, description="Метаданные")


# ---------------------------------------------------------------------------
#  GET /documents  — list
# ---------------------------------------------------------------------------


class ClassificationStatus(BaseModel):
    """Document classification status."""

    mks_status: Optional[ClassificationConfidence] = Field(
        None, description="Статус МКС: CONFIRMED, NOT_USED, SUSPECTED, EXTRACTED"
    )
    okstu_status: Optional[ClassificationConfidence] = Field(
        None, description="Статус ОКСТУ: CONFIRMED, NOT_USED, SUSPECTED, EXTRACTED"
    )
    udk_code: Optional[str] = Field(None, description="Код УДК")
    extracted_at: Optional[datetime] = Field(
        None, description="Время извлечения классификации"
    )
    extracted_by: Optional[str] = Field(
        None, description="Источник классификации"
    )
    confidence: Optional[float] = Field(None, description="Уверенность (0..1)")


class DocumentSummary(BaseModel):
    """Summary statistics for document list (FSM statuses)."""

    total: int = Field(0, description="Общее количество")
    uploaded: int = Field(0, description="Статус uploaded")
    previewing: int = Field(0, description="Статус previewing")
    awaiting_decision: int = Field(0, description="Статус awaiting_decision")
    parsing: int = Field(0, description="Статус parsing")
    validation: int = Field(0, description="Статус validation")
    review_required: int = Field(0, description="Статус review_required")
    ready_for_promotion: int = Field(0, description="Статус ready_for_promotion")
    approved: int = Field(0, description="Статус approved")
    failed: int = Field(0, description="Статус failed")
    archived: int = Field(0, description="Статус archived")


class DocumentListItem(BaseModel):
    """Document item in list response."""

    document_id: str = Field(..., description="UUID документа")
    title: Optional[str] = Field(None, description="Название документа")
    doc_code: Optional[str] = Field(None, description="Обозначение документа")
    source_type: SourceType = Field(..., description="Тип источника")
    era: Optional[Era] = Field(None, description="Эпоха")
    validity_status: Optional[ValidityStatus] = Field(
        None, description="Статус действия"
    )
    jurisdiction: Optional[Jurisdiction] = Field(None, description="Юрисдикция")
    issuing_body: Optional[str] = Field(None, description="Организация-издатель")
    mks_oks_code: Optional[str] = Field(None, description="Код МКС/ОКС")
    okstu_code: Optional[str] = Field(None, description="Код ОКСТУ")
    classification_status: Optional[ClassificationStatus] = Field(
        None, description="Статус классификации"
    )
    file_hash_sha256: Optional[str] = Field(None, description="SHA-256 хэш файла")
    file_size_bytes: Optional[int] = Field(None, description="Размер файла")
    status: DocumentStatus = Field(..., description="Текущий статус FSM")
    latest_version: int = Field(1, description="Номер последней версии")
    total_versions: int = Field(1, description="Всего версий")
    user_id: str = Field(..., description="UUID пользователя")
    uploaded_by: str = Field(..., description="Кто загрузил")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime = Field(..., description="Время обновления")


class DocumentListResponse(BaseModel):
    """Response for GET /documents."""

    summary: DocumentSummary = Field(..., description="Сводная статистика")
    items: List[DocumentListItem] = Field(..., description="Список документов")
    meta: PaginationMeta = Field(..., description="Метаданные пагинации")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}
# ---------------------------------------------------------------------------


class LatestVersionInfo(BaseModel):
    """Latest version information in document detail."""

    version_id: str = Field(..., description="UUID версии")
    version_number: int = Field(..., description="Номер версии")
    format_code: Optional[str] = Field(None, description="Код формата")
    file_hash_sha256: Optional[str] = Field(None, description="SHA-256 хэш файла")
    size_bytes: Optional[int] = Field(None, description="Размер в байтах")


class DocMetadata(BaseModel):
    """Additional metadata for document detail."""

    year: Optional[str] = Field(None, description="Год издания")
    udc: Optional[str] = Field(None, description="Код УДК")
    tags: List[str] = Field(default_factory=list, description="Теги")


class DocumentDetailResponse(BaseModel):
    """Document detail response with full metadata."""

    document_id: str = Field(..., description="UUID документа")
    title: Optional[str] = Field(None, description="Название документа")
    doc_code: Optional[str] = Field(None, description="Обозначение документа")
    source_type: SourceType = Field(..., description="Тип источника")
    title_hash_sha256: Optional[str] = Field(
        None, description="SHA-256 хэш названия"
    )
    status: DocumentStatus = Field(..., description="Текущий статус FSM")
    era: Optional[Era] = Field(None, description="Эпоха")
    validity_status: Optional[ValidityStatus] = Field(
        None, description="Статус действия"
    )
    jurisdiction: Optional[Jurisdiction] = Field(None, description="Юрисдикция")
    issuing_body: Optional[str] = Field(None, description="Организация-издатель")
    industry_code: Optional[str] = Field(None, description="Код отрасли")
    enterprise_id: Optional[str] = Field(None, description="ID предприятия")
    mks_oks_code: Optional[str] = Field(None, description="Код МКС/ОКС")
    okstu_code: Optional[str] = Field(None, description="Код ОКСТУ")
    classification_status: Optional[ClassificationStatus] = Field(
        None, description="Статус классификации"
    )
    metadata: Optional[DocMetadata] = Field(None, description="Доп. метаданные")
    latest_version: Optional[LatestVersionInfo] = Field(
        None, description="Последняя версия"
    )
    total_versions: int = Field(1, description="Всего версий")
    user_id: str = Field(..., description="UUID пользователя")
    uploaded_by: str = Field(..., description="Кто загрузил")
    created_by: Optional[str] = Field(None, description="Кем создан")
    updated_by: Optional[str] = Field(None, description="Кем обновлён")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime = Field(..., description="Время обновления")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/status  — FSM-aware status
# ---------------------------------------------------------------------------


class OcrParserStep(BaseModel):
    """OCR/Parser step status."""

    status: StepStatusEnum = Field(..., description="Статус этапа")
    pages_processed: Optional[int] = Field(None, description="Обработано страниц")


class ConverterValidatorStep(BaseModel):
    """Converter-validator step status."""

    status: StepStatusEnum = Field(..., description="Статус этапа")
    metadata_extracted: Optional[bool] = Field(
        None, description="Метаданные извлечены"
    )


class DecisionStep(BaseModel):
    """Decision step status."""

    status: str = Field(..., description="Статус: awaiting, completed")
    action: Optional[DecisionAction] = Field(None, description="Принятое решение")


class PreviewPhase(BaseModel):
    """Preview phase details."""

    status: StepStatusEnum = Field(..., description="Статус preview")
    ocr_parser: Optional[OcrParserStep] = Field(None, description="OCR/Parser")
    converter_validator: Optional[ConverterValidatorStep] = Field(
        None, description="Converter-validator"
    )
    decision: Optional[DecisionStep] = Field(None, description="Решение пользователя")


class ParsingStep(BaseModel):
    """Parsing step details."""

    status: StepStatusEnum = Field(..., description="Статус этапа")
    pages_processed: Optional[int] = Field(None, description="Обработано страниц")
    pages_failed: Optional[int] = Field(None, description="Страниц с ошибками")
    avg_confidence: Optional[float] = Field(
        None, description="Средняя уверенность (0..1)"
    )


class ValidationErrorItem(BaseModel):
    """Validation error item."""

    code: str = Field(..., description="Код ошибки")
    section_id: Optional[int] = Field(None, description="ID секции")


class ValidationStep(BaseModel):
    """Validation step details."""

    status: str = Field(..., description="Статус этапа: completed, in_progress, valid, invalid, error")
    errors_found: Optional[int] = Field(None, description="Количество ошибок")
    document_id: Optional[str] = Field(
        None, description="ID документа в валидации"
    )
    errors: Optional[List[ValidationErrorItem]] = Field(
        None, description="Детали ошибок"
    )


class RegistryStep(BaseModel):
    """Registry step status."""

    status: StepStatusEnum = Field(..., description="Статус этапа")


class FormationPipeline(BaseModel):
    """Pipeline 1 — Formation."""

    status: PipelineStatusEnum = Field(..., description="Агрегированный статус")
    preview: Optional[PreviewPhase] = Field(None, description="Preview-фаза")
    parsing: Optional[ParsingStep] = Field(None, description="Парсинг")
    validation: Optional[ValidationStep] = Field(None, description="Валидация")
    registry: Optional[RegistryStep] = Field(None, description="Registry")


class RagIndexingStep(BaseModel):
    """RAG indexing step."""

    status: StepStatusEnum = Field(..., description="Статус")
    chunks_generated: Optional[int] = Field(
        None, description="Сгенерировано чанков"
    )


class IndexationPipeline(BaseModel):
    """Pipeline 2 — Indexation."""

    status: PipelineStatusEnum = Field(..., description="Агрегированный статус")
    rag_indexing: Optional[RagIndexingStep] = Field(
        None, description="RAG indexing"
    )


class PipelinesField(BaseModel):
    """Actual pipeline fields nested under 'pipeline' key."""

    formation: Optional[FormationPipeline] = Field(None, description="Пайплайн 1")
    indexation: Optional[IndexationPipeline] = Field(
        None, description="Пайплайн 2"
    )


class StatusPipelines(BaseModel):
    """Pipelines in status response — wraps under 'pipeline' key per API doc."""

    pipeline: PipelinesField = Field(..., description="Пайплайны в контейнере pipeline")


class ChunkSummary(BaseModel):
    """Summary of chunks generated."""

    sections: int = Field(..., description="Количество секций")
    chunks: int = Field(..., description="Количество чанков")
    embeddings: int = Field(..., description="Количество эмбеддингов")


class DocumentStatusProcessing(BaseModel):
    """Status response — processing state."""

    document_id: str = Field(..., description="UUID документа")
    status: str = Field("processing", description="Статус: processing")
    progress_percent: float = Field(..., description="Прогресс (0..100)")
    steps: StatusPipelines = Field(..., description="Статусы пайплайнов")
    started_at: Optional[datetime] = Field(None, description="Время начала")
    estimated_completion: Optional[datetime] = Field(
        None, description="Предполагаемое завершение"
    )


class DocumentStatusReviewRequired(BaseModel):
    """Status response — review_required state."""

    document_id: str = Field(..., description="UUID документа")
    status: str = Field("review_required", description="Статус: review_required")
    progress_percent: float = Field(..., description="Прогресс (0..100)")
    steps: StatusPipelines = Field(..., description="Статусы пайплайнов")
    chunk_summary: Optional[ChunkSummary] = Field(
        None, description="Сводка по чанкам"
    )


class DocumentStatusReadyForPromotion(BaseModel):
    """Status response — ready_for_promotion state."""

    document_id: str = Field(..., description="UUID документа")
    status: str = Field(
        "ready_for_promotion", description="Статус: ready_for_promotion"
    )
    progress_percent: float = Field(100.0, description="Прогресс")
    steps: StatusPipelines = Field(..., description="Статусы пайплайнов")
    chunk_summary: Optional[ChunkSummary] = Field(
        None, description="Сводка по чанкам"
    )
    started_at: Optional[datetime] = Field(None, description="Время начала")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")


DocumentStatusResponse = Union[
    DocumentStatusProcessing,
    DocumentStatusReviewRequired,
    DocumentStatusReadyForPromotion,
]


# ---------------------------------------------------------------------------
#  POST /documents/{doc_id}/approve
# ---------------------------------------------------------------------------


class ApproveRequest(BaseModel):
    """Approve request body."""

    force: bool = Field(False, description="Принудительный аппрув с warning'ами")
    comment: Optional[str] = Field(None, description="Комментарий")


class ApproveResponse(BaseModel):
    """Approve response (202 Accepted)."""

    document_id: str = Field(..., description="UUID документа")
    status: str = Field("approved", description="Статус: approved")
    promotion_task_id: str = Field(..., description="ID задачи промотирования")
    approved_by: str = Field(..., description="Кто утвердил")
    approved_at: datetime = Field(..., description="Время утверждения")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/history
# ---------------------------------------------------------------------------


class HistoryComment(BaseModel):
    """Comment in history entry."""

    reason: Optional[str] = Field(None, description="Причина перехода")
    details: Optional[str] = Field(None, description="Детали")


class HistoryItem(BaseModel):
    """Single history entry."""

    history_id: str = Field(..., description="UUID записи истории")
    old_status: Optional[str] = Field(None, description="Предыдущий статус")
    new_status: str = Field(..., description="Новый статус")
    comment: Optional[HistoryComment] = Field(None, description="Комментарий")
    changed_by: str = Field(..., description="Кто изменил")
    changed_at: datetime = Field(..., description="Когда изменено")


class DocumentHistoryResponse(BaseModel):
    """Response for GET /documents/{doc_id}/history."""

    document_id: str = Field(..., description="UUID документа")
    history: List[HistoryItem] = Field(..., description="История переходов")
    meta: VersionMeta = Field(..., description="Метаданные (total)")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/file
# ---------------------------------------------------------------------------


class DocumentFileResponse(BaseModel):
    """Response for GET /documents/{doc_id}/file."""

    document_id: str = Field(..., description="UUID документа")
    version_id: str = Field(..., description="UUID версии")
    content_type: str = Field(..., description="MIME-тип")
    file_url: str = Field(..., description="Ссылка на файл")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages
# ---------------------------------------------------------------------------


class PageInfo(BaseModel):
    """Page information."""

    page: int = Field(..., description="Номер страницы")
    width: int = Field(..., description="Ширина в пикселях")
    height: int = Field(..., description="Высота в пикселях")
    ocr_status: str = Field(..., description="Статус OCR")
    confidence: float = Field(..., description="Уверенность (0..1)")
    has_text_layer: bool = Field(..., description="Наличие текстового слоя")


class DocumentPagesResponse(BaseModel):
    """Response for GET /documents/{doc_id}/pages."""

    document_id: str = Field(..., description="UUID документа")
    pages_total: int = Field(..., description="Всего страниц")
    pages: List[PageInfo] = Field(..., description="Список страниц")
    meta: PaginationMeta = Field(..., description="Метаданные пагинации")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages/{page_num}/text
# ---------------------------------------------------------------------------


class PageBlockDetail(BaseModel):
    """Block detail in page text response."""

    number: int = Field(..., description="Порядковый номер блока")
    type: str = Field(
        ...,
        description=(
            "Тип блока: paragraph, heading, table, list, image, formula, headerFooter"
        ),
    )
    bbox: List[float] = Field(
        ..., description="Координаты [x1, y1, x2, y2] в норм. единицах (0..1)"
    )
    content: Union[str, Dict[str, Any], None] = Field(
        None, description="Содержимое (текст или структура для таблиц)"
    )
    confidence: Optional[float] = Field(None, description="Уверенность (0..1)")


class TextContent(BaseModel):
    """Table content structure."""

    columns: List[str] = Field(default_factory=list, description="Заголовки колонок")
    rows: List[List[str]] = Field(default_factory=list, description="Строки таблицы")


class PageTextResponse(BaseModel):
    """Response for GET /documents/{doc_id}/pages/{page_num}/text."""

    document_id: str = Field(..., description="UUID документа")
    page: int = Field(..., description="Номер страницы")
    width: int = Field(0, description="Ширина страницы в пикселях")
    height: int = Field(0, description="Высота страницы в пикселях")
    blocks: List[PageBlockDetail] = Field(
        default_factory=list, description="Блоки на странице"
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages/{page_num}/preview
# ---------------------------------------------------------------------------


class PreviewBlock(BaseModel):
    """Block in preview response."""

    number: int = Field(..., description="Порядковый номер блока")
    type: str = Field(..., description="Тип блока")
    bbox: List[float] = Field(..., description="Координаты [x1, y1, x2, y2]")
    content: Optional[str] = Field(None, description="Содержимое")


class PagePreviewResponse(BaseModel):
    """Response for GET /documents/{doc_id}/pages/{page_num}/preview."""

    document_id: str = Field(..., description="UUID документа")
    page: int = Field(..., description="Номер страницы")
    image_url: str = Field(..., description="URL изображения")
    blocks: List[PreviewBlock] = Field(
        default_factory=list, description="Блоки на странице"
    )
    text_layer: Optional[str] = Field(None, description="Полный текст страницы")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/parameters
# ---------------------------------------------------------------------------


class ParameterRange(BaseModel):
    """Range of parameter values."""

    min: Optional[float] = Field(None, description="Минимальное значение")
    max: Optional[float] = Field(None, description="Максимальное значение")
    min_inclusive: Optional[bool] = Field(None, description="Включительно min")
    max_inclusive: Optional[bool] = Field(None, description="Включительно max")


class ParameterItem(BaseModel):
    """Single extracted parameter."""

    symbol: str = Field(..., description="Обозначение параметра")
    description: str = Field(..., description="Описание")
    unit: Optional[str] = Field(None, description="Единица измерения")
    value: Optional[float] = Field(None, description="Числовое значение")
    range: Optional[ParameterRange] = Field(None, description="Диапазон значений")
    source_clause: Optional[str] = Field(None, description="Пункт документа")
    source_page: Optional[int] = Field(None, description="Страница документа")


class DocumentParametersResponse(BaseModel):
    """Response for GET /documents/{doc_id}/parameters."""

    document_id: str = Field(..., description="UUID документа")
    parameters: List[ParameterItem] = Field(
        default_factory=list, description="Извлечённые параметры"
    )
    total: int = Field(0, description="Всего параметров")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/errors
# ---------------------------------------------------------------------------


class ProcessingError(BaseModel):
    """Processing error item."""

    error_id: str = Field(..., description="UUID ошибки")
    stage: str = Field(..., description="Этап: upload, ocr, parsing, indexing")
    page: Optional[int] = Field(None, description="Номер страницы")
    error_code: str = Field(..., description="Код ошибки")
    error_message: str = Field(..., description="Сообщение об ошибке")
    severity: str = Field(..., description="Уровень: warning, error")
    retry_attempt: int = Field(0, description="Номер попытки")
    timestamp: datetime = Field(..., description="Время ошибки")


class DocumentErrorsResponse(BaseModel):
    """Response for GET /documents/{doc_id}/errors."""

    errors: List[ProcessingError] = Field(..., description="Список ошибок")
    meta: PaginationMeta = Field(..., description="Метаданные пагинации")


# ---------------------------------------------------------------------------
#  DELETE /documents/{doc_id}
# ---------------------------------------------------------------------------


class DocumentDeleteResponse(BaseModel):
    """Response for DELETE /documents/{doc_id} (soft-delete)."""

    document_id: str = Field(..., description="UUID документа")
    deleted_at: datetime = Field(..., description="Время удаления")


# ---------------------------------------------------------------------------
#  POST /documents/{doc_id}/reprocess
# ---------------------------------------------------------------------------


class ReprocessRequest(BaseModel):
    """Request body for reprocess."""

    mode: ReprocessMode = Field(
        ReprocessMode.FULL, description="Режим переобработки"
    )
    options: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Доп. опции: engine (paddleocr, tesseract), "
            "language (ru, en), pages (1-5)"
        ),
    )


class ReprocessResponse(BaseModel):
    """Response for reprocess (202 Accepted)."""

    mode: ReprocessMode = Field(..., description="Режим переобработки")
    document_id: str = Field(..., description="UUID документа")
    user_id: str = Field(..., description="UUID пользователя")
    task_id: str = Field(..., description="ID задачи")
    status: str = Field(..., description="Статус")
    created_at: datetime = Field(..., description="Время создания")


# ---------------------------------------------------------------------------
#  GET /documents/queue
# ---------------------------------------------------------------------------


class QueueStepStatus(BaseModel):
    """Step status in queue item."""

    status: str = Field(..., description="Статус этапа")


class QueuePipelineField(BaseModel):
    """Queue pipeline fields nested under 'pipeline' key."""

    formation: Dict[str, Any] = Field(
        default_factory=dict, description="Статусы этапов формирования"
    )
    indexation: Dict[str, Any] = Field(
        default_factory=dict, description="Статусы этапов индексации"
    )


class QueuePipelineSteps(BaseModel):
    """Pipeline steps in queue item — wraps under 'pipeline' key per API doc."""

    pipeline: QueuePipelineField = Field(..., description="Пайплайны в контейнере pipeline")


class QueueItem(BaseModel):
    """Item in processing queue."""

    document_id: str = Field(..., description="UUID документа")
    title: Optional[str] = Field(None, description="Название документа")
    doc_code: Optional[str] = Field(None, description="Обозначение документа")
    source_type: SourceType = Field(..., description="Тип источника")
    status: DocumentStatus = Field(..., description="Текущий статус FSM")
    progress_percent: float = Field(0.0, description="Прогресс (0..100)")
    current_step: Optional[str] = Field(
        None, description="Текущий шаг: validation, parsing, indexing"
    )
    steps: Optional[QueuePipelineSteps] = Field(
        None, description="Статусы этапов"
    )
    user_id: str = Field(..., description="UUID пользователя")
    uploaded_by: str = Field(..., description="Кто загрузил")
    created_at: datetime = Field(..., description="Время создания")
    started_at: Optional[datetime] = Field(None, description="Время начала")
    estimated_completion: Optional[datetime] = Field(
        None, description="Предполагаемое завершение"
    )


class QueueMeta(BaseModel):
    """Queue metadata."""

    total_in_queue: int = Field(0, description="Всего в очереди")
    page: int = Field(1, description="Номер страницы")
    page_size: int = Field(50, description="Записей на странице")


class DocumentQueueResponse(BaseModel):
    """Response for GET /documents/queue."""

    queue: List[QueueItem] = Field(..., description="Очередь обработки")
    meta: QueueMeta = Field(..., description="Метаданные")


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages/{page_num}  — view (binary image)
# ---------------------------------------------------------------------------


class PageViewResponse(BaseModel):
    """Page view response metadata (the actual response is binary)."""

    pass
