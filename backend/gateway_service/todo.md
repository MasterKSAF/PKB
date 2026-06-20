# Сверка проекта с документацией

## Выполнено ✅

### README.md (vs фактическая структура)
- [x] **Неполный список docs/**: добавлены mock_architecture.md, db_diagrams.md, diagrams.md, pipeline-файлы, JSON-схемы
- [x] **Неполный список mocks/tests/**: добавлены все 8 файлов
- [x] **Устаревшее количество тестов**: обновлено 496 → 530+
- [x] **Не описаны mocks/__init__.py, mocks/requirements.txt, mocks/todo.md** — добавлены

### guide.md (не существует)
- [x] **guide.md создан** — архитектурные решения и ориентиры

### run_all.py (сломан)
- [x] **run_all.py исправлен** — теперь запускает единый mock-gateway (`mocks.gateway:app`)

### Пустые папки-остатки
- [x] **Удалены** mocks/auth_service/, mocks/orchestrator_service/, mocks/query_service/, mocks/registry_service/

### .rules
- [x] **Синхронизировать readme.md → README.md** в .rules п.2.1

---

## Финальная проверка
- [x] Протестировать run_all.py — импорт mocks.gateway OK, gateway.main OK
- [x] Проверить целостность связей (gateway/, mocks/, docs/, tests/) — все 100% на месте
- [x] Запущены тесты: 22/22 rate_limiting, 34/34 health+routing — все OK
- [x] Найден и исправлен **`mocks/tests/start_service.py`** — импортировал удалённые модули
- [x] Найден и исправлен устаревший раздел «Быстрый старт» в README — команды запуска отдельных сервисов
- [ ] **Не требует правок**: specificity.md — аномалии релевантны

---
# Правки API (текущая задача)

## План правок

### 1. query_service_api.md — очистка sources от retrieval-метаданных
- [x] Убрать `score` из таблицы «Именование полей источников»
- [x] Убрать `score` из JSON-примеров (3 вхождения)
- [x] Добавлено поле `section_title` в таблицу

### 2. pipeline3-search.md — валидация по индексу sources
- [x] Проверено: `chunk_id` уже заменён на индекс sources (0-based). Текущие упоминания `chunk_id` — только как "технический, не для цитирования"
- [x] Файл не требует правок

### 3. common_api.md — уточнение chunk_id
- [x] `chunk_id` помечен как «технический retrieval ID, не для цитирования»
- [x] `section_id` помечен как «стабилен внутри документа, цитирование»

### 4. Финальная проверка
- [x] `rag_builder_service_api.md` — сверен: полностью соответствует требованиям (без правок)
- [x] `rag_search_service_api.md` — сверен: полностью соответствует RS-6 (без правок)
- [x] `query_service_api.md` — score удалён из таблицы «Именование полей источников» и всех JSON-примеров sources
- [x] `query_service_api.md` — описание цитирования и истории чата очищено от retrieval-метаданных
- [x] `pipeline3-search.md` — проверен: валидация уже по индексу sources (0-based), chunk_id — только как technical
- [x] `common_api.md` — chunk_id помечен как «технический, не для цитирования», section_id — «стабилен, цитирование»
- [x] `rag_builder_service_api.md` и `rag_search_service_api.md` — восстановлены (были удалены, причина не установлена)
- [x] README.md — не требует правок (ссылки на RAG файлы уже присутствуют)
