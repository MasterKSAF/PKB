# План

## Выполнено

### 1. db_check: ложное ❌ на UNIQUE-индекс RAG Builder ✅
- **Файл:** `core/db_check.py`
- **Что:** убрал `rag.document_chunks_section_chunk_key` из `EXPECTED_UNIQUE_INDEXES` — индекс намеренно удалён из RAG Builder
- **Результат:** `UNIQUE-индексы | ✅ | 28 найдено`

### 2. reports: ❌ в сводной таблице при skipped шагах ✅
- **Файл:** `core/reports.py`
- **Что:** 
  - Изменил сбор статуса с `[passed, total]` на `[passed, total, failed]`
  - Иконка теперь по `p_failed == 0` вместо `p_passed == p_total`
- **Результат:** pipelines со skipped шагами (5/6, 10/11) показывают ✅

### 3. guide.md: правило о запрете сокрытия ошибок ✅
- Добавлен раздел "Запрет на сокрытие ошибок сервисов"
- Явно перечислено что считается/не считается сокрытием

## Осталось (не checker)
- **Query Service:** 1 эндпоинт падает в API Coverage (не связано с нашими правками)
- **Registry PATCH /documents/{id}:** ждём фикса от разработчика
