#
#   Integration Service API
#
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from fastapi import FastAPI

from api.v1 import routes as v1_routes

app = FastAPI()

app.include_router(v1_routes.routes, prefix="/api/v1", tags=["/api/v1"])


@app.get("/")
def root():
    return {"message": "Integration Service API - see API docs for available endpoints"}
