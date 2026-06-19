"""
Compensation (Saga rollback) tasks for failed pipeline steps.

These tasks undo side-effects of completed steps when a pipeline fails.
"""

import logging

from app.celery_app import celery_app

logger = logging.getLogger("tasks.compensation")


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30, name="tasks.compensation.delete_registry_document")
def delete_registry_document(self, draft_id: int, registry_id: str):
    """
    Compensation for 'registry_creation' step.
    Deletes a document from the registry via Registry API.
    """
    logger.info(
        f"Compensation: delete registry document: draft_id={draft_id} reg_id={registry_id}"
    )
    try:
        # Real call to Registry
        import asyncio
        from app.services.registry_client import RegistryServiceClient

        async def _delete():
            client = RegistryServiceClient()
            await client.delete_document(int(registry_id))
            await client.close()

        asyncio.run(_delete())
        logger.info(f"Registry document {registry_id} deleted (compensation)")
    except Exception as exc:
        logger.error(f"Compensation delete_registry_document failed: {exc}")
        raise

    return {
        "status": "compensated",
        "action": "delete_registry_document",
        "draft_id": draft_id,
        "registry_id": registry_id,
    }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30, name="tasks.compensation.delete_from_vector_index")
def delete_from_vector_index(self, document_id: str):
    """
    Compensation for 'rag_index' step.
    Deletes a document from the vector search index via RAG API.
    """
    logger.info(
        f"Compensation: delete from vector index: doc={document_id}"
    )
    try:
        # Real call to RAG Builder
        import asyncio
        from app.services.rag_client import RAGBuilderClient

        async def _delete():
            client = RAGBuilderClient()
            await client.delete_index(document_id)
            await client.close()

        asyncio.run(_delete())
        logger.info(f"Vector index for {document_id} deleted (compensation)")
    except Exception as exc:
        logger.error(f"Compensation delete_from_vector_index failed: {exc}")
        raise

    return {
        "status": "compensated",
        "action": "delete_from_vector_index",
        "document_id": document_id,
    }
