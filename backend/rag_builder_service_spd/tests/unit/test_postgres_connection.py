# tests/unit/test_postgres_connection.py

from rag_builder.repositories.postgres_chunk_repository import PostgresChunkRepository


def test_postgres_ping():
    repo = PostgresChunkRepository()

    assert repo.ping() is True