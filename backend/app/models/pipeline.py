"""
Pipeline job and step log ORM models.

Tracks execution of pipeline steps, retries, and compensation actions.
Now refactored to Task / TaskStep (was PipelineJob / PipelineStepLog).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Task(Base):
    """A run of a pipeline (formation or indexation) for a draft document."""

    __tablename__ = "tasks"
    __table_args__ = {"schema": "pipeline"}

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    draft_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True
    )
    # Will be filled after approval
    document_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    pipeline_type: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )  # "formation" | "indexation" | "reprocess"

    # FSM for task itself: "active" | "completed" | "failed"
    status: Mapped[str] = mapped_column(
        String(16),
        default="active",
        nullable=False,
        index=True,
    )

    # Pipeline stage: "upload" -> "preview" -> "decision" -> "full" -> "registry" -> "indexation"
    pipeline_stage: Mapped[str] = mapped_column(
        String(16), default="upload", nullable=False
    )

    progress_percent: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

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
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Whether the full pipeline (including indexation) has completed
    full_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    steps: Mapped[list["TaskStep"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id} draft={self.draft_id} "
            f"type={self.pipeline_type} status={self.status}>"
        )


class TaskStep(Base):
    """Log of a single step execution within a task."""

    __tablename__ = "task_steps"
    __table_args__ = {"schema": "pipeline"}

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pipeline.tasks.id"), nullable=False, index=True
    )
    step_name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "upload", "preview_ocr", "preview_converter", "full_ocr", "full_converter", "registry_creation"
    service_name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "Orchestrator", "OCR Service", "Parser Service", "Converter-validator", "Registry"
    step_index: Mapped[int] = mapped_column(Integer, default=0)

    # "pending" | "running" | "completed" | "failed" | "compensated"
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)

    # Payload stored as JSON (use JSONB instead for PostgreSQL for better performance)
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    output_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )

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
