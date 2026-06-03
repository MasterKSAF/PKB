"""
Pipeline job and step log ORM models.

Tracks execution of pipeline steps, retries, and compensation actions.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PipelineJob(Base):
    """A run of a pipeline (formation or indexation) for a document."""

    __tablename__ = "pipeline_jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    pipeline_type: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )  # "formation" | "indexation" | "reprocess"

    # FSM for job itself
    status: Mapped[str] = mapped_column(
        String(16),
        default="queued",
        nullable=False,
        index=True,
    )  # "queued" | "running" | "completed" | "failed" | "compensating" | "dead"

    priority: Mapped[int] = mapped_column(Integer, default=5)

    current_step_name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Concurrency guard
    locked_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    locked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="pipeline_jobs")
    step_logs: Mapped[list["PipelineStepLog"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<PipelineJob id={self.id} doc={self.document_id} "
            f"type={self.pipeline_type} status={self.status}>"
        )


class PipelineStepLog(Base):
    """Log of a single step execution within a pipeline job."""

    __tablename__ = "pipeline_step_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pipeline_jobs.id"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    step_name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "ocr", "parser", "converter", "registry", "rag_index"
    step_index: Mapped[int] = mapped_column(Integer, default=0)

    # "pending" | "running" | "success" | "failed" | "compensated"
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)

    # Payload references (refs to stored JSON, not the JSON itself)
    input_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    output_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Error details
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    job: Mapped["PipelineJob"] = relationship(back_populates="step_logs")
    document: Mapped["Document"] = relationship(back_populates="step_logs")

    def __repr__(self) -> str:
        return (
            f"<PipelineStepLog id={self.id} job={self.job_id} "
            f"step={self.step_name} status={self.status}>"
        )
