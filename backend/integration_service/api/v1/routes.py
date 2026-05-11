#
# All routes
#

from fastapi import APIRouter
from .endpoints import common

routes = APIRouter()

routes.include_router(common.router, prefix="/integration", tags=["integration"])

