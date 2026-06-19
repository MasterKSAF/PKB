"""
Task and TaskStep ORM models.

Tracks execution of pipeline tasks and their steps.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DraftNotification(Base):
    """Quality notifications from Parser/OCR services for a draft."""

    __tablename__ = "draft_notifications"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    draft_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    service: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # "ocr" | "parser"
    code: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "low_quality", "missing_pages", etc.
    message: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="warning"
    )  # "critical" | "warning" | "info"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<DraftNotification id={self.id} task={self.task_id} "
            f"code={self.code} severity={self.severity}>"
        )


class Task(Base):
    """A pipeline task (formation) for a draft/document."""

    __tablename__ = "tasks"

    __table_args__ = (
        UniqueConstraint("draft_id", "pipeline_type", name="uq_tasks_draft_pipeline"),
        UniqueConstraint("document_id", "pipeline_type", name="uq_tasks_document_pipeline"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    draft_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    document_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True
    )
    version_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    pipeline_type: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )  # "formation" | "indexation" | "reprocess"

    # Task status and stage
    status: Mapped[str] = mapped_column(
        String(16), default="active", nullable=False, index=True
    )  # "active" | "completed" | "failed"
    pipeline_stage: Mapped[str] = mapped_column(
        String(16), default="upload", nullable=False
    )  # "upload" | "preview" | "decision" | "full" | "registry" | "indexation"
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    priority: Mapped[int] = mapped_column(Integer, default=5)

    current_step_name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)

    # Trace ID for request tracing
    trace_id: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True
    )

    # Preview result tracking
    full_completed: Mapped[bool] = mapped_column(Boolean, default=False)

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
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    steps: Mapped[list["TaskStep"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["DraftNotification"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id} draft={self.draft_id} "
            f"type={self.pipeline_type} status={self.status}>"
        )


class TaskStep(Base):
    """Log of a single step execution within a pipeline task."""

    __tablename__ = "task_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "upload", "preview_ocr", "preview_converter", "full_ocr", "full_converter", "registry_creation"
    step_index: Mapped[int] = mapped_column(Integer, default=0)
    service_name: Mapped[str] = mapped_column(
        String(64), default="", nullable=False
    )  # "Orchestrator", "OCR Service", "Parser Service", "Converter-validator", "Registry"

    # "pending" | "running" | "completed" | "failed" | "compensated"
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)

    # JSON data containers (use JSONB on PostgreSQL for production)
    # Note: For PostgreSQL production, use sqlalchemy.dialects.postgresql.JSONB
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

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
    task: Mapped["Task"] = relationship(back_populates="steps")

    def __repr__(self) -> str:
        return (
            f"<TaskStep id={self.id} task={self.task_id} "
            f"step={self.step_name} status={self.status}>"
        )
