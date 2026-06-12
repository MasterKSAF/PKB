import pytest
from api.v1.models import ClassifierPending, Document

def test_document_creation_quarantines_missing_codes(client, db_session):
    # Create document with code that does not exist in classifiers
    payload = {
        "title": "Quarantine Test Doc",
        "doc_code": "QT-001",
        "mks_oks_code": "99.999",  # missing
        "okstu_code": "8888",      # missing
        "udc": "555.5"             # missing
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code == 201
    
    # Verify that the missing codes were quarantined
    pending_items = db_session.query(ClassifierPending).all()
    assert len(pending_items) == 3
    
    systems = {item.system: item for item in pending_items}
    assert "MKS" in systems
    assert systems["MKS"].code == "99.999"
    assert systems["MKS"].status == "new"
    
    assert "OKSTU" in systems
    assert systems["OKSTU"].code == "8888"
    
    assert "UDC" in systems
    assert systems["UDC"].code == "555.5"

def test_document_creation_does_not_quarantine_existing_codes(client, db_session):
    # Add an existing MKS classifier
    client.post("/api/v1/registry/classifiers/", json={
        "classifier_system": "MKS",
        "code": "12.345",
        "full_name": "Existing Classifier"
    })
    
    # Create document referencing the existing classifier and a missing one
    payload = {
        "title": "Mix Test Doc",
        "doc_code": "MIX-001",
        "mks_oks_code": "12.345",  # existing
        "okstu_code": "9999",      # missing
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code == 201
    
    # Only the missing one should be in quarantine
    pending_items = db_session.query(ClassifierPending).all()
    assert len(pending_items) == 1
    assert pending_items[0].system == "OKSTU"
    assert pending_items[0].code == "9999"

def test_document_update_quarantines_new_missing_codes(client, db_session):
    # Create document without any codes
    payload = {
        "title": "Initial Doc",
        "doc_code": "INIT-001",
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code == 201
    doc_id = response.json()["data"]["id"]
    
    # No pending items initially
    assert db_session.query(ClassifierPending).count() == 0
    
    # Update document to add a missing code
    update_payload = {
        "mks_oks_code": "77.777"
    }
    response = client.put(f"/api/v1/registry/documents/{doc_id}/", json=update_payload)
    assert response.status_code == 200
    
    # Verify that the missing code was quarantined
    pending_items = db_session.query(ClassifierPending).all()
    assert len(pending_items) == 1
    assert pending_items[0].system == "MKS"
    assert pending_items[0].code == "77.777"
