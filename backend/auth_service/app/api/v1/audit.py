from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.db.session import get_db
from app.models.models import AuditEvent
from app.schemas.schemas import AuditListResponse

router = APIRouter(prefix="/admin/audit", tags=["admin/audit"])


@router.get("", response_model=AuditListResponse)
async def audit(
    user_id: str | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("audit:read")),
):
    query = select(AuditEvent)
    count_query = select(func.count(AuditEvent.event_id))

    if user_id:
        query = query.where(AuditEvent.user_id == user_id)
        count_query = count_query.where(AuditEvent.user_id == user_id)
    if action:
        query = query.where(AuditEvent.action == action)
        count_query = count_query.where(AuditEvent.action == action)
    if date_from:
        query = query.where(AuditEvent.timestamp >= date_from)
        count_query = count_query.where(AuditEvent.timestamp >= date_from)
    if date_to:
        query = query.where(AuditEvent.timestamp <= date_to)
        count_query = count_query.where(AuditEvent.timestamp <= date_to)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    result = await db.execute(query.order_by(AuditEvent.timestamp.desc()).limit(limit).offset(offset))
    events = list(result.scalars().all())
    return {"events": events, "total": total}
