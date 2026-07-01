import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def get_session_factory() -> async_sessionmaker:
    return AsyncSessionLocal


_PG_MIGRATIONS = (
    "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS summary TEXT",
    "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS summarized_until_message_id BIGINT",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS warnings JSON",
    "ALTER TABLE chat_sources ADD COLUMN IF NOT EXISTS citation_index INTEGER",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS completion_tokens INTEGER",
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    "CREATE INDEX IF NOT EXISTS ix_chat_messages_content_trgm ON chat_messages USING gin (content gin_trgm_ops)",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS content_tsv tsvector",
    "CREATE INDEX IF NOT EXISTS ix_chat_messages_content_tsv ON chat_messages USING gin (content_tsv)",
    """
    CREATE OR REPLACE FUNCTION chat_messages_tsv_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        NEW.content_tsv := to_tsvector('russian', coalesce(NEW.content, ''));
        RETURN NEW;
    END;
    $$
    """,
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = 'trg_chat_messages_tsv'
        ) THEN
            CREATE TRIGGER trg_chat_messages_tsv
            BEFORE INSERT OR UPDATE OF content ON chat_messages
            FOR EACH ROW EXECUTE FUNCTION chat_messages_tsv_update();
        END IF;
    END $$
    """,
)


async def init_db() -> None:
    from sqlalchemy import text
    from . import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if conn.dialect.name == "postgresql":
            for stmt in _PG_MIGRATIONS:
                await conn.execute(text(stmt))


async def wait_for_db(retries: int = 10, delay: float = 2.0) -> None:
    from sqlalchemy import text
    for attempt in range(retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return
        except Exception:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay)
