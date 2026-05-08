from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies.database import get_db
from ..crud import classifier as crud
from ..schemas.classifier import ClassifierRegistryResponse, ClassifierRegistryCreate

router = APIRouter()

@router.get("/", response_model=list[ClassifierRegistryResponse])
async def list_classifiers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    classifiers = crud.get_classifiers(db, skip=skip, limit=limit)
    return classifiers

@router.post("/", response_model=ClassifierRegistryResponse)
async def create_classifier(classifier: ClassifierRegistryCreate, db: Session = Depends(get_db)):
    db_classifier = crud.get_classifier(db, code=classifier.code)
    if db_classifier:
        raise HTTPException(status_code=400, detail="Classifier code already exists")
    return crud.create_classifier(db, classifier=classifier)

@router.get("/{code}", response_model=ClassifierRegistryResponse)
async def get_classifier(code: str, db: Session = Depends(get_db)):
    db_classifier = crud.get_classifier(db, code=code)
    if db_classifier is None:
        raise HTTPException(status_code=404, detail="Classifier not found")
    return db_classifier