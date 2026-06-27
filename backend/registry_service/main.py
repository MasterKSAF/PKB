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
                
                # Load initial data straight after database modifications
                try:
                    from install.load_data import load_data
                    log_event("INFO", "startup", data={"message": "Running initial data load..."})
                    load_data()
                    log_event("INFO", "startup", data={"message": "Initial data load completed successfully"})
                except Exception as load_err:
                    log_event("WARNING", "startup", error=f"Initial data load failed: {str(load_err)}")
            except Exception as create_all_err:
                log_event("WARNING", "startup", error=f"Database table creation failed (might already exist or lack permissions): {str(create_all_err)}")
        except Exception as e:
            log_event("ERROR", "startup", error=f"Database initialization wrapper failed: {str(e)}")
            raise e
    yield

app = FastAPI(lifespan=lifespan)


# ── Trailing slash redirect middleware ──────────────────────────────
@app.middleware("http")
async def remove_trailing_slash(request: Request, call_next):
    """Редирект 307 с trailing slash на URL без слеша (кроме корня)."""
    path = request.url.path
    if len(path) > 1 and path.endswith("/"):
        new_path = path.rstrip("/")
        from starlette.responses import RedirectResponse
        return RedirectResponse(url=str(request.url.replace(path=new_path)), status_code=307)
    return await call_next(request)


import time
import uuid
import traceback
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from services.logger import (
    request_id_var, trace_id_var, span_id_var, draft_id_var,
    document_id_var, version_id_var, user_id_var,
    path_var, method_var, status_var, latency_ms_var,
    log_event
)

@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    
    # Extract headers
    req_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    tr_id = request.headers.get("X-Trace-ID") or request.headers.get("X-Traceid")
    sp_id = request.headers.get("X-Span-ID")
    dr_id = request.headers.get("X-Draft-ID")
    doc_id = request.headers.get("X-Document-ID")
    ver_id = request.headers.get("X-Version-ID")
    usr_id = request.headers.get("X-User-ID")
    
    # Set ContextVars
    token_req = request_id_var.set(req_id)
    token_tr = trace_id_var.set(tr_id)
    token_sp = span_id_var.set(sp_id)
    token_dr = draft_id_var.set(dr_id)
    token_doc = document_id_var.set(doc_id)
    token_ver = version_id_var.set(ver_id)
    
    try:
        usr_id_int = int(usr_id) if usr_id and usr_id.isdigit() else None
    except ValueError:
        usr_id_int = None
    token_usr = user_id_var.set(usr_id_int)
    
    # Set HTTP ContextVars
    token_path = path_var.set(request.url.path)
    token_method = method_var.set(request.method)
    
    try:
        response = await call_next(request)
        
        # Calculate latency
        latency = int((time.perf_counter() - start_time) * 1000)
        latency_ms_var.set(latency)
        status_var.set(response.status_code)
        
        # Add correlation ID to response headers
        response.headers["X-Request-ID"] = req_id
        
        # Automatically log request completion at INFO level
        if request.url.path not in ("/api/v1/health", "/health"):
            log_event("INFO", request.url.path)
            
        return response
    except Exception as e:
        # If an exception happens inside the application, compute latency for log
        latency = int((time.perf_counter() - start_time) * 1000)
        latency_ms_var.set(latency)
        status_var.set(500)
        raise e
    finally:
        # Reset ContextVars
        request_id_var.reset(token_req)
        trace_id_var.reset(token_tr)
        span_id_var.reset(token_sp)
        draft_id_var.reset(token_dr)
        document_id_var.reset(token_doc)
        version_id_var.reset(token_ver)
        user_id_var.reset(token_usr)
        path_var.reset(token_path)
        method_var.reset(token_method)

ERROR_CODE_TRANSLATIONS = {
    "DOCUMENT_NOT_FOUND": "Документ не найден",
    "DRAFT_NOT_FOUND": "Черновик не найден",
    "CLASSIFIER_NOT_FOUND": "Узел классификатора не найден",
    "TERM_NOT_FOUND": "Термин не найден",
    "CATEGORY_NOT_FOUND": "Категория не найдена",
    "CATEGORY_HAS_DOCUMENTS": "Нельзя удалить категорию с привязанными документами",
    "DUPLICATE_CATEGORY_NAME": "Категория с таким именем уже существует",
    "DRAFT_ALREADY_DECIDED": "По черновику уже принято решение",
    "DRAFT_ALREADY_PREVIEWED": "Preview уже выполнен",
    "EMPTY_DOCUMENT": "Документ пустой (0 страниц)",
    "DUPLICATE_CODE": "Код классификатора уже существует",
    "DUPLICATE_DOCUMENT": "Документ с таким бизнес-ключом уже существует",
    "DUPLICATE_TERM": "Термин уже существует",
    "HAS_CHILDREN": "Нельзя удалить узел с дочерними",
    "HAS_DOCUMENTS": "Есть документы, ссылающиеся на код классификатора",
    "CROSS_SYSTEM_PARENT": "Родитель в другой системе классификации",
    "INVALID_DATE_RANGE": "date_from позже date_to или превышен максимальный диапазон",
    "INTERNAL_ERROR": "Внутренняя ошибка сервера",
    "VALIDATION_ERROR": "Ошибка валидации полей"
}

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # If detail is already formatted with "error"
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        error_payload = exc.detail["error"]
        code = error_payload.get("code", "HTTP_ERROR")
        msg = error_payload.get("message", str(exc.detail))
        
        # Translate if needed
        if code in ERROR_CODE_TRANSLATIONS:
            import re
            if not re.search('[а-яА-Я]', msg):
                msg = ERROR_CODE_TRANSLATIONS[code]
            
        # Exclude stack traces or database info from message/details
        if code == "INTERNAL_ERROR":
            msg = "Внутренняя ошибка сервера"
            
        details = error_payload.get("details", {})
        if not isinstance(details, dict):
            details = {}
        
        req_id = request_id_var.get()
        if req_id:
            details["request_id"] = req_id
            
        status_code = exc.status_code
        if code == "VALIDATION_ERROR" and status_code == 422:
            status_code = 400

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "message": msg,
                    "details": details
                }
            }
        )

    
    # Fallback for standard HTTPException
    code = "HTTP_ERROR"
    msg = str(exc.detail)
    if exc.status_code == 404:
        code = "NOT_FOUND"
        msg = "Ресурс не найден"
    elif exc.status_code == 405:
        code = "METHOD_NOT_ALLOWED"
        msg = "Метод не поддерживается"
        
    details = {}
    req_id = request_id_var.get()
    if req_id:
        details["request_id"] = req_id
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": msg,
                "details": details
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        loc = error.get("loc", [])
        field = ".".join(str(l) for l in loc[1:]) if len(loc) > 1 else (str(loc[0]) if loc else "body")
        
        reason = error.get("type", "invalid")
        value = error.get("input")
        if isinstance(value, str) and len(value) > 200:
            value = value[:200] + "..."
            
        ctx = error.get("ctx", {})
        constraint = str(ctx) if ctx else None
        
        errors.append({
            "field": field,
            "reason": reason,
            "value": value,
            "constraint": constraint
        })
        
    details = {
        "validation_errors": errors
    }
    req_id = request_id_var.get()
    if req_id:
        details["request_id"] = req_id
        
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Ошибка валидации полей",
                "details": details
            }
        }
    )

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    details = exc.details or {}
    req_id = request_id_var.get()
    if req_id:
        details["request_id"] = req_id
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": details
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    tb_str = "".join(traceback.format_exception(None, exc, exc.__traceback__))
    log_event("ERROR", request.url.path, error=f"Unhandled internal error: {str(exc)}\n{tb_str}")
    
    details = {}
    req_id = request_id_var.get()
    if req_id:
        details["request_id"] = req_id
        
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Внутренняя ошибка сервера",
                "details": details
            }
        }
    )

app.include_router(v1_routes.routes, prefix="/api/v1", tags=["/api/v1"])

@app.get("/")
def root():
    return {"message": "A list of endpoints is in the API docs directory"}
