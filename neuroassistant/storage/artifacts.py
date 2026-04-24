"""Artifact storage for ingestion pipeline (local filesystem MVP)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from neuroassistant.domain import PipelineEvent


class ArtifactStorage(Protocol):
    def root(self) -> Path:
        raise NotImplementedError

    def document_root(self, document_id: str) -> Path:
        raise NotImplementedError

    def run_root(self, document_id: str, ingestion_id: str) -> Path:
        raise NotImplementedError

    def raw_dir(self, document_id: str, ingestion_id: str) -> Path:
        raise NotImplementedError

    def derived_dir(self, document_id: str, ingestion_id: str) -> Path:
        raise NotImplementedError

    def logs_dir(self, document_id: str, ingestion_id: str) -> Path:
        raise NotImplementedError

    def raw_file_path(
        self,
        document_id: str,
        ingestion_id: str,
        filename: str,
    ) -> Path:
        raise NotImplementedError

    def metadata_path(self, document_id: str, ingestion_id: str) -> Path:
        raise NotImplementedError

    def events_path(self, document_id: str, ingestion_id: str) -> Path:
        raise NotImplementedError

    def append_event(self, event: PipelineEvent) -> None:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class LocalArtifactStorage:
    """Local filesystem artifact storage.

    Layout:
      <root>/<document_id>/<ingestion_id>/
        raw/
        derived/
          pages/
          preprocessed/
          metadata.json
        logs/
          events.jsonl
    """

    artifact_root: Path

    @classmethod
    def from_env(cls) -> "LocalArtifactStorage":
        root = os.environ.get("ARTIFACT_ROOT", "./data_artifacts")
        return cls(artifact_root=Path(root))

    def root(self) -> Path:
        return self.artifact_root

    def document_root(self, document_id: str) -> Path:
        return self.root() / document_id

    def run_root(self, document_id: str, ingestion_id: str) -> Path:
        return self.document_root(document_id) / ingestion_id

    def raw_dir(self, document_id: str, ingestion_id: str) -> Path:
        return self.run_root(document_id, ingestion_id) / "raw"

    def derived_dir(self, document_id: str, ingestion_id: str) -> Path:
        return self.run_root(document_id, ingestion_id) / "derived"

    def logs_dir(self, document_id: str, ingestion_id: str) -> Path:
        return self.run_root(document_id, ingestion_id) / "logs"

    def pages_dir(self, document_id: str, ingestion_id: str) -> Path:
        return self.derived_dir(document_id, ingestion_id) / "pages"

    def preprocessed_dir(self, document_id: str, ingestion_id: str) -> Path:
        return self.derived_dir(document_id, ingestion_id) / "preprocessed"

    def raw_file_path(
        self,
        document_id: str,
        ingestion_id: str,
        filename: str,
    ) -> Path:
        safe_name = Path(filename).name
        return self.raw_dir(document_id, ingestion_id) / safe_name

    def metadata_path(self, document_id: str, ingestion_id: str) -> Path:
        return self.derived_dir(document_id, ingestion_id) / "metadata.json"

    def events_path(self, document_id: str, ingestion_id: str) -> Path:
        return self.logs_dir(document_id, ingestion_id) / "events.jsonl"

    def ensure_run_dirs(self, document_id: str, ingestion_id: str) -> None:
        self.raw_dir(document_id, ingestion_id).mkdir(parents=True, exist_ok=True)
        self.pages_dir(document_id, ingestion_id).mkdir(parents=True, exist_ok=True)
        self.preprocessed_dir(document_id, ingestion_id).mkdir(
            parents=True,
            exist_ok=True,
        )
        self.logs_dir(document_id, ingestion_id).mkdir(parents=True, exist_ok=True)

    def append_event(self, event: PipelineEvent) -> None:
        if event.document_id is None:
            raise ValueError("event.document_id is required for storage logging")

        self.ensure_run_dirs(event.document_id, event.ingestion_id)
        path = self.events_path(event.document_id, event.ingestion_id)
        line = json.dumps(event.model_dump(mode="json"), ensure_ascii=False)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

