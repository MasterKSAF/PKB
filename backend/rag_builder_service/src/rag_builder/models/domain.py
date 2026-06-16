from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    section_id: int
    document_id: int
    chunk_index: int
    content: str
    strategy: str
    page: int | None
