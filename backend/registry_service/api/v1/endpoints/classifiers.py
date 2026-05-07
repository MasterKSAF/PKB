#
# registry classifiers router
#

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def classifiers():
    return {"message": "all registry classifiers are here"}