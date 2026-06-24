def test_export_meridian(test_client):
    payload = {
        "document_id": "doc-8a3f2b",
        "data": {
            "designation": "21900M2.362135.0903СБ",
            "title": "Сборочный чертёж корпуса",
            "materials": ["Сталь 09Г2С"],
            "dimensions": "1200x800x600",
            "specification_items": [
                {"position": 1, "name": "Кница", "quantity": 4}
            ]
        }
    }
    
    response = test_client.post("/api/v1/meridian/export", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "export_id" in data
    assert "external_id" in data
    assert data["status"] == "sent"
    assert data["response_message"] == "Принято"
    assert "sent_at" in data
