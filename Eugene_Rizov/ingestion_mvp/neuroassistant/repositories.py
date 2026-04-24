"""Repositories for documents and ingestion runs (in-memory MVP).

MongoDB or other persistence can be plugged in later by implementing the same
interface. For MVP we keep everything in-memory, but still write event logs and
artifacts to the local filesystem.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime

from neuroassistant.domain import Document
from neuroassistant.domain import DocumentStatus
from neuroassistant.domain import IngestionRun
from neuroassistant.domain import PipelineError


@dataclass(slots=True)
class RepoSnapshot:
    documents_count: int
    runs_count: int
    created_at: datetime


class InMemoryRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._documents: dict[str, Document] = {}
        self._runs: dict[str, IngestionRun] = {}
        self._runs_by_document: dict[str, list[str]] = {}

    def upsert_document(self, document: Document) -> None:
        with self._lock:
            self._documents[document.document_id] = document

    def get_document(self, document_id: str) -> Document | None:
        with self._lock:
            return self._documents.get(document_id)

    def list_documents(self) -> list[Document]:
        with self._lock:
            return list(self._documents.values())

    def create_run(self, run: IngestionRun) -> None:
        with self._lock:
            self._runs[run.ingestion_id] = run
            self._runs_by_document.setdefault(run.document_id, []).append(
                run.ingestion_id,
            )
            doc = self._documents.get(run.document_id)
            if doc is not None:
                doc.latest_ingestion_id = run.ingestion_id
                self._documents[doc.document_id] = doc

    def get_run(self, ingestion_id: str) -> IngestionRun | None:
        with self._lock:
            return self._runs.get(ingestion_id)

    def list_runs_for_document(self, document_id: str) -> list[IngestionRun]:
        with self._lock:
            ids = list(self._runs_by_document.get(document_id, []))
            return [self._runs[i] for i in ids if i in self._runs]

    def set_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
    ) -> None:
        with self._lock:
            doc = self._documents.get(document_id)
            if doc is None:
                return
            doc.status = status
            self._documents[document_id] = doc

    def set_run_status(
        self,
        ingestion_id: str,
        status: DocumentStatus,
    ) -> None:
        with self._lock:
            run = self._runs.get(ingestion_id)
            if run is None:
                return
            run.status = status
            self._runs[ingestion_id] = run

    def add_run_error(self, ingestion_id: str, error: PipelineError) -> None:
        with self._lock:
            run = self._runs.get(ingestion_id)
            if run is None:
                return
            run.errors.append(error)
            self._runs[ingestion_id] = run

    def snapshot(self) -> RepoSnapshot:
        with self._lock:
            return RepoSnapshot(
                documents_count=len(self._documents),
                runs_count=len(self._runs),
                created_at=datetime.now(UTC),
            )

