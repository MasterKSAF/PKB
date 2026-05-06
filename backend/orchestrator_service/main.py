#
#   ПКБ "Петробалт" backend API
#

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from api.v1.v1_routes import routes as v1_routes

from services.response import APIException


app = FastAPI()

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

app.include_router(v1_routes, prefix="/api/v1", tags=["/api/v1"])


@app.get("/")
def root():

    # raise APIException(200, message="bla bla bal", details="{id: 2345}")

    return {"message": "A list of endpoints is in the API root directory's README.md file @github"}
