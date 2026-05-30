from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExportSchema(BaseModel):
    export_id: str
    document_id: str
    external_id: str
    status: str
    sent_at: Optional[datetime] = None
    response_message: str

    model_config = {
        'extra': 'ignore',
    }
