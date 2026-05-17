def test_external_status(test_client):
    response = test_client.get("/api/v1/external/status")
    assert response.status_code == 200
    data = response.json()
    assert "systems" in data
    assert isinstance(data["systems"], list)
    assert len(data["systems"]) == 1
    
    system = data["systems"][0]
    assert system["api_name"] == "meridian"
    assert system["status"] == "available"
    assert "last_checked" in system
    assert "latency_ms" in system
