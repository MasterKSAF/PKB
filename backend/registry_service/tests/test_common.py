def test_get_enums(client):
    response = client.get("/api/v1/registry/enums")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "doc_type" in data["data"]
    assert "jurisdiction" in data["data"]

def test_get_stats(client):
    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "classifiers_total" in data["data"]
    assert "terminology_total" in data["data"]
    assert "documents_total" in data["data"]
