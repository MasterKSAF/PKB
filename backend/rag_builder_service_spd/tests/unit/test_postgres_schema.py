# tests/unit/test_postgres_schema.py

from uuid import uuid4

from rag_builder.core.config import settings
from rag_builder.repositories.postgres_chunk_repository import PostgresChunkRepository


def test_postgres_ensure_schema():
    repo = PostgresChunkRepository()

    repo.ensure_schema()

    assert repo.ping() is True



def test_mark_stale_indexing_jobs_failed():
    repo = PostgresChunkRepository()
    repo.ensure_schema()

    indexing_txn_id = str(uuid4())
    document_id = 880001

    try:
        repo.create_indexing_job(
            document_id=document_id,
            indexing_txn_id=indexing_txn_id,
            status="indexing",
        )

        with repo._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {settings.POSTGRES_SCHEMA}.indexing_jobs
                    SET updated_at = now() - interval '2 hours'
                    WHERE indexing_txn_id = %s
                    """,
                    (indexing_txn_id,),
                )
            conn.commit()

        marked_count = repo.mark_stale_indexing_jobs_failed(
            stale_after_seconds=3600,
        )

        assert marked_count >= 1

        job = repo.get_indexing_job(indexing_txn_id)

        assert job is not None
        assert job["status"] == "failed"
        assert any(
            error["code"] == "INDEXING_JOB_STALE"
            for error in job["errors"]
        )

    finally:
        with repo._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.indexing_jobs
                    WHERE indexing_txn_id = %s
                    """,
                    (indexing_txn_id,),
                )
            conn.commit()
