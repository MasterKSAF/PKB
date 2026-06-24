from app.core.config import settings


# --- auth/token ---

async def test_token_success(client, seeded_db):
    r = await client.post("/api/v1/auth/token", json={
        "username": settings.default_admin_email,
        "password": settings.default_admin_password,
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_token_wrong_password(client, seeded_db):
    r = await client.post("/api/v1/auth/token", json={
        "username": settings.default_admin_email,
        "password": "wrongpassword",
    })
    assert r.status_code == 401


# --- auth/me ---

async def test_me_format(auth_client):
    r = await auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["role"], str)
    assert isinstance(data["permissions"], dict)
    assert "can_manage_users" in data["permissions"]
    assert "available_tabs" in data
    assert isinstance(data["available_tabs"], list)


async def test_me_unauthorized(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


# --- admin/users ---

async def test_list_users_has_meta(auth_client):
    r = await auth_client.get("/api/v1/admin/users")
    assert r.status_code == 200
    data = r.json()
    assert "users" in data
    assert "meta" in data
    meta = data["meta"]
    assert "total" in meta
    assert "page" in meta
    assert "page_size" in meta


async def test_create_user_success(auth_client):
    r = await auth_client.post("/api/v1/admin/users", json={
        "email": "newuser@test.com",
        "full_name": "New User",
        "password": "Test1234!",
        "roles": ["engineer"],
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "newuser@test.com"


async def test_create_user_duplicate_returns_409(auth_client):
    payload = {
        "email": "dup@test.com",
        "full_name": "Dup User",
        "password": "Test1234!",
        "roles": ["engineer"],
    }
    await auth_client.post("/api/v1/admin/users", json=payload)
    r = await auth_client.post("/api/v1/admin/users", json=payload)
    assert r.status_code == 409


async def test_create_user_unknown_role_returns_400(auth_client):
    r = await auth_client.post("/api/v1/admin/users", json={
        "email": "bad@test.com",
        "full_name": "Bad",
        "password": "Test1234!",
        "roles": ["nonexistent_role"],
    })
    assert r.status_code == 400


async def test_get_user_by_id(auth_client):
    create = await auth_client.post("/api/v1/admin/users", json={
        "email": "byid@test.com",
        "full_name": "By Id",
        "password": "Test1234!",
        "roles": ["engineer"],
    })
    user_id = create.json()["user_id"]

    r = await auth_client.get(f"/api/v1/admin/users/{user_id}")
    assert r.status_code == 200
    assert r.json()["user_id"] == user_id


async def test_patch_user(auth_client):
    create = await auth_client.post("/api/v1/admin/users", json={
        "email": "patch@test.com",
        "full_name": "Patch User",
        "password": "Test1234!",
        "roles": ["engineer"],
    })
    user_id = create.json()["user_id"]

    r = await auth_client.patch(f"/api/v1/admin/users/{user_id}", json={"roles": ["knowledge_admin"]})
    assert r.status_code == 200


async def test_put_user(auth_client):
    create = await auth_client.post("/api/v1/admin/users", json={
        "email": "put@test.com",
        "full_name": "Put User",
        "password": "Test1234!",
        "roles": ["engineer"],
    })
    user_id = create.json()["user_id"]

    r = await auth_client.put(f"/api/v1/admin/users/{user_id}", json={
        "full_name": "Put User Updated",
        "roles": ["engineer"],
    })
    assert r.status_code == 200


async def test_delete_user(auth_client):
    create = await auth_client.post("/api/v1/admin/users", json={
        "email": "del@test.com",
        "full_name": "Del User",
        "password": "Test1234!",
        "roles": ["engineer"],
    })
    user_id = create.json()["user_id"]

    r = await auth_client.delete(f"/api/v1/admin/users/{user_id}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False


# --- admin/roles ---

async def test_list_roles(auth_client):
    r = await auth_client.get("/api/v1/admin/roles")
    assert r.status_code == 200
    assert "roles" in r.json()


async def test_create_role_success(auth_client):
    r = await auth_client.post("/api/v1/admin/roles", json={
        "name": "test_role",
        "permissions": ["test:read"],
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "test_role"
    assert "test:read" in data["permissions"]


async def test_create_role_duplicate_returns_409(auth_client):
    payload = {"name": "dup_role", "permissions": ["dup:read"]}
    await auth_client.post("/api/v1/admin/roles", json=payload)
    r = await auth_client.post("/api/v1/admin/roles", json=payload)
    assert r.status_code == 409


# --- admin/audit ---

async def test_list_audit_has_meta(auth_client):
    r = await auth_client.get("/api/v1/admin/audit")
    assert r.status_code == 200
    data = r.json()
    assert "events" in data
    assert "meta" in data
    meta = data["meta"]
    assert "total" in meta
    assert "page" in meta
    assert "page_size" in meta


# --- auth/refresh и auth/revoke ---

async def test_refresh_token(client, seeded_db):
    login = await client.post("/api/v1/auth/token", json={
        "username": settings.default_admin_email,
        "password": settings.default_admin_password,
    })
    refresh_token = login.json()["refresh_token"]

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_revoke_token(client, seeded_db):
    login = await client.post("/api/v1/auth/token", json={
        "username": settings.default_admin_email,
        "password": settings.default_admin_password,
    })
    refresh_token = login.json()["refresh_token"]

    r = await client.post("/api/v1/auth/revoke", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "revoked_at" in r.json()
