# Правки по проблемам API (из таблицы)

## План

### 1. POST /chat/sessions/{session_id}/messages/search → 405
- [x] Реализовать эндпоинт в `query_routes.py` по документации

### 2. POST /registry/documents/import → 400/500 (CSV вместо JSON)
- [x] Добавить парсинг CSV/XLSX аналогично `import_classifiers` и `import_terms`

### 3. POST /drafts → 400 (trailing slash / form compatibility)
- [x] Разобраться и исправить — добавлен путь `/drafts/`

### 4. POST .../messages → 422 (session_id / form compatibility)
- [x] Разобраться и исправить — добавлен fallback на form-data

---

### Финальная проверка
- [x] Сверка с todo.md — все 4 пункта выполнены
- [x] Перепросмотр правок — мусора, затираний нет
- [x] Оценка целостности — изменения изолированы, не затрагивают смежные модули
- [x] Покрытие тестами — 550/550 тестов пройдено, 1 предсуществующий баг (test_91, не связан с правками)
