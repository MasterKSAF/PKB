# src/rag_builder/models/domain.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Chunk:
    document_id: int
    document_version_id: int
    section_id: int

    parent_id: int | None
    clause: str | None
    path: str

    page: int | None
    bbox: list[float] | None

    chunk_index: int
    chunk_type: str
    content: str

    metadata: dict[str, Any]

@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: Chunk
    embedding: list[float]

@dataclass(frozen=True)
class EmbeddingResult:
    embedding: list[float]
    token_count: int
    cost_usd: float

@dataclass(frozen=True)
class IndexIssue:
    code: str
    message: str
    section_id: int | None = None

@dataclass(frozen=True)
class IndexingResult:
    chunks: list[EmbeddedChunk]

    embedding_tokens: int
    embedding_cost_usd: float

    warnings: list[IndexIssue]
    errors: list[IndexIssue]
