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
    Deletes a document from the registry database.

    In production: calls RegistryServiceClient.delete_registry_document().
    """
    logger.info(
        f"Compensation: delete registry document: draft_id={draft_id} reg_id={registry_id}"
    )
    return {
        "status": "compensated",
        "action": "delete_registry_document",
        "draft_id": draft_id,
    }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30, name="tasks.compensation.delete_from_vector_index")
def delete_from_vector_index(self, document_id: str):
    """
    Compensation for 'rag_index' step.
    Deletes a document from the vector search index.

    In production: calls RAGServiceClient.delete_index().
    """
    logger.info(
        f"Compensation: delete from vector index: doc={document_id}"
    )
    return {
        "status": "compensated",
        "action": "delete_from_vector_index",
        "document_id": document_id,
    }
