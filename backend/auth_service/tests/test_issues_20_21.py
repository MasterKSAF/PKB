"""
Tests for GitHub issues:
  #21 — available_tabs and UserPermissions were inconsistent:
        system_admin got can_manage_users=True but "admin" was absent from available_tabs;
        can_manage_registry was always False even for roles that have the registry tab.
  #20 — available_tabs was derived from a hardcoded role-name map;
        now driven by actual permissions so the UI can trust the API instead of
        maintaining a local role map.
"""

from app.core.config import settings


# ── Issue #21 ─────────────────────────────────────────────────────────────────


async def test_system_admin_available_tabs_include_admin(auth_client):
    """
    system_admin has users:manage → must see "admin" tab.
    Previously available_tabs came from _ROLE_TABS and the bug caused the admin
    tab to be absent or inconsistent with can_manage_users.
    """
    r = await auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert "admin" in data["available_tabs"], (
        f"system_admin must have 'admin' tab; got available_tabs={data['available_tabs']}"
    )


async def test_me_permissions_and_available_tabs_are_consistent(auth_client):
    """
    can_manage_users and 'admin' tab must agree — if one is set the other must be too.
    These came from different sources (string permissions vs role map) and could diverge.
    """
    r = await auth_client.get("/api/v1/auth/me")
    data = r.json()
    perms = data["permissions"]
    tabs = data["available_tabs"]

    if perms["can_manage_users"]:
        assert "admin" in tabs, "can_manage_users=True but 'admin' is missing from available_tabs"
    else:
        assert "admin" not in tabs, "can_manage_users=False but 'admin' is present in available_tabs"


async def test_can_manage_registry_consistent_with_registry_tab(client, seeded_db):
    """
    can_manage_registry must be True for any role that has the 'registry' tab.
    Previously can_manage_registry was always False (hardcoded) even for
    knowledge_admin who has the registry tab.
    """
    admin_auth = {"Authorization": await _admin_token(client)}
    await client.post("/api/v1/admin/users", json={
        "email": "ka_reg@test.com", "full_name": "KA",
        "password": "Test1234!", "roles": ["knowledge_admin"],
    }, headers=admin_auth)

    login = await client.post("/api/v1/auth/token", json={
        "username": "ka_reg@test.com", "password": "Test1234!",
    })
    ka_token = login.json()["access_token"]
    data = (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ka_token}"})).json()

    if "registry" in data["available_tabs"]:
        assert data["permissions"]["can_manage_registry"] is True, (
            "'registry' tab is present but can_manage_registry=False"
        )


async def test_engineer_has_no_admin_tab(client, seeded_db):
    """engineer has no users:manage → must NOT see 'admin' tab."""
    admin_auth = {"Authorization": await _admin_token(client)}
    await client.post("/api/v1/admin/users", json={
        "email": "eng_notabs@test.com", "full_name": "Eng",
        "password": "Test1234!", "roles": ["engineer"],
    }, headers=admin_auth)

    login = await client.post("/api/v1/auth/token", json={
        "username": "eng_notabs@test.com", "password": "Test1234!",
    })
    me = (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})).json()

    assert "admin" not in me["available_tabs"]
    assert me["permissions"]["can_manage_users"] is False


# ── Issue #20 ─────────────────────────────────────────────────────────────────


async def test_available_tabs_derived_from_permissions_not_role_name(client, seeded_db):
    """
    available_tabs must reflect actual permissions.
    engineer has no documents:write → must NOT get 'documents' or 'registry' tabs.
    knowledge_admin has documents:write → must get both 'documents' and 'registry' tabs.
    The old hardcoded role map could not enforce this — this test catches regression.
    """
    admin_auth = {"Authorization": await _admin_token(client)}

    await client.post("/api/v1/admin/users", json={
        "email": "eng_perm@test.com", "full_name": "Eng",
        "password": "Test1234!", "roles": ["engineer"],
    }, headers=admin_auth)
    await client.post("/api/v1/admin/users", json={
        "email": "ka_perm@test.com", "full_name": "KA",
        "password": "Test1234!", "roles": ["knowledge_admin"],
    }, headers=admin_auth)

    eng_token = (await client.post("/api/v1/auth/token", json={
        "username": "eng_perm@test.com", "password": "Test1234!",
    })).json()["access_token"]
    ka_token = (await client.post("/api/v1/auth/token", json={
        "username": "ka_perm@test.com", "password": "Test1234!",
    })).json()["access_token"]

    eng_me = (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {eng_token}"})).json()
    ka_me = (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ka_token}"})).json()

    assert "documents" not in eng_me["available_tabs"], (
        f"engineer must not have 'documents' tab; got {eng_me['available_tabs']}"
    )
    assert "registry" not in eng_me["available_tabs"], (
        f"engineer must not have 'registry' tab; got {eng_me['available_tabs']}"
    )
    assert eng_me["permissions"]["can_upload_documents"] is False

    assert "documents" in ka_me["available_tabs"], (
        f"knowledge_admin must have 'documents' tab; got {ka_me['available_tabs']}"
    )
    assert "registry" in ka_me["available_tabs"], (
        f"knowledge_admin must have 'registry' tab; got {ka_me['available_tabs']}"
    )
    assert ka_me["permissions"]["can_upload_documents"] is True


async def test_available_tabs_differ_between_roles(client, seeded_db):
    """
    Different roles must produce different available_tabs.
    Catches the regression where the hardcoded map gave identical tabs to all roles.
    """
    admin_auth = {"Authorization": await _admin_token(client)}

    await client.post("/api/v1/admin/users", json={
        "email": "eng_diff@test.com", "full_name": "Eng",
        "password": "Test1234!", "roles": ["engineer"],
    }, headers=admin_auth)
    await client.post("/api/v1/admin/users", json={
        "email": "sa_diff@test.com", "full_name": "SA",
        "password": "Test1234!", "roles": ["system_admin"],
    }, headers=admin_auth)

    eng_token = (await client.post("/api/v1/auth/token", json={
        "username": "eng_diff@test.com", "password": "Test1234!",
    })).json()["access_token"]
    sa_token = (await client.post("/api/v1/auth/token", json={
        "username": "sa_diff@test.com", "password": "Test1234!",
    })).json()["access_token"]

    eng_tabs = set((await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {eng_token}"})).json()["available_tabs"])
    sa_tabs = set((await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {sa_token}"})).json()["available_tabs"])

    assert eng_tabs != sa_tabs, f"engineer and system_admin must have different tabs; both got {eng_tabs}"
    assert "admin" in sa_tabs
    assert "monitor" in sa_tabs
    assert "admin" not in eng_tabs


# ── helpers ───────────────────────────────────────────────────────────────────

async def _admin_token(client) -> str:
    r = await client.post("/api/v1/auth/token", json={
        "username": settings.default_admin_email,
        "password": settings.default_admin_password,
    })
    return f"Bearer {r.json()['access_token']}"
