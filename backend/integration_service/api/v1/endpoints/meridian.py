from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.v1.database import get_db
from api.v1.models import ExportRecord
from api.v1.schemas import ExportRequest, ExportResponse
import uuid
from datetime import datetime, timezone

router = APIRouter()

@router.post("/export", response_model=ExportResponse)
def export_meridian(req: ExportRequest, db: Session = Depends(get_db)):
    export_id = f"exp-{uuid.uuid4().hex[:6]}"
    external_id = f"mer-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    
    record = ExportRecord(
        export_id=export_id,
        document_id=req.document_id,
        external_id=external_id,
        status="sent",
        sent_at=now,
        response_message="Принято"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record
