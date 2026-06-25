import pytest

def test_get_enums(client):
    response = client.get("/api/v1/registry/enums")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "classifier_system" in data["data"]
    assert "source_type" in data["data"]
    assert "document_status" in data["data"]
    assert "era" in data["data"]

def test_get_enums_structure(client):
    response = client.get("/api/v1/registry/enums")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["data"]["classifier_system"], list)
    assert isinstance(data["data"]["jurisdiction"], list)
    assert "MKS" in data["data"]["classifier_system"]
    assert "RU" in data["data"]["jurisdiction"]
    assert "draft" in data["data"]["document_status"]

def test_get_stats_empty(client):
    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "classifiers_total" in data["data"]
    assert "terminology_total" in data["data"]
    assert "documents_total" in data["data"]
    assert "documents_by_status" in data["data"]

    assert data["data"]["classifiers_total"] == {}
    assert data["data"]["terminology_total"] == 0
    assert data["data"]["documents_total"] == 0

def test_get_stats_with_data(client):
    client.post("/api/v1/registry/classifiers", json={
        "classifier_system": "MKS",
        "code": "STATS_01",
        "full_name": "Stats Classifier"
    })
    client.post("/api/v1/registry/classifiers", json={
        "classifier_system": "MKS",
        "code": "STATS_02",
        "full_name": "Stats Classifier 2"
    })

    client.post("/api/v1/registry/terminology", json={
        "raw_term": "Stats Term",
        "standard_term": "Stats Term",
        "normalized_value": "stats term",
        "term_type": "term"
    })

    client.post("/api/v1/registry/documents", json={
        "title": "Stats Document",
        "status": "draft",
        "classifier_system": "MKS"
    })
    client.post("/api/v1/registry/documents", json={
        "title": "Stats Document 2",
        "status": "approved",
        "classifier_system": "MKS"
    })

    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["data"]["classifiers_total"]["MKS"] == 2
    assert data["data"]["terminology_total"] == 1
    assert data["data"]["documents_total"] == 2
    assert isinstance(data["data"]["documents_by_status"], dict)

def test_get_stats_status_breakdown(client):
    client.post("/api/v1/registry/documents", json={"title": "Draft Doc Status", "status": "draft", "classifier_system": "MKS"})
    client.post("/api/v1/registry/documents", json={"title": "Draft Doc Status 2", "status": "draft", "classifier_system": "MKS"})
    client.post("/api/v1/registry/documents", json={"title": "Approved Doc Status", "status": "approved", "classifier_system": "MKS"})
    client.post("/api/v1/registry/documents", json={"title": "Processing Doc Status", "status": "processing", "classifier_system": "MKS"})

    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()

    status_breakdown = data["data"]["documents_by_status"]
    assert status_breakdown["draft"] >= 2
    assert status_breakdown["approved"] >= 1
    assert status_breakdown["processing"] >= 1


def test_get_db_logs_on_failure(monkeypatch):
    from api.v1.dependencies.database import get_db
    
    logged_events = []
    def mock_log_event(severity, endpoint, query_string=None, data=None, error=None):
        logged_events.append((severity, endpoint, error))
    
    monkeypatch.setattr("api.v1.dependencies.database.log_event", mock_log_event)
    
    # We will simulate an error during db dependency execution
    db_gen = get_db()
    db = next(db_gen)
    
    with pytest.raises(ValueError, match="Simulated database error"):
        db_gen.throw(ValueError("Simulated database error"))
        
    assert len(logged_events) == 1
    assert logged_events[0][0] == "ERROR"
    assert logged_events[0][1] == "database_connection"
    assert "Simulated database error" in logged_events[0][2]


def test_log_payload_masking(monkeypatch):
    import os
    from services.logger import log_payload
    
    # 1. Test normal payload (no PII)
    payload1 = {"name": "test_doc", "code": "123"}
    assert log_payload(payload1) == payload1
    
    # 2. Test masking default fields (password, access_token, refresh_token)
    payload2 = {
        "title": "Document title",
        "password": "secretpassword",
        "access_token": "token123",
        "nested": {
            "refresh_token": "token456",
            "non_pii": "value"
        },
        "list_items": [
            {"password": "pw1"},
            {"ok": True}
        ]
    }
    expected2 = {
        "title": "Document title",
        "password": "***",
        "access_token": "***",
        "nested": {
            "refresh_token": "***",
            "non_pii": "value"
        },
        "list_items": [
            {"password": "***"},
            {"ok": True}
        ]
    }
    assert log_payload(payload2) == expected2
    
    # 3. Test custom LOG_PII_FIELDS
    monkeypatch.setenv("LOG_PII_FIELDS", "secret_key, email")
    payload3 = {
        "email": "user@example.com",
        "secret_key": "12345",
        "password": "should_not_mask"
    }
    expected3 = {
        "email": "***",
        "secret_key": "***",
        "password": "should_not_mask"
    }
    assert log_payload(payload3) == expected3


def test_health_check_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "registry-service"
    assert data["version"] == "1.0.0"

def test_request_validation_error_format(client):
    response = client.post("/api/v1/registry/drafts", json={
        "file_key": 12345,
        "document_key": {},
        "status": None
    })
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "validation_errors" in data["error"]["details"]
    assert len(data["error"]["details"]["validation_errors"]) > 0

def test_document_date_range_validation(client):
    # 1. date_from > date_to
    response = client.get("/api/v1/registry/documents", params={
        "date_from": "2026-01-02T00:00:00",
        "date_to": "2026-01-01T00:00:00"
    })
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_DATE_RANGE"
    assert "date_from позже date_to" in data["error"]["message"]

    # 2. date range > 100 years
    response = client.get("/api/v1/registry/documents", params={
        "date_from": "1900-01-01T00:00:00",
        "date_to": "2026-01-01T00:00:00"
    })
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_DATE_RANGE"
    assert "Превышен максимальный диапазон дат" in data["error"]["message"]

def test_request_id_tracing_headers(client):
    headers = {"X-Request-ID": "test-request-id-123"}
    response = client.get("/api/v1/registry/enums", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "test-request-id-123"

def test_generic_exception_hiding(client, monkeypatch):
    from api.v1.crud import document
    def mock_get_documents(*args, **kwargs):
        raise ValueError("Database connection dropped!")
        
    monkeypatch.setattr(document, "get_documents", mock_get_documents)
    
    response = client.get("/api/v1/registry/documents")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_ERROR"
    assert data["error"]["message"] == "Внутренняя ошибка сервера"
    assert "Database connection dropped!" not in str(data)



