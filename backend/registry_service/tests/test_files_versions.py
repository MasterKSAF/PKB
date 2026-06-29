import pytest
from datetime import datetime, timezone
from api.v1.models.files import File
from api.v1.models.document_versions import DocumentVersion

def test_get_file_metadata(client, db_session):
    # 1. Insert test file
    test_file = File(
        file_id="f-test-123",
        filename="test.pdf",
        size=1024,
        mime_type="application/pdf",
        url="/files/f-test-123",
        uploaded_at=datetime.now(timezone.utc).replace(tzinfo=None),
        storage_path="/storage/test.pdf",
        related_document_id="10"
    )
    db_session.add(test_file)
    db_session.commit()

    # 2. Get via API
    response = client.get("/api/v1/registry/files/f-test-123")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["file_id"] == "f-test-123"
    assert data["filename"] == "test.pdf"
    assert data["size"] == 1024
    assert data["mime_type"] == "application/pdf"
    assert data["url"] == "/files/f-test-123"
    assert data["related_document_id"] == "10"
    assert data["storage_path"] == "/storage/test.pdf"

    # Test 404
    res_404 = client.get("/api/v1/registry/files/f-nonexistent")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "FILE_NOT_FOUND"

def test_list_document_files(client, db_session):
    # 1. Insert test files
    f1 = File(
        file_id="f-doc-1",
        filename="doc1.pdf",
        size=2048,
        mime_type="application/pdf",
        url="/files/f-doc-1",
        uploaded_at=datetime.now(timezone.utc).replace(tzinfo=None),
        storage_path="/storage/doc1.pdf",
        related_document_id="42"
    )
    f2 = File(
        file_id="f-doc-2",
        filename="doc2.pdf",
        size=4096,
        mime_type="application/pdf",
        url="/files/f-doc-2",
        uploaded_at=datetime.now(timezone.utc).replace(tzinfo=None),
        storage_path="/storage/doc2.pdf",
        related_document_id="42"
    )
    # Different doc id
    f3 = File(
        file_id="f-doc-3",
        filename="doc3.pdf",
        size=8192,
        mime_type="application/pdf",
        url="/files/f-doc-3",
        uploaded_at=datetime.now(timezone.utc).replace(tzinfo=None),
        storage_path="/storage/doc3.pdf",
        related_document_id="99"
    )
    db_session.add_all([f1, f2, f3])
    db_session.commit()

    # 2. Get via API
    response = client.get("/api/v1/registry/documents/42/files")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    file_ids = {item["file_id"] for item in data}
    assert "f-doc-1" in file_ids
    assert "f-doc-2" in file_ids

def test_list_document_versions(client, db_session):
    # 1. Insert document versions
    v1 = DocumentVersion(
        id=101,
        document_id=50,
        version_number=1,
        file_hash_sha256="hash1",
        file_size_bytes=1000,
        format_code="pdf",
        format_label="PDF",
        file_key="key1",
        revision=1,
        source_filename="v1.pdf",
        file_path="/path/v1.pdf",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    v2 = DocumentVersion(
        id=102,
        document_id=50,
        version_number=2,
        file_hash_sha256="hash2",
        file_size_bytes=2000,
        format_code="pdf",
        format_label="PDF",
        file_key="key2",
        revision=1,
        source_filename="v2.pdf",
        file_path="/path/v2.pdf",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add_all([v1, v2])
    db_session.commit()

    # 2. Get via API
    response = client.get("/api/v1/registry/documents/50/versions")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    # Ensure they are sorted by version_number desc
    assert int(data[0]["version_number"]) == 2
    assert int(data[1]["version_number"]) == 1

def test_get_document_version(client, db_session):
    # 1. Insert document version
    v = DocumentVersion(
        id=201,
        document_id=60,
        version_number=1,
        file_hash_sha256="hash_v",
        file_size_bytes=5000,
        format_code="pdf",
        format_label="PDF",
        file_key="key_v",
        revision=1,
        source_filename="v.pdf",
        file_path="/path/v.pdf",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(v)
    db_session.commit()

    # 2. Get via API
    response = client.get("/api/v1/registry/versions/201")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == "201"
    assert data["document_id"] == "60"
    assert data["file_hash_sha256"] == "hash_v"

    # Test 404
    res_404 = client.get("/api/v1/registry/versions/999")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "VERSION_NOT_FOUND"


def test_get_document_file_endpoint(client, db_session):
    # 1. Setup Document and version
    from api.v1.models import Document
    doc = Document(
        doc_code="DOC-FILE-TEST-1",
        title="Doc File Test",
        era="RF",
        status="uploaded"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    v = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        file_hash_sha256="abcdef",
        file_size_bytes=9999,
        format_code="pdf",
        format_label="PDF",
        file_key="key_test_file",
        source_filename="test_file.pdf",
        file_path="key_test_file",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(v)
    db_session.commit()

    # Test GET /registry/documents/{id}/file JSON format
    response = client.get(f"/api/v1/registry/documents/{doc.id}/file")
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert "key_test_file" in res_data["file_url"]
    assert res_data["file_size"] == 9999
    assert res_data["content_type"] == "application/pdf"

    # Test GET /registry/documents/{id}/file binary format (redirect)
    response_bin = client.get(f"/api/v1/registry/documents/{doc.id}/file?format=binary", follow_redirects=False)
    assert response_bin.status_code == 307
    assert response_bin.headers["location"] == "/api/v1/files/key_test_file"


def test_create_document_links_file_and_version(client, db_session):
    # 1. Create a draft first
    from api.v1.models import Draft
    draft = Draft(
        file_key="f-draft-123",
        document_key="doc-draft-123",
        status="ready_for_approve",
        confidence=0.9,
        raw_data={
            "document": {
                "source": {
                    "file_name": "draft_source.pdf",
                    "file_size_bytes": 12345,
                    "file_hash_sha256": "draft_hash_123"
                }
            }
        },
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(draft)
    db_session.commit()
    db_session.refresh(draft)

    # 2. Create document via API passing draft_id
    payload = {
        "title": "Document from Draft",
        "doc_code": "DOC-DRAFT-01",
        "status": "approved",
        "source_draft_id": draft.draft_id
    }
    response = client.post("/api/v1/registry/documents", json=payload)
    assert response.status_code == 201
    doc_id = response.json()["data"]["id"]

    # 3. Check that File record was created
    response_files = client.get(f"/api/v1/registry/documents/{doc_id}/files")
    assert response_files.status_code == 200
    files_data = response_files.json()["data"]
    assert len(files_data) == 1
    assert files_data[0]["file_id"] == "f-draft-123"
    assert files_data[0]["filename"] == "draft_source.pdf"
    assert files_data[0]["size"] == 12345

    # 4. Check that DocumentVersion was created
    response_versions = client.get(f"/api/v1/registry/documents/{doc_id}/versions")
    assert response_versions.status_code == 200
    versions_data = response_versions.json()["data"]
    assert len(versions_data) == 1
    assert versions_data[0]["file_key"] == "f-draft-123"
    assert versions_data[0]["file_hash_sha256"] == "draft_hash_123"

