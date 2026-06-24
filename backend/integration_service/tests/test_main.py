def test_root_endpoint(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Integration Service API" in data["message"]
