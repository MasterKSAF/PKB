"""
Common Pydantic schemas.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail — code is a string per API spec."""

    code: str = Field(..., description="Код ошибки, например DOCUMENT_NOT_FOUND")
    message: str = Field(..., description="Сообщение об ошибке")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Дополнительные детали"
    )


class ErrorResponse(BaseModel):
    """Error response."""

    error: ErrorDetail


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(..., description="Общее количество записей")
    page: int = Field(default=1, description="Текущая страница")
    page_size: int = Field(default=50, description="Записей на странице (max 200)")


class ListResponse(BaseModel, Generic[T]):
    """Generic list response with items and pagination meta."""

    items: List[T]
    meta: PaginationMeta
