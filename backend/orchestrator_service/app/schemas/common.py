"""
Common Pydantic schemas.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail."""
    code: int
    code_name: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: ErrorDetail


class PaginationParams(BaseModel):
    """Pagination parameters."""
    limit: int = 20
    offset: int = 0
