from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session
from api.v1.database import get_db
from api.v1.models import FileRecord
from api.v1.schemas import FileResponse, DeleteFileResponse, ErrorResponse
import uuid
import os
import shutil
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add integration_service root to sys.path so config can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config import settings

router = APIRouter()

@router.post("/upload", response_model=FileResponse, status_code=201, responses={400: {"model": ErrorResponse}})
def upload_file(
    file: UploadFile = File(...), 
    related_document_id: str = Form(None),
    db: Session = Depends(get_db)
):
    dirs = settings.STORAGE_DIRECTORIES
    main_dir = dirs[0]
    
    file_id = f"file-{uuid.uuid4().hex}"
    mime_type = file.content_type or "application/octet-stream"
    
    file_path = str(main_dir / file_id)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    size = os.path.getsize(file_path)
    url = f"/files/{file_id}"
    
    now = datetime.now(timezone.utc)
    
    record = FileRecord(
        file_id=file_id,
        filename=file.filename,
        size=size,
        mime_type=mime_type,
        url=url,
        uploaded_at=now,
        related_document_id=related_document_id,
        storage_path=file_path
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record

def _find_file(record: FileRecord) -> str:
    dirs = settings.STORAGE_DIRECTORIES
    for d in dirs:
        path = d / record.file_id
        if path.exists():
            return str(path)
    return None

@router.get("/{file_id}")
def get_file(file_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.file_id == file_id).first()
    if not record:
        return HTTPException(status_code=404, detail={"error": {"code": "FILE_NOT_FOUND", "message": "Файл не найден", "details": {}}})
        
    actual_path = _find_file(record)
    if not actual_path:
        return HTTPException(status_code=404, detail={"error": {"code": "FILE_NOT_FOUND", "message": "Физический файл не найден", "details": {}}})
         
    return FastAPIFileResponse(actual_path, media_type=record.mime_type, filename=record.filename)

@router.delete("/{file_id}", response_model=DeleteFileResponse)
def delete_file(file_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.file_id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail={"error": {"code": "FILE_NOT_FOUND", "message": "Файл не найден", "details": {}}})
        
    actual_path = _find_file(record)
    if actual_path:
        os.remove(actual_path)
        
    db.delete(record)
    db.commit()
    
    return DeleteFileResponse(file_id=file_id, deleted_at=datetime.now(timezone.utc))

@router.get("/{file_id}/info", response_model=FileResponse)
def get_file_info(file_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.file_id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail={"error": {"code": "FILE_NOT_FOUND", "message": "Файл не найден", "details": {}}})
    return record
