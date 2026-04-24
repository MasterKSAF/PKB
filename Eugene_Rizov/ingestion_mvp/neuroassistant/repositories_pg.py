"""Postgres-backed repository for ingestion metadata."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import select
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column

from neuroassistant.db import Base
from neuroassistant.domain import ClassificationResult
from neuroassistant.domain import Document
from neuroassistant.domain import DocumentMetadata
from neuroassistant.domain import DocumentStatus
from neuroassistant.domain import IngestionRun
from neuroassistant.domain import PipelineError


class DocumentRow(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    filename: Mapped[str] = mapped_column(Text())
    content_type: Mapped[str | None] = mapped_column(Text(), nullable=True)
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer())
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON())
    status: Mapped[str] = mapped_column(String(64))
    latest_ingestion_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RunRow(Base):
    __tablename__ = "ingestion_runs"

    ingestion_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(64))
    classification: Mapped[dict[str, Any] | None] = mapped_column(JSON(), nullable=True)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSON())
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON())


class PostgresRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_document(self, document: Document) -> None:
        row = self._session.get(DocumentRow, document.document_id)
        payload = document.model_dump(mode="json")
        if row is None:
            row = DocumentRow(
                document_id=payload["document_id"],
                created_at=document.created_at,
                filename=document.filename,
                content_type=document.content_type,
                sha256=document.sha256,
                size_bytes=document.size_bytes,
                metadata_json=document.metadata.model_dump(mode="json"),
                status=document.status.value,
                latest_ingestion_id=document.latest_ingestion_id,
            )
            self._session.add(row)
        else:
            row.filename = document.filename
            row.content_type = document.content_type
            row.sha256 = document.sha256
            row.size_bytes = document.size_bytes
            row.metadata_json = document.metadata.model_dump(mode="json")
            row.status = document.status.value
            row.latest_ingestion_id = document.latest_ingestion_id
        self._session.commit()

    def get_document(self, document_id: str) -> Document | None:
        row = self._session.get(DocumentRow, document_id)
        if row is None:
            return None
        return Document(
            document_id=row.document_id,
            created_at=row.created_at,
            filename=row.filename,
            content_type=row.content_type,
            sha256=row.sha256,
            size_bytes=row.size_bytes,
            metadata=DocumentMetadata(**row.metadata_json),
            status=DocumentStatus(row.status),
            latest_ingestion_id=row.latest_ingestion_id,
        )

    def list_documents(self) -> list[Document]:
        rows = list(self._session.execute(select(DocumentRow)).scalars().all())
        return [self.get_document(r.document_id) for r in rows if r.document_id]

    def create_run(self, run: IngestionRun) -> None:
        row = self._session.get(RunRow, run.ingestion_id)
        classification = (
            run.classification.model_dump(mode="json")
            if run.classification is not None
            else None
        )
        errors = [e.model_dump(mode="json") for e in run.errors]
        if row is None:
            row = RunRow(
                ingestion_id=run.ingestion_id,
                document_id=run.document_id,
                created_at=run.created_at,
                status=run.status.value,
                classification=classification,
                errors=errors,
                metrics=run.metrics,
            )
            self._session.add(row)
        else:
            row.status = run.status.value
            row.classification = classification
            row.errors = errors
            row.metrics = run.metrics
        # Update doc latest run pointer best-effort
        doc = self._session.get(DocumentRow, run.document_id)
        if doc is not None:
            doc.latest_ingestion_id = run.ingestion_id
        self._session.commit()

    def get_run(self, ingestion_id: str) -> IngestionRun | None:
        row = self._session.get(RunRow, ingestion_id)
        if row is None:
            return None
        classification = (
            ClassificationResult(**row.classification)
            if row.classification is not None
            else None
        )
        errors = [PipelineError(**e) for e in (row.errors or [])]
        return IngestionRun(
            ingestion_id=row.ingestion_id,
            document_id=row.document_id,
            created_at=row.created_at,
            status=DocumentStatus(row.status),
            classification=classification,
            errors=errors,
            metrics=row.metrics or {},
        )

    def list_runs_for_document(self, document_id: str) -> list[IngestionRun]:
        rows = list(
            self._session.execute(
                select(RunRow).where(RunRow.document_id == document_id),
            ).scalars()
        )
        return [self.get_run(r.ingestion_id) for r in rows if r.ingestion_id]

    def set_document_status(self, document_id: str, status: DocumentStatus) -> None:
        row = self._session.get(DocumentRow, document_id)
        if row is None:
            return
        row.status = status.value
        self._session.commit()

    def set_run_status(self, ingestion_id: str, status: DocumentStatus) -> None:
        row = self._session.get(RunRow, ingestion_id)
        if row is None:
            return
        row.status = status.value
        self._session.commit()

    def add_run_error(self, ingestion_id: str, error: PipelineError) -> None:
        row = self._session.get(RunRow, ingestion_id)
        if row is None:
            return
        current = row.errors or []
        current.append(error.model_dump(mode="json"))
        row.errors = current
        self._session.commit()


def now_utc() -> datetime:
    return datetime.now(UTC)

