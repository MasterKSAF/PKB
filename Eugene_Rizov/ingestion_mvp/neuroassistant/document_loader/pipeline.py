"""Ingestion pipeline (validate -> store -> classify -> preprocess)."""

from __future__ import annotations

import json
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from neuroassistant.classifier.classifier import classify_file
from neuroassistant.domain import ClassificationResult
from neuroassistant.domain import Document
from neuroassistant.domain import DocumentMetadata
from neuroassistant.domain import DocumentStatus
from neuroassistant.domain import IngestionRun
from neuroassistant.domain import PipelineError
from neuroassistant.domain import PipelineEvent
from neuroassistant.domain import PipelineEventStatus
from neuroassistant.domain import PipelineScope
from neuroassistant.domain import PipelineStage
from neuroassistant.preprocessing.preprocess import preprocess_image
from neuroassistant.preprocessing.preprocess import preprocess_pdf_to_images
from neuroassistant.repositories import InMemoryRepository
from neuroassistant.storage.artifacts import LocalArtifactStorage
from neuroassistant.utils import sha256_bytes
from neuroassistant.utils import timer


@dataclass(frozen=True, slots=True)
class IngestionResult:
    document: Document
    run: IngestionRun


class IngestionPipeline:
    def __init__(
        self,
        repo: InMemoryRepository,
        storage: LocalArtifactStorage,
        max_bytes: int = 50 * 1024 * 1024,
    ) -> None:
        self._repo = repo
        self._storage = storage
        self._max_bytes = max_bytes

    def ingest_bytes(
        self,
        filename: str,
        content_type: str | None,
        data: bytes,
        metadata: DocumentMetadata | None = None,
    ) -> IngestionResult:
        """Full synchronous ingestion (register + process)."""
        result = self.register_bytes(
            filename=filename,
            content_type=content_type,
            data=data,
            metadata=metadata,
        )
        self.run_existing(result.run.ingestion_id)
        stored_doc = self._repo.get_document(result.document.document_id)
        stored_run = self._repo.get_run(result.run.ingestion_id)
        return IngestionResult(
            document=stored_doc or result.document,
            run=stored_run or result.run,
        )

    def register_bytes(
        self,
        filename: str,
        content_type: str | None,
        data: bytes,
        metadata: DocumentMetadata | None = None,
    ) -> IngestionResult:
        """Register document and store raw bytes; does not run processing."""
        metadata = metadata or DocumentMetadata()
        document_id = _new_id("doc")
        ingestion_id = _new_id("ing")
        sha256 = sha256_bytes(data)

        doc = Document(
            document_id=document_id,
            filename=Path(filename).name,
            content_type=content_type,
            sha256=sha256,
            size_bytes=len(data),
            metadata=metadata,
            status=DocumentStatus.received,
            latest_ingestion_id=ingestion_id,
        )
        self._repo.upsert_document(doc)

        run = IngestionRun(
            ingestion_id=ingestion_id,
            document_id=document_id,
            status=DocumentStatus.received,
        )
        self._repo.create_run(run)

        self._validate_and_store(doc, run, data)
        stored_doc = self._repo.get_document(document_id) or doc
        stored_run = self._repo.get_run(ingestion_id) or run
        return IngestionResult(document=stored_doc, run=stored_run)

    def run_existing(self, ingestion_id: str) -> None:
        run = self._repo.get_run(ingestion_id)
        if run is None:
            return
        doc = self._repo.get_document(run.document_id)
        if doc is None:
            return

        raw_path = self._storage.raw_file_path(
            doc.document_id,
            run.ingestion_id,
            doc.filename,
        )
        if not raw_path.exists():
            err = PipelineError(
                error_type="raw_missing",
                message="Raw file missing in artifact storage",
                stage=PipelineStage.store,
                retryable=False,
                context={"raw_path": str(raw_path)},
            )
            self._repo.add_run_error(run.ingestion_id, err)
            self._repo.set_run_status(run.ingestion_id, DocumentStatus.failed)
            self._repo.set_document_status(doc.document_id, DocumentStatus.failed)
            self._emit_event(
                doc.document_id,
                run.ingestion_id,
                PipelineStage.store,
                PipelineEventStatus.failed,
                error=err,
            )
            return

        self._classify(doc, run)
        self._preprocess(doc, run)
        self._finalize(doc, run)

    def _validate_and_store(
        self,
        doc: Document,
        run: IngestionRun,
        data: bytes,
    ) -> None:
        stage = PipelineStage.validate
        self._emit_event(doc.document_id, run.ingestion_id, stage, "started")
        with timer() as t:
            error = self._validate_bytes(data)
        if error is not None:
            self._fail(doc, run, stage, error, duration_ms=t.duration_ms)
            return
        self._emit_event(
            doc.document_id,
            run.ingestion_id,
            stage,
            "succeeded",
            duration_ms=t.duration_ms,
            metrics={"size_bytes": len(data)},
        )

        stage = PipelineStage.store
        self._emit_event(doc.document_id, run.ingestion_id, stage, "started")
        with timer() as t:
            try:
                self._storage.ensure_run_dirs(doc.document_id, run.ingestion_id)
                raw_path = self._storage.raw_file_path(
                    doc.document_id,
                    run.ingestion_id,
                    doc.filename,
                )
                raw_path.write_bytes(data)
            except OSError as e:
                err = PipelineError(
                    error_type=type(e).__name__,
                    message=str(e),
                    stage=stage,
                    retryable=False,
                    context={"filename": doc.filename},
                    stacktrace=traceback.format_exc(),
                )
                self._fail(doc, run, stage, err, duration_ms=t.duration_ms)
                return

        self._repo.set_document_status(doc.document_id, DocumentStatus.stored)
        self._repo.set_run_status(run.ingestion_id, DocumentStatus.stored)
        self._emit_event(
            doc.document_id,
            run.ingestion_id,
            stage,
            "succeeded",
            duration_ms=t.duration_ms,
            metrics={"raw_path": str(raw_path)},
        )

    def _classify(self, doc: Document, run: IngestionRun) -> None:
        stage = PipelineStage.classify
        self._emit_event(doc.document_id, run.ingestion_id, stage, "started")
        raw_path = self._storage.raw_file_path(
            doc.document_id,
            run.ingestion_id,
            doc.filename,
        )
        with timer() as t:
            try:
                result = classify_file(raw_path, doc.content_type)
            except Exception as e:  # noqa: BLE001
                err = PipelineError(
                    error_type=type(e).__name__,
                    message=str(e),
                    stage=stage,
                    retryable=False,
                    context={"raw_path": str(raw_path)},
                    stacktrace=traceback.format_exc(),
                )
                self._fail(doc, run, stage, err, duration_ms=t.duration_ms)
                return

        self._write_metadata(doc.document_id, run.ingestion_id, result)
        self._repo.set_document_status(doc.document_id, DocumentStatus.classified)
        self._repo.set_run_status(run.ingestion_id, DocumentStatus.classified)
        stored_run = self._repo.get_run(run.ingestion_id)
        if stored_run is not None:
            stored_run.classification = result
            self._repo.create_run(stored_run)
        self._emit_event(
            doc.document_id,
            run.ingestion_id,
            stage,
            "succeeded",
            duration_ms=t.duration_ms,
            metrics=result.model_dump(mode="json"),
        )

    def _preprocess(self, doc: Document, run: IngestionRun) -> None:
        stage = PipelineStage.preprocess
        self._emit_event(doc.document_id, run.ingestion_id, stage, "started")
        raw_path = self._storage.raw_file_path(
            doc.document_id,
            run.ingestion_id,
            doc.filename,
        )
        stored_run = self._repo.get_run(run.ingestion_id)
        classification = stored_run.classification if stored_run else None

        with timer() as t:
            metrics: dict[str, Any] = {}
            try:
                if classification is None or not classification.needs_preprocessing:
                    self._emit_event(
                        doc.document_id,
                        run.ingestion_id,
                        stage,
                        "succeeded",
                        duration_ms=t.duration_ms,
                        metrics={"skipped": True},
                    )
                    self._repo.set_document_status(
                        doc.document_id,
                        DocumentStatus.preprocessed,
                    )
                    self._repo.set_run_status(run.ingestion_id, DocumentStatus.preprocessed)
                    return

                pages_dir = self._storage.pages_dir(doc.document_id, run.ingestion_id)
                pre_dir = self._storage.preprocessed_dir(doc.document_id, run.ingestion_id)
                if raw_path.suffix.lower() == ".pdf":
                    pm = preprocess_pdf_to_images(raw_path, pages_dir, pre_dir)
                    metrics = {
                        "pages_rendered": pm.pages_rendered,
                        "pages_preprocessed": pm.pages_preprocessed,
                    }
                else:
                    out_path = pre_dir / Path(doc.filename).name
                    preprocess_image(raw_path, out_path)
                    metrics = {"images_preprocessed": 1}
            except Exception as e:  # noqa: BLE001
                err = PipelineError(
                    error_type=type(e).__name__,
                    message=str(e),
                    stage=stage,
                    retryable=False,
                    context={"raw_path": str(raw_path)},
                    stacktrace=traceback.format_exc(),
                )
                self._fail(doc, run, stage, err, duration_ms=t.duration_ms)
                return

        self._repo.set_document_status(doc.document_id, DocumentStatus.preprocessed)
        self._repo.set_run_status(run.ingestion_id, DocumentStatus.preprocessed)
        self._emit_event(
            doc.document_id,
            run.ingestion_id,
            stage,
            "succeeded",
            duration_ms=t.duration_ms,
            metrics=metrics,
        )

    def _finalize(self, doc: Document, run: IngestionRun) -> None:
        stored_run = self._repo.get_run(run.ingestion_id)
        if stored_run is None:
            return
        if stored_run.errors:
            status = DocumentStatus.completed_with_errors
        else:
            status = DocumentStatus.completed
        self._repo.set_document_status(doc.document_id, status)
        self._repo.set_run_status(run.ingestion_id, status)

    def _validate_bytes(self, data: bytes) -> PipelineError | None:
        if not data:
            return PipelineError(
                error_type="empty_file",
                message="Uploaded file is empty",
                stage=PipelineStage.validate,
                retryable=False,
            )
        if len(data) > self._max_bytes:
            return PipelineError(
                error_type="too_large",
                message="Uploaded file exceeds max allowed size",
                stage=PipelineStage.validate,
                retryable=False,
                context={"max_bytes": self._max_bytes, "size_bytes": len(data)},
            )
        return None

    def _fail(
        self,
        doc: Document,
        run: IngestionRun,
        stage: PipelineStage,
        error: PipelineError,
        duration_ms: int | None = None,
    ) -> None:
        self._repo.add_run_error(run.ingestion_id, error)
        self._repo.set_run_status(run.ingestion_id, DocumentStatus.failed)
        self._repo.set_document_status(doc.document_id, DocumentStatus.failed)
        self._emit_event(
            doc.document_id,
            run.ingestion_id,
            stage,
            PipelineEventStatus.failed,
            duration_ms=duration_ms,
            error=error,
        )

    def _emit_event(
        self,
        document_id: str,
        ingestion_id: str,
        stage: PipelineStage,
        status: PipelineEventStatus | str,
        duration_ms: int | None = None,
        metrics: dict[str, Any] | None = None,
        error: PipelineError | None = None,
    ) -> None:
        if isinstance(status, str):
            status = PipelineEventStatus(status)
        event = PipelineEvent(
            ingestion_id=ingestion_id,
            document_id=document_id,
            scope=PipelineScope.document,
            stage=stage,
            status=status,
            duration_ms=duration_ms,
            metrics=metrics or {},
            error=error,
        )
        self._storage.append_event(event)

    def _write_metadata(
        self,
        document_id: str,
        ingestion_id: str,
        classification: ClassificationResult,
    ) -> None:
        path = self._storage.metadata_path(document_id, ingestion_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = classification.model_dump(mode="json")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"

