from fastapi import APIRouter
from sqlalchemy import text
from ..db import AsyncSessionLocal

router = APIRouter()


@router.get("/health")
async def health():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unavailable"
    return {"status": "ok", "db": db_status, "service": "query-service"}
