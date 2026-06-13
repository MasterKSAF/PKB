#
#   ПКБ "Петробалт" backend API
#
import os

import sys
from pathlib import Path
PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import builtins

import env
from services.response import DomainException, success_response
# Inject into builtins BEFORE importing any routers so it's available globally during module evaluation
builtins.success_response = success_response
builtins.DomainException = DomainException

from api.v1 import routes as v1_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    import sys
    from sqlalchemy import text
    from api.v1.dependencies.database import engine
    from api.v1.models import Base
    from services.logger import log_event

    if "pytest" not in sys.modules:
        try:
            # Create required schemas if they do not exist (only if backend is not sqlite)
            if engine.dialect.name != "sqlite":
                schemas = {table.schema for table in Base.metadata.tables.values() if table.schema}
                try:
                    with engine.connect() as conn:
                        for schema in schemas:
                            if schema == "public":
                                continue
                            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                        conn.commit()
                except Exception as schema_err:
                    log_event("WARNING", "startup", error=f"Schema creation failed (might already exist or lack permissions): {str(schema_err)}")

            try:
                Base.metadata.create_all(bind=engine)
                log_event("INFO", "startup", data={"message": "All database schemas and models created successfully"})
            except Exception as create_all_err:
                log_event("WARNING", "startup", error=f"Database table creation failed (might already exist or lack permissions): {str(create_all_err)}")
        except Exception as e:
            log_event("ERROR", "startup", error=f"Database initialization wrapper failed: {str(e)}")
            raise e
    yield

app = FastAPI(lifespan=lifespan)

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

app.include_router(v1_routes.routes, prefix="/api/v1", tags=["/api/v1"])


@app.get("/")
def root():

    # raise APIException(200, message="bla bla bal", details="{id: 2345}")

    return {"message": "A list of endpoints is in the API docs directory"}