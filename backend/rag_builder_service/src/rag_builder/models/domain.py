from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Chunk:
    section_id: int
    document_id: UUID
    chunk_index: int
    content: str
    strategy: str
    page: int | None
