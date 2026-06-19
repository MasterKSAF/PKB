from fastapi import APIRouter
from sqlalchemy import text
from ..db import AsyncSessionLocal

router = APIRouter()


@router.get("/system/health")
@router.get("/health")
async def health():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unavailable"
    return {"status": "ok", "db": db_status, "service": "query-service"}


@router.get("/health/live")
async def health_live():
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "db": str(e)},
        )
