from fastapi import HTTPException
from fastapi.responses import JSONResponse


def api_error(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details or {}},
    )


def error_response(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )
