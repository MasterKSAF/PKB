# Todo — Добавление mock-данных для стартового вывода

## Задача
Расширить начальные seed-данные в `common.py`, чтобы при старте сервиса было больше
реалистичных данных для демонстрации/разработки UI.

## План

### 1. Анализ текущих seed-данных
- [x] Прочитаны все handler-файлы и common.py
- [x] Выявлены области с недостаточным количеством seed-данных

### 2. Расширение seed-данных в common.py
- [x] **SEED_DOCUMENTS** +2 (разные статусы: review_required, failed)
- [x] **SEED_DOCUMENT_ERRORS** +3 (для новых документов)
- [x] **SEED_REGISTRY_DOCUMENTS** +2 (разные source_type, eras)
- [x] **SEED_CLASSIFIERS** +5 (MKS и OKSTU)
- [x] **SEED_TERMINOLOGY** +3 (разные term_type)
- [x] **SEED_SESSIONS** +2 (с разными сообщениями)
- [x] **SEED_HISTORY** +3 (для разных сессий)
- [x] **SEED_PROJECTS** — новый seed (3 проекта)
- [x] **SEED_AUDIT** +3 (разные действия)
- [x] **SEED_CATEGORIES** +2
- [x] **SEED_REGISTRY_DRAFTS** — новый seed (2 черновика)

### 3. Обновление init_all_data()
- [x] Добавить инициализацию `_projects` из `SEED_PROJECTS`
- [x] Добавить инициализацию `_registry_drafts` из `SEED_REGISTRY_DRAFTS`
- [x] Установить `_projects_id_seq` равным максимальному ID проекта

### 4. Исправление тестов (выявлено при валидации)
- [x] `test_24_list_documents_filter_type` — исправлен параметр запроса `document_type` → `source_type`
- [x] `test_35_document_queue` — исправлен путь проверки `pipeline` → `item["steps"]["pipeline"]`

### 5. Проверка
- [x] Запущены все 462 теста — **все проходят** ✅
