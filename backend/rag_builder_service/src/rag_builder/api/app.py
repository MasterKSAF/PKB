from contextlib import asynccontextmanager
import asyncio
import sys
from collections.abc import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from rag_builder.api.middleware import RequestContextMiddleware
from rag_builder.api.v1.health_routes import router as health_router
from rag_builder.api.v1.rag_routes import router as rag_router
from rag_builder.core.config import settings
from rag_builder.core.logging import configure_logging
from rag_builder.db.migrations import upgrade_to_head, validate_startup_migrations
from rag_builder.db.session import engine


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("Application startup init")
        if "pytest" not in sys.modules:
            await asyncio.to_thread(upgrade_to_head)
            await validate_startup_migrations(engine)
        logger.info("Application startup ready")
        yield
        logger.info("Application shutdown")

    configure_logging()
    app = FastAPI(title="RAG Builder Service", version=settings.app_version, lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(rag_router, prefix=settings.api_prefix)
    return app
