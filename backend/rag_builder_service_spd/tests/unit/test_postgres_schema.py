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

def test_get_active_indexing_job_for_document_ignores_stale_job():
    repo = PostgresChunkRepository()
    repo.ensure_schema()

    indexing_txn_id = str(uuid4())
    document_id = 880002

    try:
        repo.create_indexing_job(
            document_id=document_id,
            indexing_txn_id=indexing_txn_id,
            status="indexing",
        )

        active_job = repo.get_active_indexing_job_for_document(
            document_id=document_id,
            stale_after_seconds=3600,
        )

        assert active_job is not None
        assert active_job["document_id"] == document_id
        assert active_job["status"] == "indexing"
        assert active_job["indexing_txn_id"] == indexing_txn_id

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

        stale_job = repo.get_active_indexing_job_for_document(
            document_id=document_id,
            stale_after_seconds=3600,
        )

        assert stale_job is None

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

def test_count_active_indexing_jobs_ignores_stale_jobs():
    repo = PostgresChunkRepository()
    repo.ensure_schema()

    fresh_txn_id = str(uuid4())
    stale_txn_id = str(uuid4())
    document_id = 880003

    try:
        repo.create_indexing_job(
            document_id=document_id,
            indexing_txn_id=fresh_txn_id,
            status="indexing",
        )
        repo.create_indexing_job(
            document_id=document_id + 1,
            indexing_txn_id=stale_txn_id,
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
                    (stale_txn_id,),
                )
            conn.commit()

        active_count = repo.count_active_indexing_jobs(
            stale_after_seconds=3600,
        )

        assert active_count >= 1

        with repo._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT count(*)
                    FROM {settings.POSTGRES_SCHEMA}.indexing_jobs
                    WHERE indexing_txn_id IN (%s, %s)
                      AND status IN ('pending_index', 'indexing')
                      AND updated_at >= now() - (%s * interval '1 second')
                    """,
                    (
                        fresh_txn_id,
                        stale_txn_id,
                        3600,
                    ),
                )
                local_active_count = cur.fetchone()[0]

        assert local_active_count == 1

    finally:
        with repo._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.indexing_jobs
                    WHERE indexing_txn_id IN (%s, %s)
                    """,
                    (
                        fresh_txn_id,
                        stale_txn_id,
                    ),
                )
            conn.commit()
