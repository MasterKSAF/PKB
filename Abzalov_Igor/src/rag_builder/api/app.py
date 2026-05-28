from fastapi import FastAPI
from loguru import logger

from rag_builder.api.middleware import RequestContextMiddleware
from rag_builder.api.v1.rag_routes import router as rag_router
from rag_builder.core.config import settings
from rag_builder.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    logger.info("Application startup init")
    app = FastAPI(title="RAG Builder Service", version="0.1.0")
    app.add_middleware(RequestContextMiddleware)
    app.include_router(rag_router, prefix=settings.api_prefix)
    logger.info("Application startup ready")
    return app
