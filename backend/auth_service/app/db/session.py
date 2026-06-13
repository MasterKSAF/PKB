from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


database_url = settings.database_url
if database_url.startswith("sqlite://") and not database_url.startswith("sqlite+aiosqlite://"):
    database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_async_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
