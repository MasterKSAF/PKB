import pytest


@pytest.mark.asyncio
async def test_create_project(client):
    r = await client.post("/api/v1/chat/projects", json={
        "code": "21900M2",
        "name": "Ледокол проекта 21900М2",
        "description": "Тест",
        "status": "active",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["code"] == "21900M2"
    assert data["name"] == "Ледокол проекта 21900М2"
    assert data["status"] == "active"
    assert "project_id" in data
    return data["project_id"]


@pytest.mark.asyncio
async def test_list_projects(client):
    await client.post("/api/v1/chat/projects", json={"code": "LIST-TEST", "name": "Для списка"})
    r = await client.get("/api/v1/chat/projects")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["total"] >= 1
    item = data["items"][0]
    assert "code" in item
    assert "status" in item


@pytest.mark.asyncio
async def test_list_projects_filter_by_status(client):
    await client.post("/api/v1/chat/projects", json={"code": "ARCH-1", "name": "Архивный", "status": "archived"})
    r = await client.get("/api/v1/chat/projects?status=archived")
    assert r.status_code == 200
    data = r.json()
    assert all(item["status"] == "archived" for item in data["items"])


@pytest.mark.asyncio
async def test_get_project(client):
    r = await client.post("/api/v1/chat/projects", json={"code": "GET-TEST", "name": "Получить"})
    pid = r.json()["project_id"]
    r = await client.get(f"/api/v1/chat/projects/{pid}")
    assert r.status_code == 200
    data = r.json()
    assert data["project_id"] == pid
    assert data["code"] == "GET-TEST"


@pytest.mark.asyncio
async def test_update_project(client):
    r = await client.post("/api/v1/chat/projects", json={"code": "UPD-TEST", "name": "До обновления"})
    pid = r.json()["project_id"]
    r = await client.put(f"/api/v1/chat/projects/{pid}", json={"name": "После обновления", "status": "archived"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "После обновления"
    assert data["status"] == "archived"


@pytest.mark.asyncio
async def test_delete_project(client):
    r = await client.post("/api/v1/chat/projects", json={"code": "DEL-TEST", "name": "На удаление"})
    pid = r.json()["project_id"]
    r = await client.delete(f"/api/v1/chat/projects/{pid}")
    assert r.status_code == 204
    r = await client.get(f"/api/v1/chat/projects/{pid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_project_not_found(client):
    r = await client.get("/api/v1/chat/projects/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_project_invalid_status(client):
    r = await client.post("/api/v1/chat/projects", json={"code": "BAD", "name": "Плохой статус", "status": "unknown"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_project_duplicate_code(client):
    r = await client.post("/api/v1/chat/projects", json={"code": "DUPCODE", "name": "Проект 1"})
    assert r.status_code == 201
    r = await client.post("/api/v1/chat/projects", json={"code": "DUPCODE", "name": "Проект 2"})
    assert r.status_code == 409
    assert r.json()["detail"]["error"]["code"] == "DUPLICATE_PROJECT"
