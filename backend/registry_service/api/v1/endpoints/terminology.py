from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from ..dependencies.database import get_db
from ..crud import terminology as crud
from ..schemas.terminology import TerminologyRegistryResponse, TerminologyRegistryCreate

router = APIRouter()

@router.get("/", response_model=list[TerminologyRegistryResponse])
async def list_terms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    terms = crud.get_terms(db, skip=skip, limit=limit)
    return terms

@router.post("/", response_model=TerminologyRegistryResponse)
async def create_term(term: TerminologyRegistryCreate, db: Session = Depends(get_db)):
    return crud.create_term(db, term=term)

@router.get("/{term_id}", response_model=TerminologyRegistryResponse)
async def get_term(term_id: UUID, db: Session = Depends(get_db)):
    db_term = crud.get_term(db, term_id=term_id)
    if db_term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    return db_term