import json
from pathlib import Path

from rag_builder.models.contracts import BuildRequest
from rag_builder.repositories.chunk_repository import InMemoryChunkRepository
from rag_builder.services.indexing_service import IndexingService


def test_indexing_saves_chunks_to_repository():
    json_path = Path("examples/gost_20868_81.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    request = BuildRequest.model_validate(data)

    repository = InMemoryChunkRepository()

    service = IndexingService(repository)

    result = service.index_document(request)

    assert len(result) == 3

    assert repository.count() == 3

    stored = repository.list_chunks()

    assert len(stored) == 3

    assert stored[0].chunk.document_id == 420000