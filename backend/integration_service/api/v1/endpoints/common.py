from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any

router = APIRouter()


def success_response(data: Any, meta: dict | None = None, status_code: int = 200) -> JSONResponse:
    content = {
        "data": data,
        "meta": meta or {}
    }
    return JSONResponse(status_code=status_code, content=content)


@router.get("/")
async def health_check():
    return success_response(data={"status": "ok", "service": "integration"})
