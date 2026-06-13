from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.schemas.schemas import UserCreate, UserListItem, UserListResponse, UserPublic, UserUpdate
from app.services.audit_service import create_audit_event
from app.services.user_service import create_user, get_permissions, get_user_by_id, list_users, role_names, update_user

router = APIRouter(prefix="/admin/users", tags=["admin/users"])


def to_public(user) -> UserPublic:
    return UserPublic(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        roles=role_names(user),
        permissions=get_permissions(user),
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=UserListResponse)
async def users(
    role: str | None = None,
    search: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission("users:manage")),
):
    found, total = await list_users(db, role, search, limit, offset)
    return {
        "users": [
            UserListItem(
                user_id=u.user_id,
                email=u.email,
                full_name=u.full_name,
                roles=role_names(u),
                is_active=u.is_active,
                created_at=u.created_at,
            ) for u in found
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create(payload: UserCreate, request: Request, db: AsyncSession = Depends(get_db), current_user = Depends(require_permission("users:manage"))):
    try:
        user = await create_user(db, payload.email, payload.full_name, payload.password, payload.roles)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await create_audit_event(db, "user.create", current_user.user_id, "user", user.user_id, {"email": user.email}, request.client.host if request.client else None)
    return to_public(user)


@router.get("/{user_id}", response_model=UserPublic)
async def get_one(user_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.user_id != user_id and "users:manage" not in get_permissions(current_user):
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return to_public(user)


@router.patch("/{user_id}", response_model=UserPublic)
async def update_one(user_id: str, payload: UserUpdate, request: Request, db: AsyncSession = Depends(get_db), current_user = Depends(require_permission("users:manage"))):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    try:
        updated = await update_user(db, user, **payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await create_audit_event(db, "user.update", current_user.user_id, "user", user_id, payload.model_dump(exclude_unset=True), request.client.host if request.client else None)
    return to_public(updated)


@router.delete("/{user_id}")
async def deactivate(user_id: str, request: Request, db: AsyncSession = Depends(get_db), current_user = Depends(require_permission("users:manage"))):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    updated = await update_user(db, user, is_active=False)
    await create_audit_event(db, "user.deactivate", current_user.user_id, "user", user_id, None, request.client.host if request.client else None)
    return {"user_id": updated.user_id, "is_active": updated.is_active, "deactivated_at": updated.updated_at}
