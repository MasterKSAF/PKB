# tests/unit/test_indexing.py

import json
from pathlib import Path

from rag_builder.models.contracts import BuildRequest
from rag_builder.services.indexing_service import IndexingService


def test_index_document_returns_embedded_chunks():
    json_path = Path("examples/gost_20868_81.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    request = BuildRequest.model_validate(data)

    service = IndexingService()
    result = service.index_document(request)

    assert len(result) == 3

    first = result[0]

    assert first.chunk.document_id == 420000
    assert first.chunk.document_version_id == 420001
    assert first.chunk.clause == "1"

    assert first.embedding == [0.0, 0.0, 0.0]