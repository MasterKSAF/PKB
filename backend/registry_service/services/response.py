#
#  Forming unified API responses
#

from fastapi.responses import JSONResponse
from typing import Any

class DomainException(Exception):
    """
    Defines a custom domain exception to format errors like:
    {
      "error": {
        "code": "ERROR_CODE",
        "message": "Error message",
        "details": {}
      }
    }
    """
    def __init__(
            self,
            status_code: int,
            error_code: str,
            message: str,
            details: dict | None = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}

def success_response(data: Any, meta: dict | None = None, status_code: int = 200) -> JSONResponse:
    """
    Generates a standardized positive response with a custom status code.
    Format:
    {
        "data": <data>,
        "meta": <meta>
    }
    """
    content = {
        "data": data,
        "meta": meta or {}
    }
    return JSONResponse(status_code=status_code, content=content)
