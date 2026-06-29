import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.api.v1.auth import _rate_buckets

# aiosqlite 0.11+ убрал create_function — патч для SQLAlchemy 2.0 совместимости
if not hasattr(aiosqlite.Connection, "create_function"):
    async def _create_function_noop(self, *args, **kwargs):
        pass
    aiosqlite.Connection.create_function = _create_function_noop

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models.models import Role, RolePermission, User

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    _rate_buckets.clear()
    yield
    _rate_buckets.clear()

DEFAULT_ROLES = {
    "engineer": ["documents:read", "search", "history:read"],
    "knowledge_admin": ["documents:read", "documents:write", "search", "history:read"],
    "system_admin": ["users:manage", "roles:manage", "audit:read", "documents:read", "documents:write", "search", "history:read"],
}


@pytest.fixture
async def db():
    engine = create_async_engine(
        _TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def seeded_db(db: AsyncSession) -> AsyncSession:
    roles = {}
    for name, perms in DEFAULT_ROLES.items():
        role = Role(name=name)
        role.permissions = [RolePermission(permission=p) for p in perms]
        db.add(role)
        roles[name] = role

    admin = User(
        email=settings.default_admin_email,
        full_name="Admin User",
        password_hash=hash_password(settings.default_admin_password),
        roles=[roles["system_admin"]],
    )
    db.add(admin)
    await db.commit()
    return db


@pytest.fixture
async def client(db: AsyncSession):
    app.router.on_startup.clear()

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(seeded_db: AsyncSession):
    app.router.on_startup.clear()

    async def override_get_db():
        yield seeded_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/auth/token", json={
            "username": settings.default_admin_email,
            "password": settings.default_admin_password,
        })
        ac.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
        yield ac
    app.dependency_overrides.clear()
