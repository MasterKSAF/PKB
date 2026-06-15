"""
Draft ORM model.

Local cache of draft metadata. The authoritative source is Registry,
but we keep a lightweight copy here for quick existence/status checks.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Draft(Base):
    """A draft (uploaded file awaiting processing)."""

    __tablename__ = "drafts"

    draft_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    status: Mapped[str] = mapped_column(
        String(16), default="uploaded", nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Draft id={self.draft_id} status={self.status}>"
