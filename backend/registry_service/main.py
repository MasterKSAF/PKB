#
#   ПКБ "Петробалт" backend API
#
import os

import sys
from pathlib import Path
PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

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

app = FastAPI()

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