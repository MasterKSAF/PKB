# todo — разграничение Orchestrator и Registry

## Задача
Чётко разделить ответственность: Registry — данные (CRUD + чтение черновиков и документов),
Orchestrator — только пайплайн (управление жизненным циклом, статус обработки, задачи).

Чтение черновиков и документов уходит из Orchestrator в Registry (прямой доступ через Gateway).

## План

### 1. guide.md — зафиксировать правило разграничения
- [x] Добавить раздел «Разграничение ответственности Orchestrator vs Registry»
- [x] Описать три категории: Registry (данные), Orchestrator (пайплайн), Gateway (маршрутизация)
- [x] Описать internal-эндпоинты Registry (только для Orchestrator)
- [x] Описать правило связки: `GET /{drafts,documents}/{id}/tasks` — всегда Orchestrator

### 2. registry_service_api.md — добавить недостающие эндпоинты
- [x] Добавить публичные GET-эндпоинты draft (чтение) в таблицу методов
- [x] Добавить GET /registry/drafts — список черновиков
- [x] Добавить GET /registry/drafts/{draft_id} — карточка черновика
- [x] Добавить GET /registry/drafts/{draft_id}/preview — preview-метаданные
- [x] Добавить GET /registry/documents/{id}/pages — список страниц
- [x] Добавить GET /registry/documents/{id}/pages/{num} — страница
- [x] Добавить GET /registry/documents/{id}/pages/{num}/text — текст страницы
- [x] Добавить GET /registry/documents/{id}/pages/{num}/preview — превью страницы
- [x] Добавить GET /registry/documents/{id}/file — скачивание файла
- [x] Добавить GET /registry/documents/{id}/history — история статусов
- [x] Добавить GET /registry/documents/{id}/parameters — извлечённые параметры
- [x] Добавить GET /registry/documents/{id}/versions — список версий
- [x] Промаркировать internal-эндпоинты (закрытые от Gateway)

### 3. orchestrator_service_api.md — удалить дублирующиеся read-only эндпоинты
- [x] Удалить описание GET /documents — список документов
- [x] Удалить описание GET /documents/{id} — карточка документа
- [x] Удалить описание GET /documents/{id}/pages/* — страницы
- [x] Удалить описание GET /documents/{id}/file — скачивание
- [x] Удалить описание GET /documents/{id}/history — история
- [x] Удалить описание GET /documents/{id}/parameters — параметры
- [x] Удалить описание GET /documents/{id}/versions — версии
- [x] Удалить описание GET /drafts — список черновиков
- [x] Удалить описание GET /drafts/{draft_id} — карточка черновика
- [x] Удалить описание GET /drafts/{draft_id}/preview — preview-метаданные
- [x] Удалить описание DELETE /documents/{doc_id} — удаление документа
- [x] Удалить описание PUT/PATCH /documents/{doc_id} — обновление документа
- [x] Добавить GET /documents/{id}/tasks — связь документа с задачами
- [x] Добавить GET /drafts/{id}/tasks — связь черновика с задачами (перенести из documents group)
- [x] Обновить примечание в начале: «Orchestrator — только пайплайн и управление»

### 4. gateway_service_api.md — обновить routing table
- [x] Разделить `/api/v1/documents/*` — чтение и CRUD в Registry, статус/очередь/ошибки в Orchestrator
- [x] Разделить `/api/v1/drafts/*` — чтение в Registry, запись/управление в Orchestrator
- [x] Добавить примечание о разграничении (ссылка на guide.md)
- [x] Обновить таблицу маршрутов drafts (только write-эндпоинты)
- [x] Обновить секцию «Маршрутизация черновиков» — убрать описание read
- [x] Обновить sequence diagram (убрать избыточные прокси)

### 5. pipeline1-formation.md — исправить ссылки
- [x] Проверить и исправить ссылки на чтение черновиков (Registry вместо Orchestrator)
- [x] Оставить ссылки на управление черновиками (Orchestrator)

### 6. common_api.md
- [x] Таблица кодов ошибок проверена — принадлежность не изменилась, правки не требуются
- [-] Ссылка на guide.md — отменено (внутреннее, не для common_api.md)

### 7. README.md — обновить описание сервисов
- [x] Gateway — уточнён routing (разделение /documents/* и /drafts/*)
- [x] Orchestrator — уточнена ответственность (только пайплайн)
- [x] Registry — уточнена ответственность (единый источник истины)

### 8. specificity.md
- [x] A23 помечена (resolved)

### 9. Финальная проверка целостности
- [x] check_cross_references.py — PASSED (после обновления expected counts)
- [x] Проверить консистентность ссылок — пройдено (скриптом)
- [x] Проверить read-only удалены из orchestrator — пройдено (скриптом, ожидаемые FAIL устранены)

### 10. Перенос reprocess из Registry в Orchestrator
- [x] Удалить секцию 3.13 `POST /registry/documents/{doc_id}/reprocess` из registry_service_api.md
- [x] Убрать reprocess из таблицы содержания registry_service_api.md
- [x] Добавить `POST /documents/{doc_id}/reprocess` в orchestrator_service_api.md
- [x] Обновить README.md — строка 176 (путь и принадлежность)
- [x] Обновить gateway_service_api.md — routing уже правильный, проверить
- [x] Обновить pipeline1-formation.md, pipeline2-indexation.md, rag_builder_service_api.md — ссылки на Registry
- [x] Обновить common_api.md — ссылка (строка 504)
- [ ] ~~Зафиксировать аномалию в specificity.md~~ — specificity.md не хранит историю правок
