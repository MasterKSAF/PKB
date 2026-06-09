import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import AuditEvent


def create_audit_event(
    db: Session,
    action: str,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditEvent:
    if details is not None:
        details = json.loads(json.dumps(details, ensure_ascii=False))

    event = AuditEvent(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
