"""
Document ORM model — core entity for pipeline state management.

Tracks FSM state across Pipeline 1 (formation) and Pipeline 2 (indexation).
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    """Document entity — central state holder for the pipeline FSM."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    file_hash_sha256: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    title_hash_sha256: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=True)
    minio_ref: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    # FSM state (Pipeline 1)
    status: Mapped[str] = mapped_column(
        String(32),
        default="uploaded",
        index=True,
        nullable=False,
    )

    # Pipeline 2 state
    pipeline_2_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )

    # Metadata
    source_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    doc_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    era: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    issuing_body: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Error tracking
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Pipeline 1 step results (JSON as text for simplicity; use JSONB in production)
    ocr_result_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    parser_result_ref: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )
    converter_result_ref: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )
    registry_result_ref: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    pipeline_jobs: Mapped[list["PipelineJob"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    step_logs: Mapped[list["PipelineStepLog"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} status={self.status}>"
