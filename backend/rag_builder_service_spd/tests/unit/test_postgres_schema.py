# tests/unit/test_postgres_schema.py

from rag_builder.repositories.postgres_chunk_repository import PostgresChunkRepository


def test_postgres_ensure_schema():
    repo = PostgresChunkRepository()

    repo.ensure_schema()

    assert repo.ping() is True