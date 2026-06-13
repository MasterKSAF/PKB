# tests/unit/test_postgres_insert.py

import json
from pathlib import Path

from rag_builder.models.contracts import BuildRequest
from rag_builder.repositories.postgres_chunk_repository import (
    PostgresChunkRepository,
)
from rag_builder.services.indexing_service import IndexingService


def test_save_chunks_to_postgres():
    json_path = Path("examples/gost_20868_81.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    request = BuildRequest.model_validate(data)

    indexing_service = IndexingService()

    chunks = indexing_service.index_document(request)

    repository = PostgresChunkRepository()

    repository.ensure_schema()
    repository.save_chunks(chunks)