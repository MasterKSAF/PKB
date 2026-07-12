from convertor_validator_service_lama.models.contracts import (
    RagBuilderBuildAcceptedResponse,
)
from convertor_validator_service_lama.services.rag_builder_client_contracts import (
    build_rag_builder_client_error,
)


def test_rag_builder_build_accepted_response_contract() -> None:
    response = RagBuilderBuildAcceptedResponse.model_validate(
        {
            "status": "indexing",
            "document_id": 420000,
            "indexing_txn_id": "5c2d9d45-2e02-44ad-a2d7-806ba5158341",
            "task_id": 26,
        }
    )

    assert response.status == "indexing"
    assert response.document_id == 420000
    assert response.indexing_txn_id == "5c2d9d45-2e02-44ad-a2d7-806ba5158341"
    assert response.task_id == 26


def test_rag_builder_client_error_from_structured_detail() -> None:
    error = build_rag_builder_client_error(
        status_code=409,
        detail={
            "code": "ALREADY_PROCESSING",
            "message": "Document indexing is already in progress",
            "details": {
                "document_id": 420000,
                "indexing_txn_id": "active-txn",
                "status": "indexing",
            },
        },
    )

    assert error.status_code == 409
    assert error.code == "ALREADY_PROCESSING"
    assert error.message == "Document indexing is already in progress"
    assert error.details == {
        "document_id": 420000,
        "indexing_txn_id": "active-txn",
        "status": "indexing",
    }


def test_rag_builder_client_error_from_string_detail() -> None:
    error = build_rag_builder_client_error(
        status_code=404,
        detail="Indexing job not found",
    )

    assert error.status_code == 404
    assert error.code == "RAG_BUILDER_ERROR"
    assert error.message == "Indexing job not found"
    assert error.details == {}
