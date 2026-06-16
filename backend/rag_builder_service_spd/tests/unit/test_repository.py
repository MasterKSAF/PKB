# tests/unit/test_repository.py

import pytest


from rag_builder.repositories.chunk_repository import (
    ChunkRepository,
    InMemoryChunkRepository,
)

def test_repository_not_implemented():
    repository = ChunkRepository()

    with pytest.raises(NotImplementedError):
        repository.save_chunks([])

def test_in_memory_repository_saves_chunks():
    repository = InMemoryChunkRepository()

    repository.save_chunks([])

    assert repository.count() == 0
    assert repository.list_chunks() == []