import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .db import init_db, wait_for_db
from .routes.health import router as health_router
from .routes.chat import router as chat_router
from .routes.text import router as text_router
from .routes.projects import router as projects_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await wait_for_db()
    await init_db()
    yield


app = FastAPI(title="PKB Query Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc), "details": {}}},
    )


app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(text_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"service": "query-service", "docs": "/docs"}
