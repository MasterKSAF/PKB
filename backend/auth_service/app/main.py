from fastapi import FastAPI

from app.api.v1 import audit, auth, internal, roles, users
from app.core.config import settings
from app.core.logger import get_logger, setup_logging
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Сервис аутентификации, ролей, доступов и аудита.",
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(internal.router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup():
    async with AsyncSessionLocal() as db:
        await init_db(db)
    logger.info("Auth Service started (env=%s)", settings.env)


@app.get("/health")
@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
