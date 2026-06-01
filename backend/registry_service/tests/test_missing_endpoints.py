import uuid

from api.v1.models import ClassifierPending, DocumentHistory


def test_check_documents_uniqueness(client):
    client.post("/api/v1/registry/documents/", json={
        "title": "Unique Doc",
        "doc_code": "UNQ-1",
        "era": "RF",
        "status": "approved",
    })
    response = client.post("/api/v1/registry/documents/check-uniqueness", json={
        "title": "Unique Doc",
        "doc_code": "UNQ-1",
        "era": "RF",
    })
    assert response.status_code == 200
    body = response.json()["data"]
    assert "is_duplicate" in body
    assert "title_hash_sha256" in body


def test_document_sections(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Sections Doc"})
    doc_id = create_res.json()["data"]["id"]

    response = client.get(f"/api/v1/registry/documents/{doc_id}/sections")
    assert response.status_code == 200
    body = response.json()
    assert body["document"]["id"] == doc_id
    assert "sections" in body
    assert "references" in body


def test_document_history_with_rows(client, db_session):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "History Doc"})
    doc_id = create_res.json()["data"]["id"]

    db_session.add(DocumentHistory(
        id=uuid.uuid4(),
        document_id=uuid.UUID(doc_id),
        old_status=None,
        new_status="uploaded",
        comment='{"reason": "initial_upload"}',
        changed_by="tester",
    ))
    db_session.commit()

    response = client.get(f"/api/v1/registry/documents/{doc_id}/history")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["new_status"] == "uploaded"
    assert data[0]["comment"]["reason"] == "initial_upload"


def test_document_succession_chain(client):
    pred = client.post("/api/v1/registry/documents/", json={
        "title": "Pred", "doc_code": "P-1", "era": "USSR",
    }).json()["data"]
    main_res = client.post("/api/v1/registry/documents/", json={
        "title": "Main",
        "doc_code": "M-1",
        "era": "USSR",
        "predecessor_doc_id": pred["id"],
    })
    assert main_res.status_code in (200, 201), main_res.text
    main = main_res.json()["data"]
    succ = client.post("/api/v1/registry/documents/", json={
        "title": "Succ", "doc_code": "S-1", "era": "RF",
    }).json()["data"]
    patch_res = client.patch(f"/api/v1/registry/documents/{main['id']}", json={"successor_doc_id": succ["id"]})
    assert patch_res.status_code == 200

    response = client.get(f"/api/v1/registry/documents/{main['id']}/succession")
    assert response.status_code == 200
    chain = response.json()["data"]["chain"]
    relations = {item["relation"] for item in chain}
    assert "self" in relations
    assert "predecessor" in relations
    assert "successor" in relations


def test_classifier_validate(client):
    client.post("/api/v1/registry/classifiers/", json={
        "classifier_system": "MKS",
        "code": "47.020",
        "full_name": "Hull",
    })
    response = client.post("/api/v1/registry/classifiers/validate", json={
        "classification": {"mks_oks_code": "47.020", "okstu_code": None, "udk_code": None},
    })
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["mks_status"] == "CONFIRMED"
    assert data["overall_status"] == "valid"


def test_classifier_pending_accept_reject(client, db_session):
    doc_id = client.post("/api/v1/registry/documents/", json={"title": "Pending Doc"}).json()["data"]["id"]
    pending = ClassifierPending(
        id=uuid.uuid4(),
        system="MKS",
        code="47.020.99",
        found_in_document_id=uuid.UUID(doc_id),
        status="new",
    )
    db_session.add(pending)
    db_session.commit()

    list_res = client.get("/api/v1/registry/classifiers/pending?system=MKS")
    assert list_res.status_code == 200
    assert list_res.json()["meta"]["total"] >= 1

    accept_res = client.post(
        f"/api/v1/registry/classifiers/pending/{pending.id}/accept",
        json={"parent_code": "47.020", "full_name": "Other hull parts", "admin_comment": "ok"},
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["data"]["status"] == "mapped"

    pending2 = ClassifierPending(
        id=uuid.uuid4(),
        system="MKS",
        code="47.020.98",
        status="new",
    )
    db_session.add(pending2)
    db_session.commit()

    reject_res = client.post(
        f"/api/v1/registry/classifiers/pending/{pending2.id}/reject",
        json={"admin_comment": "invalid code"},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["status"] == "rejected"
