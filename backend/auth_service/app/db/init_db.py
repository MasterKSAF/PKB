from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, engine
from app.models.models import Role, RolePermission, User


DEFAULT_ROLES = {
    "engineer": ["documents:read", "search", "history:read"],
    "knowledge_admin": ["documents:read", "documents:write", "search", "history:read"],
    "system_admin": ["users:manage", "roles:manage", "audit:read", "documents:read", "documents:write", "search"],
}


async def init_db(db: AsyncSession) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    for name, permissions in DEFAULT_ROLES.items():
        result = await db.execute(select(Role).where(Role.name == name))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=name)
            role.permissions = [RolePermission(permission=p) for p in permissions]
            db.add(role)

    await db.commit()

    result = await db.execute(select(User).where(User.email == settings.default_admin_email))
    admin = result.scalar_one_or_none()
    if not admin:
        role_result = await db.execute(select(Role).where(Role.name == "system_admin"))
        admin_role = role_result.scalar_one()
        admin = User(
            email=settings.default_admin_email,
            full_name="System Administrator",
            password_hash=hash_password(settings.default_admin_password),
            roles=[admin_role],
        )
        db.add(admin)
        await db.commit()
