import httpx
from fastapi import APIRouter
from sqlalchemy import text
from ..config import get_settings
from ..db import AsyncSessionLocal

router = APIRouter()


@router.get("/system/health")
@router.get("/health")
async def health():
    settings = get_settings()
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    llm_status = "ok"
    if not settings.MOCK_LLM_ENABLED:
        try:
            headers = {"Content-Type": "application/json"}
            if settings.LLM_API_KEY:
                headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.LLM_API_URL}/models", headers=headers)
                if resp.status_code != 200:
                    llm_status = f"unavailable (HTTP {resp.status_code})"
        except httpx.ConnectError:
            llm_status = "unavailable (connect_error)"
        except httpx.TimeoutException:
            llm_status = "unavailable (timeout)"
        except Exception as e:
            llm_status = f"unavailable ({e})"
    else:
        llm_status = "mock"

    return {
        "status": "ok",
        "db": db_status,
        "llm": llm_status,
        "llm_model": settings.LLM_MODEL,
        "llm_url": settings.LLM_API_URL,
        "service": "query-service",
    }


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
