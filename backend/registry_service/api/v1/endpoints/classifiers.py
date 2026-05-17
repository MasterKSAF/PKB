from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Optional
from ..dependencies.database import get_db
from ..crud import classifier as crud
from ..schemas.classifier import ClassifierRegistryResponse, ClassifierRegistryCreate, ClassifierRegistryUpdate, ClassifierTreeResponse

router = APIRouter()

@router.get("/")
async def list_classifiers(
    code: Optional[str] = None,
    full_name: Optional[str] = None,
    doc_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    language: Optional[str] = None,
    is_thematic: Optional[bool] = None,
    parent_code: Optional[str] = None,
    page: int = Query(1, ge=1), 
    page_size: int = Query(50, ge=1, le=100), 
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    items, total = crud.get_classifiers(
        db, code=code, full_name=full_name, doc_type=doc_type, 
        jurisdiction=jurisdiction, language=language, 
        is_thematic=is_thematic, parent_code=parent_code,
        skip=skip, limit=page_size
    )
    validated = [ClassifierRegistryResponse.model_validate(item) for item in items]
    return success_response(
        data=jsonable_encoder(validated),
        meta={"total": total, "page": page, "page_size": page_size}
    )

@router.get("/tree")
async def get_classifier_tree(
    root_code: Optional[str] = None,
    max_depth: int = Query(10, ge=1),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    roots, total = crud.get_classifier_tree(db, root_code=root_code, max_depth=max_depth, search=search)
    validated = [ClassifierTreeResponse.model_validate(item) for item in roots]
    return success_response(
        data=jsonable_encoder(validated),
        meta={"total": total, "max_depth_reached": False}
    )

@router.get("/{code}")
async def get_classifier(code: str, db: Session = Depends(get_db)):
    db_classifier = crud.get_classifier(db, code=code)
    if not db_classifier:
        raise DomainException(404, "CLASSIFIER_NOT_FOUND", f"Узел классификатора с кодом {code} не найден")
    return success_response(data=jsonable_encoder(ClassifierTreeResponse.model_validate(db_classifier)))

@router.post("/")
async def create_classifier(classifier: ClassifierRegistryCreate, db: Session = Depends(get_db)):
    db_classifier = crud.get_classifier(db, code=classifier.code)
    if db_classifier:
        raise DomainException(409, "DUPLICATE_CODE", "Код классификатора уже существует")
    new_classifier = crud.create_classifier(db, classifier=classifier)
    return success_response(
        data=jsonable_encoder(ClassifierRegistryResponse.model_validate(new_classifier)),
        status_code=201
    )

@router.put("/{code}")
async def update_classifier(code: str, classifier_update: ClassifierRegistryUpdate, db: Session = Depends(get_db)):
    db_classifier = crud.get_classifier(db, code=code)
    if not db_classifier:
        raise DomainException(404, "CLASSIFIER_NOT_FOUND", "Узел классификатора не найден")
    updated = crud.update_classifier(db, db_classifier=db_classifier, classifier_update=classifier_update)
    return success_response(data=jsonable_encoder(ClassifierRegistryResponse.model_validate(updated)))

@router.patch("/{code}")
async def patch_classifier(code: str, classifier_update: ClassifierRegistryUpdate, db: Session = Depends(get_db)):
    return await update_classifier(code, classifier_update, db)

@router.delete("/{code}")
async def delete_classifier(code: str, force: bool = False, db: Session = Depends(get_db)):
    db_classifier = crud.get_classifier(db, code=code)
    if not db_classifier:
        raise DomainException(404, "CLASSIFIER_NOT_FOUND", "Узел классификатора не найден")
    
    if not force and db_classifier.classifier_registry_reverse_purgatory:
        raise DomainException(409, "HAS_CHILDREN", f"Нельзя удалить: узел имеет {len(db_classifier.classifier_registry_reverse_purgatory)} дочерних. Используйте force=true")
        
    crud.delete_classifier(db, code)
    return success_response(data={"deleted_code": code})

@router.post("/import")
async def import_classifiers(mapping: str, file: UploadFile = File(...)):
    # Stub for import
    return success_response(
        data={"inserted": 0, "updated": 0, "errors": []}
    )