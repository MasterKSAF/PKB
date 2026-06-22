import pytest

from rag_builder.repositories.postgres_chunk_repository import (
    PostgresChunkRepository,
)


def test_embedding_dim_sql_accepts_service_checker_dimension(monkeypatch):
    monkeypatch.setattr(
        "rag_builder.repositories.postgres_chunk_repository.settings.EMBEDDING_DIM",
        312,
    )

    repository = PostgresChunkRepository()

    assert repository._embedding_dim_sql() is not None


@pytest.mark.parametrize("bad_dim", [0, -1])
def test_embedding_dim_sql_rejects_non_positive_dimension(
        monkeypatch,
        bad_dim,
):
    monkeypatch.setattr(
        "rag_builder.repositories.postgres_chunk_repository.settings.EMBEDDING_DIM",
        bad_dim,
    )

    repository = PostgresChunkRepository()

    with pytest.raises(ValueError, match="positive integer"):
        repository._embedding_dim_sql()