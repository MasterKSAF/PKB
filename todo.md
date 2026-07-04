# Сессия: фикс дублей file_hash_sha256 ✅

## Сделано

### Проблема: почему были дубли
1. **`approve_draft`** не передавал `file_hash_sha256` в `doc_payload` → NULL в БД
2. **PostgreSQL** UNIQUE constraint не работает на NULL → дубли множились
3. **`create_draft`** проверял только `is_duplicate_file` (активные черновики), не `is_duplicate_document`
4. **`registry.drafts`** не имел колонки `file_hash_sha256` — хэш терялся после создания черновика
5. **`base_client.py`** — `ConnectError` и `CircuitBreakerError` маскировались mock-response вместо re-raise

### Исправления

| Файл | Изменение |
|------|-----------|
| `orchestrator/.../base_client.py` | `ConnectError` и `CircuitBreakerError` → **raise**, а не fallback к моку |
| `orchestrator/.../drafts.py` | Проверка `is_duplicate_document` → 409 `DUPLICATE_DOCUMENT` |
| `orchestrator/.../drafts.py:683` | `get_draft` возвращает `file_hash_sha256` |
| `orchestrator/.../orchestrator.py:1295` | `doc_payload["file_hash_sha256"]` из `draft_data` (Registry) |
| `registry/.../models/draft.py` | Колонки `file_hash_sha256`, `title_hash_sha256`, `title_key` |
| `registry/.../crud/draft.py` | Сохранение `file_hash_sha256` при create_draft |
| `registry/.../schemas/draft.py` | `file_hash_sha256` в DraftSchema |
| `registry/.../routes.py` | Передача полей в CRUD |
| `data/tests/test_file_hash_dedup.py` | **Новый** E2E тест (9/9 PASS) |
| `data/tests/config.py` | `TEST_CLEANUP` / `cleanup_enabled()` |
| `data/tests/test_pdf_tests_full.py` | Параметризация директории, auto-approve |

### Миграция БД
```sql
ALTER TABLE registry.drafts ADD COLUMN file_hash_sha256 TEXT;
ALTER TABLE registry.drafts ADD COLUMN title_hash_sha256 TEXT;
ALTER TABLE registry.drafts ADD COLUMN title_key TEXT;
```
