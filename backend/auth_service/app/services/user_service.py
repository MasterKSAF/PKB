from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.models.models import Role, RolePermission, User


def get_permissions(user: User) -> list[str]:
    permissions: set[str] = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.permission)
    return sorted(permissions)


def role_names(user: User) -> list[str]:
    return sorted([role.name for role in user.roles])


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(
        select(User).where(User.email == email).options(selectinload(User.roles).selectinload(Role.permissions))
    ).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.execute(
        select(User).where(User.user_id == user_id).options(selectinload(User.roles).selectinload(Role.permissions))
    ).scalar_one_or_none()


def get_roles_by_names(db: Session, names: list[str]) -> list[Role]:
    return list(db.execute(select(Role).where(Role.name.in_(names))).scalars().all())


def create_user(db: Session, email: str, full_name: str, password: str, roles: list[str]) -> User:
    existing = get_user_by_email(db, email)
    if existing:
        raise ValueError("Пользователь с таким email уже существует")

    role_objects = get_roles_by_names(db, roles)
    if len(role_objects) != len(set(roles)):
        raise ValueError("Одна или несколько ролей не найдены")

    user = User(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        roles=role_objects,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return get_user_by_id(db, user.user_id)


def update_user(db: Session, user: User, **kwargs) -> User:
    roles = kwargs.pop("roles", None)
    for key, value in kwargs.items():
        if value is not None:
            setattr(user, key, value)

    if roles is not None:
        role_objects = get_roles_by_names(db, roles)
        if len(role_objects) != len(set(roles)):
            raise ValueError("Одна или несколько ролей не найдены")
        user.roles = role_objects

    db.commit()
    db.refresh(user)
    return get_user_by_id(db, user.user_id)


def create_role(db: Session, name: str, permissions: list[str]) -> Role:
    existing = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
    if existing:
        raise ValueError("Роль уже существует")

    role = Role(name=name)
    role.permissions = [RolePermission(permission=p) for p in sorted(set(permissions))]
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def list_roles(db: Session) -> list[Role]:
    return list(db.execute(select(Role).options(selectinload(Role.permissions))).scalars().all())


def list_users(db: Session, role: str | None, search: str | None, limit: int, offset: int):
    query = select(User).options(selectinload(User.roles).selectinload(Role.permissions))
    count_query = select(func.count(User.user_id))

    if role:
        query = query.join(User.roles).where(Role.name == role)
        count_query = count_query.join(User.roles).where(Role.name == role)

    if search:
        pattern = f"%{search.lower()}%"
        query = query.where(func.lower(User.email).like(pattern) | func.lower(User.full_name).like(pattern))
        count_query = count_query.where(func.lower(User.email).like(pattern) | func.lower(User.full_name).like(pattern))

    total = db.execute(count_query).scalar_one()
    users = list(db.execute(query.order_by(User.created_at.desc()).limit(limit).offset(offset)).scalars().unique().all())
    return users, total
