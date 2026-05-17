from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from ..dependencies.database import get_db
from ..crud import terminology as crud
from ..schemas.terminology import TerminologyRegistryPurgatoryResponse, TerminologyRegistryPurgatoryCreate, TerminologyRegistryPurgatoryUpdate, TerminologyRegistryPurgatoryNormalizeResponse

router = APIRouter()

@router.get("/")
async def list_terms(
    raw_term: Optional[str] = None,
    normalized_term: Optional[str] = None,
    term_type: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    page: int = Query(1, ge=1), 
    page_size: int = Query(50, ge=1, le=100), 
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    items, total = crud.get_terms(
        db, raw_term=raw_term, normalized_term=normalized_term, term_type=term_type, is_blocked=is_blocked,
        skip=skip, limit=page_size
    )
    validated = [TerminologyRegistryPurgatoryResponse.model_validate(item) for item in items]
    return success_response(
        data=jsonable_encoder(validated),
        meta={"total": total, "page": page, "page_size": page_size}
    )

@router.get("/normalize")
async def normalize_term(term: str, db: Session = Depends(get_db)):
    db_term = crud.normalize_term(db, term=term)
    if db_term:
        resp = TerminologyRegistryPurgatoryNormalizeResponse(
            raw_term=db_term.raw_term,
            standard_term=db_term.standard_term,
            normalized_value=db_term.normalized_value,
            term_type=db_term.term_type,
            is_blocked=db_term.is_blocked
        )
    else:
        resp = TerminologyRegistryPurgatoryNormalizeResponse(
            raw_term=term,
            standard_term=term,
            normalized_value=term,
            term_type="unknown",
            is_blocked=False
        )
    return success_response(data=jsonable_encoder(resp))

@router.get("/{term_id}")
async def get_term(term_id: UUID, db: Session = Depends(get_db)):
    db_term = crud.get_term(db, term_id=term_id)
    if not db_term:
        raise DomainException(404, "TERM_NOT_FOUND", "Термин не найден")
    return success_response(data=jsonable_encoder(TerminologyRegistryPurgatoryResponse.model_validate(db_term)))

@router.post("/")
async def create_term(term: TerminologyRegistryPurgatoryCreate, db: Session = Depends(get_db)):
    db_term = crud.get_terms(db, raw_term=term.raw_term)[0] if crud.get_terms(db, raw_term=term.raw_term)[0] else None
    if db_term:
        raise DomainException(409, "DUPLICATE_TERM", "Термин уже существует")
    new_term = crud.create_term(db, term=term)
    return success_response(
        data=jsonable_encoder(TerminologyRegistryPurgatoryResponse.model_validate(new_term)),
        status_code=201
    )

@router.put("/{term_id}")
async def update_term(term_id: UUID, term_update: TerminologyRegistryPurgatoryUpdate, db: Session = Depends(get_db)):
    db_term = crud.get_term(db, term_id=term_id)
    if not db_term:
        raise DomainException(404, "TERM_NOT_FOUND", "Термин не найден")
    updated = crud.update_term(db, db_term=db_term, term_update=term_update)
    return success_response(data=jsonable_encoder(TerminologyRegistryPurgatoryResponse.model_validate(updated)))

@router.patch("/{term_id}")
async def patch_term(term_id: UUID, term_update: dict, db: Session = Depends(get_db)):
    db_term = crud.get_term(db, term_id=term_id)
    if not db_term:
        raise DomainException(404, "TERM_NOT_FOUND", "Термин не найден")
    updated = crud.update_term(db, db_term=db_term, term_update=term_update, is_patch=True)
    return success_response(data=jsonable_encoder(TerminologyRegistryPurgatoryResponse.model_validate(updated)))

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