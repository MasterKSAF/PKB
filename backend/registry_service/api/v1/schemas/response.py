from __future__ import annotations

from typing import Any, Dict, List, Optional, TypeVar, Generic

from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int


class ResponseMeta(BaseModel):
    total: int
    page: int
    page_size: int
    max_depth_reached: Optional[bool] = None


class ListResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta


class SingleResponse(BaseModel, Generic[T]):
    data: T


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
