from fastapi import APIRouter
from api.v1.schemas import ExternalStatusResponse, SystemStatus
from datetime import datetime, timezone

router = APIRouter()

@router.get("/status", response_model=ExternalStatusResponse)
def external_status():
    return ExternalStatusResponse(
        systems=[
            SystemStatus(
                api_name="meridian",
                status="available",
                last_checked=datetime.now(timezone.utc),
                latency_ms=230
            )
        ]
    )
