from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, engine
from app.models.models import Role, RolePermission, User


DEFAULT_ROLES = {
    "engineer": ["documents:read", "search", "history:read"],
    "knowledge_admin": ["documents:read", "documents:write", "search", "history:read"],
    "system_admin": ["users:manage", "roles:manage", "audit:read", "documents:read", "documents:write", "search"],
}


def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=engine)

    for name, permissions in DEFAULT_ROLES.items():
        role = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
        if not role:
            role = Role(name=name)
            role.permissions = [RolePermission(permission=p) for p in permissions]
            db.add(role)

    db.commit()

    admin = db.execute(select(User).where(User.email == settings.default_admin_email)).scalar_one_or_none()
    if not admin:
        admin_role = db.execute(select(Role).where(Role.name == "system_admin")).scalar_one()
        admin = User(
            email=settings.default_admin_email,
            full_name="System Administrator",
            password_hash=hash_password(settings.default_admin_password),
            roles=[admin_role],
        )
        db.add(admin)
        db.commit()
