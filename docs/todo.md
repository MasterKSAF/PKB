# Todo: Синхронизация API RAG Builder с пайплайнами

## Задача
Проверить и исправить соответствие `rag_builder_service_api.md` описаниям пайплайнов (pipeline2-indexation.md, overview.md) и смежных API (orchestrator_service_api.md, registry_service_api.md).

## Результат

### 1. 🔴 `rag_builder_service_api.md` — `POST /rag/build` переведён на асинхронную модель
- [x] Код ответа: `201` → `202`
- [x] Добавлен `task_id` в ответ
- [x] Статус в ответе: `completed` → `indexing` (нефинальный)
- [x] Таблица кодов: `201 — Индексация запущена` → `202 — Индексация запущена (асинхронно)`

### 2. 🔴 `rag_builder_service_api.md` + `pipeline2-indexation.md` — унификация статусов
- [x] В ответе `POST /rag/build`: `completed` → `indexing` (промежуточный)
- [x] В `GET /rag/build/{doc_id}/status`: сохранён `indexed` как финальный
- [x] В longpoll pipeline2-indexation.md: `status: completed` → `status: indexed` (2 места)
- [x] В sequence-диаграмме pipeline2-indexation.md: `completed` → `indexed`
- [x] В описании выхода этапа pipeline2-indexation.md: `completed/failed` → `indexed/failed`

### 3. 🟡 `rag_builder_service_api.md` — таблица полей запроса
- [x] Добавлен `protected_spans` (массив объектов)
- [x] Добавлен `options` (object) + `options.strategy`
- [x] Добавлены `sections[].document_id`, `sections[].clause`, `sections[].title`, `sections[].level`, `sections[].page`

### 4. 🟡 `rag_builder_service_api.md` — тип `document_id`
- [x] В таблицах ответов `document_id` исправлен с `string` на `bigint`

### 5. 🟡 `orchestrator_service_api.md` — уточнение статусов
- [x] Описание FSM уточнено: «Статусы документов (FSM) для Indexation: `pending_index` → ...»
- [x] `indexation.status` и `rag_indexing.status` остались как `pending`/`completed` (это статусы шагов Оркестратора)

### 6. ⚪ `pipeline2-indexation.md` — интеграция DELETE в workflow
- [x] Добавлен раздел «Переиндексация» с описанием вызова `DELETE /rag/build/{doc_id}`

### 7. ⚪ `rag_builder_service_api.md` — уточнение источника данных
- [x] Фраза скорректирована: Orchestrator получает JSON из Registry и передаёт в RAG Builder

### 8. ⚪ `rag_builder_service_api.md` — `protected_spans` и `options` в описание
- [x] Добавлено описание `protected_spans` и `options.strategy` в тело документации

### 9. 📝 `specificity.md`
- [x] Запись B7 разделена: RAG Builder — синхронизирован, Auth Service и RAG Search — остаются

### 10. ⚪ Дополнительные правки по результатам финальной проверки
- [x] `pipeline2-indexation.md`: удалено упоминание статуса `partially_indexed` (согласно решению X3)
- [x] `orchestrator_service_api.md`: добавлена секция «Особенности переиндексации» в `POST /documents/{doc_id}/reprocess` с описанием вызова DELETE
- [x] `orchestrator_service_api.md`: `embeddings: 34` → `embeddings: 31` (согласование с примером RAG Builder)
