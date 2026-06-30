# Тестирование загрузки документов и дублей

## Результаты проверки (2026-07-01)

### 1. Загрузка PDF — базовая
- `2-020101-004.pdf` — Upload (HTTP 202) + Preview — OK
- `gost_22786-77.pdf` — Upload (HTTP 202) + Preview — OK

### 2. Дубли (НЕ РАБОТАЕТ)
- `test_dup_check.py`: оба PDF создают разные draft_id при повторной загрузке
- Причина: `check_document_uniqueness` проверяет только таблицу `Document`, не `Draft`, `is_duplicate_file` = False всегда

### 3. Pipeline Registry → Orchestrator → RAG Builder (СЛОМАН)
- `run_registry_step` вызывает `POST /api/v1/registry/documents` → **400 Bad Request**
- Причина: `create_pipeline_document` ожидает `document.metadata.title` и `document.metadata.doc_code`, но конвертер отдаёт другой формат
- Registry не сохраняет секции → Orchestrator не может их прочитать → RAG Builder не получает данные
- Статус документа остаётся "uploaded" вместо "validating"

### 4. Отображение в реестре
- Документы видны в `/api/v1/registry/documents`, но с неполными данными
- Секции (sections) — 0, chunk_count — N/A

### Исправлено
- (ничего не исправляли, только диагностика)
