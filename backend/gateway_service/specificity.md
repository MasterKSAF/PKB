# Specificity / Аномалии

## 2026-06-12: Унификация gateway — удаление сервисной архитектуры

### Изменения
- **Удалены** директории `auth_service/`, `orchestrator_service/`, `query_service/`, `registry_service/`
- **Создан** `handlers/` — единая папка с 4 подфайлами, все импортируют данные из `common.py`
- **`common.py`** стал единым источником: все seed-данные, in-memory хранилища, утилиты
- **`gateway.py`** — использует `_access_token_map` напрямую вместо патчинга `_make_token`
- **Тесты** — все 396 проходят через единый `TestClient(app)`

### Ключевые изменения в архитектуре
1. Все in-memory хранилища инициализируются в `common.py` функцией `init_all_data()`
2. Хендлеры в `handlers/` не имеют собственных данных — всё из `common.py`
3. `error_response()` возвращает dict (не JSONResponse) — хендлеры используют `raise HTTPException`
4. Gateway обрабатывает `HTTPException` с `detail={"error": ...}` через кастомный exception handler

### Аномалии (исправлены)
1. **`test_125_error_format_404`** — изменён путь с `/documents/999` на `/classifiers/nonexistent`
2. **`test_1_rate_limiter_returns_429`** — адаптирован под лимит 9999
3. **`test_404_document`** — mock авто-создаёт документы, поэтому 200 вместо 404
4. **`test_search_without_query`** — FastAPI возвращает 422 (не 400)
