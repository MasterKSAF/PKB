"""
Orchestrator Service - FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings


def create_application() -> FastAPI:
    """Create FastAPI application instance."""
    application = FastAPI(
        title="Orchestrator Service API",
        description="Единая точка входа для публичного API Нейроассистента ПКБ",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    application.include_router(
        api_router,
        prefix=settings.API_V1_PREFIX
    )
    
    @application.get("/")
    async def root():
        return {
            "service": "orchestrator-service",
            "version": settings.APP_VERSION,
            "docs": "/docs"
        }
    
    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
