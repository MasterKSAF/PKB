#
# registry router
#

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def registry():
    return {"message": "all registry is here"}