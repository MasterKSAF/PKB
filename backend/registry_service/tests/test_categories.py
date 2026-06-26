import pytest
from datetime import datetime, timezone, date
from api.v1.models.category import Category, DocumentCategory
from api.v1.models.document import Document

def test_create_category(client, db_session):
    # 1. POST valid payload
    payload = {
        "name": "Тестовая категория",
        "description": "Описание тестовой категории",
        "color": "#123456"
    }
    response = client.post("/api/v1/registry/categories", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Тестовая категория"
    assert data["description"] == "Описание тестовой категории"
    assert data["color"] == "#123456"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # 2. POST duplicate name -> 409 DUPLICATE_CATEGORY_NAME
    response_dup = client.post("/api/v1/registry/categories", json=payload)
    assert response_dup.status_code == 409
    assert response_dup.json()["error"]["code"] == "DUPLICATE_CATEGORY_NAME"

def test_list_categories(client, db_session):
    # Seed categories
    for i in range(1, 6):
        cat = Category(
            name=f"Категория {i}",
            code=f"cat_{i}",
            description=f"Описание {i}",
            color=f"#00000{i}",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db_session.add(cat)
    db_session.commit()

    # GET list
    response = client.get("/api/v1/registry/categories?page=1&page_size=3")
    assert response.status_code == 200
    res_body = response.json()
    assert len(res_body["data"]) == 3
    assert res_body["meta"]["total"] == 5
    assert res_body["meta"]["page"] == 1
    assert res_body["meta"]["page_size"] == 3

def test_get_category(client, db_session):
    cat = Category(
        name="Уникальная категория",
        code="uniq_cat",
        description="Детали",
        color="#FFFFFF",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)

    # Success GET
    response = client.get(f"/api/v1/registry/categories/{cat.id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == cat.id
    assert data["name"] == "Уникальная категория"

    # 404 GET
    response_404 = client.get("/api/v1/registry/categories/9999")
    assert response_404.status_code == 404
    assert response_404.json()["error"]["code"] == "CATEGORY_NOT_FOUND"

def test_update_category(client, db_session):
    cat1 = Category(
        name="Кат 1",
        code="cat_1",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    cat2 = Category(
        name="Кат 2",
        code="cat_2",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add_all([cat1, cat2])
    db_session.commit()
    db_session.refresh(cat1)
    db_session.refresh(cat2)

    # 1. Update success (partial)
    payload = {
        "name": "Новое имя Кат 1",
        "color": "#FF0000"
    }
    response = client.put(f"/api/v1/registry/categories/{cat1.id}", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Новое имя Кат 1"
    assert data["color"] == "#FF0000"
    assert data["id"] == cat1.id

    # 2. Update to duplicate name -> 409
    payload_dup = {
        "name": "Кат 2"
    }
    response_dup = client.put(f"/api/v1/registry/categories/{cat1.id}", json=payload_dup)
    assert response_dup.status_code == 409
    assert response_dup.json()["error"]["code"] == "DUPLICATE_CATEGORY_NAME"

    # 3. Update non-existing -> 404
    response_404 = client.put("/api/v1/registry/categories/9999", json=payload)
    assert response_404.status_code == 404
    assert response_404.json()["error"]["code"] == "CATEGORY_NOT_FOUND"

def test_delete_category(client, db_session):
    cat = Category(
        name="Удаляемая категория",
        code="del_cat",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)

    # 1. DELETE non-existing -> 404
    response_404 = client.delete("/api/v1/registry/categories/9999")
    assert response_404.status_code == 404
    assert response_404.json()["error"]["code"] == "CATEGORY_NOT_FOUND"

    # 2. DELETE linked category -> 409 CATEGORY_HAS_DOCUMENTS
    doc = Document(
        id=500,
        doc_code="DOC-500",
        title="Linked Document",
        valid_from=date(2020, 1, 1),
        valid_until=date(2030, 1, 1),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(doc)
    link = DocumentCategory(document_id=500, category_id=cat.id)
    db_session.add(link)
    db_session.commit()

    response_linked = client.delete(f"/api/v1/registry/categories/{cat.id}")
    assert response_linked.status_code == 409
    assert response_linked.json()["error"]["code"] == "CATEGORY_HAS_DOCUMENTS"

    # 3. DELETE success (after removing link)
    db_session.delete(link)
    db_session.commit()

    response_ok = client.delete(f"/api/v1/registry/categories/{cat.id}")
    assert response_ok.status_code == 200
    res_data = response_ok.json()["data"]
    assert res_data["id"] == cat.id
    assert "deleted_at" in res_data
    assert res_data["message"] == "Категория удалена"
