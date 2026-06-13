from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logger import get_logger
from app.core.security import hash_password
from app.models.models import Role, RolePermission, User

logger = get_logger(__name__)


class DuplicateError(Exception):
    pass


def get_permissions(user: User) -> list[str]:
    permissions: set[str] = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.permission)
    return sorted(permissions)


def role_names(user: User) -> list[str]:
    return sorted([role.name for role in user.roles])


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email).options(selectinload(User.roles).selectinload(Role.permissions))
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(
        select(User).where(User.user_id == user_id).options(selectinload(User.roles).selectinload(Role.permissions))
    )
    return result.scalar_one_or_none()


async def get_roles_by_names(db: AsyncSession, names: list[str]) -> list[Role]:
    result = await db.execute(select(Role).where(Role.name.in_(names)))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, email: str, full_name: str, password: str, roles: list[str]) -> User:
    existing = await get_user_by_email(db, email)
    if existing:
        logger.warning("Attempt to create duplicate user: %s", email)
        raise DuplicateError("Пользователь с таким email уже существует")

    role_objects = await get_roles_by_names(db, roles)
    if len(role_objects) != len(set(roles)):
        logger.warning("Unknown roles requested during user creation: %s", roles)
        raise ValueError("Одна или несколько ролей не найдены")

    user = User(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        roles=role_objects,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("User created: %s", email)
    return await get_user_by_id(db, user.user_id)


async def update_user(db: AsyncSession, user: User, **kwargs) -> User:
    roles = kwargs.pop("roles", None)
    for key, value in kwargs.items():
        if value is not None:
            setattr(user, key, value)

    if roles is not None:
        role_objects = await get_roles_by_names(db, roles)
        if len(role_objects) != len(set(roles)):
            logger.warning("Unknown roles during user update for %s: %s", user.user_id, roles)
            raise ValueError("Одна или несколько ролей не найдены")
        user.roles = role_objects

    await db.commit()
    await db.refresh(user)
    logger.info("User updated: %s", user.user_id)
    return await get_user_by_id(db, user.user_id)


async def create_role(db: AsyncSession, name: str, permissions: list[str]) -> Role:
    result = await db.execute(select(Role).where(Role.name == name))
    existing = result.scalar_one_or_none()
    if existing:
        logger.warning("Attempt to create duplicate role: %s", name)
        raise DuplicateError("Роль уже существует")

    role = Role(name=name)
    role.permissions = [RolePermission(permission=p) for p in sorted(set(permissions))]
    db.add(role)
    await db.commit()
    await db.refresh(role, ["permissions"])
    logger.info("Role created: %s", name)
    return role


async def list_roles(db: AsyncSession) -> list[Role]:
    result = await db.execute(select(Role).options(selectinload(Role.permissions)))
    return list(result.scalars().all())


async def list_users(db: AsyncSession, role: str | None, search: str | None, limit: int, offset: int):
    query = select(User).options(selectinload(User.roles).selectinload(Role.permissions))
    count_query = select(func.count(User.user_id))

    if role:
        query = query.join(User.roles).where(Role.name == role)
        count_query = count_query.join(User.roles).where(Role.name == role)

    if search:
        pattern = f"%{search.lower()}%"
        query = query.where(func.lower(User.email).like(pattern) | func.lower(User.full_name).like(pattern))
        count_query = count_query.where(func.lower(User.email).like(pattern) | func.lower(User.full_name).like(pattern))

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    result = await db.execute(query.order_by(User.created_at.desc()).limit(limit).offset(offset))
    users = list(result.scalars().unique().all())
    return users, total
