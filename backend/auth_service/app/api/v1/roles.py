from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.db.session import get_db
from app.schemas.schemas import RoleCreate, RoleListResponse, RolePublic
from app.services.audit_service import create_audit_event
from app.services.user_service import create_role, list_roles

router = APIRouter(prefix="/roles", tags=["roles"])


def to_public(role) -> RolePublic:
    return RolePublic(
        role_id=role.role_id,
        name=role.name,
        permissions=sorted([p.permission for p in role.permissions]),
        created_at=role.created_at,
    )


@router.get("", response_model=RoleListResponse)
async def roles(db: AsyncSession = Depends(get_db), current_user = Depends(require_permission("roles:manage"))):
    roles_list = await list_roles(db)
    return {"roles": [to_public(r) for r in roles_list]}


@router.post("", response_model=RolePublic, status_code=status.HTTP_201_CREATED)
async def create(payload: RoleCreate, request: Request, db: AsyncSession = Depends(get_db), current_user = Depends(require_permission("roles:manage"))):
    try:
        role = await create_role(db, payload.name, payload.permissions)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await create_audit_event(db, "role.create", current_user.user_id, "role", role.role_id, {"name": role.name}, request.client.host if request.client else None)
    return to_public(role)
