"""
ExternalTask ORM model.

Tracks async tasks submitted to external services (Parser, RAG Builder).
The BackgroundTaskPoller polls this table and updates status asynchronously.
"""

from datetime import datetime

from typing import Any, Dict, Optional

from sqlalchemy import BigInteger, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# PK-колонки: BigInteger для PostgreSQL, Integer для SQLite
_BIGINT_PK = BigInteger().with_variant(Integer, "sqlite")


class ExternalTask(Base):
    """An async task submitted to an external service."""

    __tablename__ = "external_tasks"

    __table_args__ = {"schema": "pipeline"}

    id: Mapped[int] = mapped_column(
        _BIGINT_PK, primary_key=True, autoincrement=True
    )
    orchestrator_task_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    step_name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # full_ocr, rag_index, reprocess, activate
    external_service: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # parser, rag_builder
    external_task_id: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True
    )  # pending -> completed / failed
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None
    )
    error_message: Mapped[str] = mapped_column(
        Text, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<ExternalTask id={self.id} service={self.external_service} "
            f"ext_id={self.external_task_id} status={self.status}>"
        )
