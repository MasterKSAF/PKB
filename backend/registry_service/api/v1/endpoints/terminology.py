from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from ..dependencies.database import get_db
from ..crud import terminology as crud
from ..schemas.terminology import TerminologyRegistryResponse, TerminologyRegistryCreate, TerminologyRegistryUpdate, TerminologyNormalizeResponse

router = APIRouter()

@router.get("/")
async def list_terms(
    term: Optional[str] = None,
    normalized_term: Optional[str] = None,
    context: Optional[str] = None,
    source: Optional[str] = None,
    page: int = Query(1, ge=1), 
    page_size: int = Query(50, ge=1, le=100), 
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    items, total = crud.get_terms(
        db, term=term, normalized_term=normalized_term, context=context, source=source,
        skip=skip, limit=page_size
    )
    validated = [TerminologyRegistryResponse.model_validate(item) for item in items]
    return success_response(
        data=jsonable_encoder(validated),
        meta={"total": total, "page": page, "page_size": page_size}
    )

@router.get("/normalize")
async def normalize_term(term: str, context: Optional[str] = None, db: Session = Depends(get_db)):
    db_term = crud.normalize_term(db, term=term, context=context)
    if db_term:
        resp = TerminologyNormalizeResponse(term=term, normalized_term=db_term.normalized_value)
    else:
        resp = TerminologyNormalizeResponse(term=term, normalized_term=term)
    return success_response(data=jsonable_encoder(resp))

@router.get("/{term_id}")
async def get_term(term_id: UUID, db: Session = Depends(get_db)):
    db_term = crud.get_term(db, term_id=term_id)
    if not db_term:
        raise DomainException(404, "TERM_NOT_FOUND", "Термин не найден")
    return success_response(data=jsonable_encoder(TerminologyRegistryResponse.model_validate(db_term)))

@router.post("/")
async def create_term(term: TerminologyRegistryCreate, db: Session = Depends(get_db)):
    db_term = crud.get_term_by_raw_and_context(db, raw_term=term.term, context=term.context)
    if db_term:
        raise DomainException(409, "DUPLICATE_TERM", "Термин с таким контекстом уже существует")
    new_term = crud.create_term(db, term=term)
    return success_response(
        data=jsonable_encoder(TerminologyRegistryResponse.model_validate(new_term)),
        status_code=201
    )

@router.put("/{term_id}")
async def update_term(term_id: UUID, term_update: TerminologyRegistryUpdate, db: Session = Depends(get_db)):
    db_term = crud.get_term(db, term_id=term_id)
    if not db_term:
        raise DomainException(404, "TERM_NOT_FOUND", "Термин не найден")
    updated = crud.update_term(db, db_term=db_term, term_update=term_update)
    return success_response(data=jsonable_encoder(TerminologyRegistryResponse.model_validate(updated)))

@router.delete("/{term_id}")
async def delete_term(term_id: UUID, db: Session = Depends(get_db)):
    db_term = crud.get_term(db, term_id=term_id)
    if not db_term:
        raise DomainException(404, "TERM_NOT_FOUND", "Термин не найден")
    crud.delete_term(db, term_id)
    return success_response(data={"deleted_id": str(term_id)})

@router.post("/import")
async def import_terminology(mapping: str, file: UploadFile = File(...)):
    # Stub for import
    return success_response(
        data={"inserted": 0, "updated": 0, "errors": []}
    )