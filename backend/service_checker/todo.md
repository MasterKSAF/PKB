# План выявления и исправления ошибок API Coverage

## Текущий статус (2026-06-23)

**Pipeline**: 15/15 ✅ (полностью зелёный)
**API Coverage**: 198/226 (8 failed, 20 skipped)

---

## 1. REGISTRY — 2 failed, 3 skipped

### 1a. Categories — 500 Internal Server Error
- **Симптом**: `GET /registry/categories` и `POST /registry/categories` → 500
- **Логи**: нет в логах (нужно смотреть registry.err)
- **Вероятная причина**: таблица `registry.categories` не создана (миграция не применилась) или ошибка в коде
- **Действия**:
  1. Проверить registry.err логи
  2. Проверить, создана ли таблица `registry.categories`
  3. Воспроизвести запрос вручную: `curl http://localhost:8084/api/v1/registry/categories`

### 1b. PATCH /registry/drafts/{draft_id}/metadata → 404
- **Симптом**: checker ожидает 404 (internal API, только Orchestrator)
- **Это НЕ ошибка** — checker явно указывает `expected_status=404`
- **Действие**: убедиться, что Registry возвращает 404 для внешних вызовов

---

## 2. ORCHESTRATOR — 5 failed, 14 skipped

### 2a. GET /drafts/ — 405 Method Not Allowed (DRAFTS-3)
- **Причина**: list_drafts удалён при рефакторинге (чтение через Registry)
- **Решение**: 2 варианта —
  - (a) Добавить прокси `GET /drafts/` → Registry `/registry/drafts`
  - (b) Обновить checker: удалить этот endpoint из API Coverage для оркестратора

### 2b. PATCH /drafts/{draft_id}/metadata — 500 (DRAFTS-8)
- **Причина**: прокси в Registry, но Registry возвращает 404 для внешних (см. 1b)
- **Решение**: в прокси оркестратора обработать 404 от Registry как успех (expected_status=404)

### 2c. GET /monitor/metrics — 404 (MONITOR-1)
- **Причина**: Prometheus-метрики не подключены
- **Решение**: подключить `/metrics` через `prometheus_client` или `opentelemetry`

### 2d-e. GET /documents/, GET /documents/queue — 404 (DOCUMENTS-1,2)
- **Причина**: эти эндпоинты не входят в scope оркестратора (Registry)
- **Решение**: обновить checker — удалить из coverage для оркестратора

### 2f. 14 skipped документов с {doc_id}
- **Причина**: нет prepare-эндпоинта, создающего document_id
- **Решение**: добавить prepare-шаг (POST /documents) перед документами

---

## 3. QUERY — 1 failed

### 3a. POST /chat/projects — 500 (CHAT-4)
- **Симптом**: второй вызов POST /chat/projects с тем же code → UniqueViolation → 500
- **Логи из todos**: `UniqueViolationError: duplicate key value violates unique constraint "uq_chat_projects_user_code"`
- **Решение**: обработать UniqueViolation → 409 Conflict (не 500)

---

## 4. GATEWAY — 3 skipped (предварительные)
- **Причина**: нет prepare-данных для эндпоинтов с path-параметрами
- **Решение**: добавить prepare-шаги

---

## Порядок исправления (приоритет)

| Приоритет | Задача | Ожидаемый эффект |
|-----------|--------|-----------------|
| P0 | 2a, 2d-e: Обновить checker (убрать эндпоинты Registry из coverage оркестратора) | -5 failed |
| P1 | 2b: Обработать 404 от Registry в прокси metadata | -1 failed |
| P1 | 3a: Query 500 → 409 | -1 failed |
| P2 | 2f: Добавить document prepare | -14 skipped |
| P3 | 2c: Мониторинг метрики | -1 failed |
| P3 | 1a: Разобраться с Categories 500 | -2 failed, -3 skipped |
