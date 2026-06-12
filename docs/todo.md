# План реализации: Пользовательские категории документов

## Цель
Реализовать функциональность пользовательских категорий для группировки документов в разделы «Базы знаний»: many-to-many связь документов с категориями, CRUD категорий, фильтрация по категории в списке документов.

---

## Бэкенд (Registry Service)

### 1. Миграция БД

**Таблица `registry.categories`:**

```sql
CREATE TABLE registry.categories (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        varchar(255) NOT NULL UNIQUE,
    description text,
    color       varchar(7),  -- hex #RRGGBB
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
```

**Таблица `registry.document_categories`:**

```sql
CREATE TABLE registry.document_categories (
    document_id bigint NOT NULL REFERENCES registry.documents(id) ON DELETE CASCADE,
    category_id bigint NOT NULL REFERENCES registry.categories(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, category_id)
);
```

**Индексы:**
```sql
CREATE INDEX idx_document_categories_category_id ON registry.document_categories(category_id);
```

**Триггер обновления `updated_at`** (если используется паттерн) — для `registry.categories`.

таблицы и их параметры отражаем только в схемах и примечаниях

### 2. API — эндпоинты (группа `/registry/categories`)

#### 2.1. `GET /registry/categories` — список категорий
- **Query params:** `page`, `page_size`, `sort_by` (name, created_at), `order`
- **Response:** `{ data: [{ id, name, description, color, document_count, created_at, updated_at }], meta }`
- **Логика:** `document_count` — `SELECT COUNT(*) FROM registry.document_categories WHERE category_id = ?`

#### 2.2. `POST /registry/categories` — создать категорию
- **Body:** `{ name (required), description, color }`
- **Validation:** `name` — уникальность, не пустая; `color` — опциональный hex (#RRGGBB)
- **Response:** `201 { data: { id, name, description, color, document_count: 0, created_at, updated_at } }`

#### 2.3. `GET /registry/categories/{category_id}` — одна категория
- **Response:** `200 { data: { id, name, description, color, document_count, ... } }`

#### 2.4. `PUT /registry/categories/{category_id}` — обновить категорию
- **Body:** `{ name (required), description, color }`
- **Validation:** уникальность `name` (исключая саму себя)
- **Response:** `200 { data: { ... } }`

#### 2.5. `DELETE /registry/categories/{category_id}` — удалить категорию
- **Проверка:** если у категории есть документы — отдавать `409 CATEGORY_HAS_DOCUMENTS` (опционально можно разрешить с каскадным удалением связей, если нужно)
- **Response:** `200 { data: { id, deleted_at, message } }`

### 3. API — доработка эндпоинтов документов

#### 3.1. `GET /registry/documents` — добавить query-параметр
- `?category_id=int` — фильтр документов по категории: `WHERE d.id IN (SELECT document_id FROM registry.document_categories WHERE category_id = ?)`

#### 3.2. `GET /registry/documents` и `GET /registry/documents/{id}` — добавить поле `categories`
- `categories: [{ id: bigint, name: string }]` — подгружать через JOIN или отдельный запрос

#### 3.3. `PATCH /registry/documents/{id}` — добавить поле `category_ids`
- `category_ids: bigint[]` — полная замена привязки категорий
- **Логика:** удалить все записи из `document_categories` для документа, вставить новые
- **Транзакция:** в одном запросе с обновлением полей документа

### 4. Gateway routing

Добавить маршрут в Gateway routing table, если его нет:
```
/registry/categories/* → registry-service:8084
```

Убедиться, что Gateway пускает query-параметр `category_id` в `/registry/documents`.
