# Пайплайн 3 (Поиск, через Query Service): сценарии поведения

> **Назначение документа.** Описание сценариев поведения Query Service при прогоне Пайплайна 3 (поиск и генерация ответа) и роли Оркестратора в координации. Документ дополняет:
> - [Пайплайн 3: Поиск документа](../pipeline3-search.md) — основной поток, FSM
> - [API Query Service](../../api/query_service_api.md) — эндпоинты Query Service
> - [API RAG Search Service](../../api/rag_search_service_api.md) — детали поиска
>
> Стиль описания: **Ситуация → Поведение Query Service / Оркестратора → Результат / Статус → Код ошибки**.

**Охват документа:** Пайплайн 3 (поиск и генерация). Query Service — владелец пайплайна. Оркестратор — координатор мониторинга и связи с Pipeline 1/2. Пайплайн 1 (формирование) — в [pipeline1-orchestrator_details.md](pipeline1-orchestrator_details.md). Пайплайн 2 (индексация) — в [pipeline2-orchestrator_details.md](pipeline2-orchestrator_details.md).

---

## 0. Общая модель

**Владелец Пайплайна 3 — Query Service** (см. [overview.md §Матрица ответственности](../overview.md#матрица-ответственности-сервисов)). Оркестратор **не участвует** в основном потоке обработки сообщения. Его роль:

1. **Мониторинг** очереди и статуса обработки сообщений (через `pipeline.tasks`).
2. **Связь** Пайплайна 3 с результатами Пайплайна 1/2 (например, документ в статусе `indexed` — иначе RAG Search вернёт пустой результат).
3. **Координация reprocess** при необходимости (если документ не найден в индексе).
4. **Longpoll-агрегация** статуса для UI (`GET /documents/{doc_id}/status`).

**FSM сообщения** (см. [pipeline3-search.md §Статусная модель](../pipeline3-search.md#статусная-модель-fsm)):

```
[*] → idle (виртуальный)
idle → pending (POST .../messages)
pending → enriching → searching → generating → enriching_citations → answered → [*]
       ↘                ↘           ↘            ↘                  ↘
        failed          failed      failed       failed            failed
```

**Состояние FSM хранится в `chat.messages.status`** (см. [specificity.md B6](../../specificity.md) — `chat.messages.status` формализован).

---

## 1. Маршрутизация

| Сценарий | Маршрут | Участники |
|----------|---------|-----------|
| UI отправляет вопрос | `POST /chat/sessions/{session_id}/messages` | UI → **Gateway** → **Query Service** (минуя Оркестратор) |
| UI получает статус сообщения | `GET /chat/sessions/{session_id}/messages/{message_id}?longpoll=15` | UI → **Gateway** → **Query Service** |
| UI получает историю чата | `GET /chat/sessions/{session_id}/messages` | UI → **Gateway** → **Query Service** |
| UI запрашивает статус документа | `GET /documents/{doc_id}/status` | UI → **Gateway** → **Оркестратор** (агрегация статуса) |
| UI запрашивает очередь обработки | `GET /documents/queue` | UI → **Gateway** → **Оркестратор** |
| Query Service вызывает RAG Search | `POST /rag/search` | Query Service → **RAG Search** (минуя Оркестратор и Gateway) |
| Query Service вызывает LLM | `POST <llm_provider>` | Query Service → **LLM Provider** (внешний) |

> **Принцип:** основной поток Пайплайна 3 идёт через Query Service. Оркестратор подключается только для мониторинга и агрегации статуса. Это разделяет ответственность (см. [guide.md §Разграничение ответственности](../../guide.md#разграничение-ответственности-orchestrator-vs-registry)).

---

## 2. Приём сообщения: `POST /chat/sessions/{session_id}/messages`

| Сценарий | Поведение Query Service | Результат | Код |
|----------|-------------------------|-----------|-----|
| Норма | Сохранить сообщение в `chat.messages` со статусом `pending`. Создать запись в `pipeline.tasks` (если требуется мониторинг — best effort) | `202 { message_id, status: "pending" }` | — |
| Сессия не найдена | — | `404 SESSION_NOT_FOUND` | `SESSION_NOT_FOUND` |
| Пустой `content` | — | `400 VALIDATION_ERROR` | `VALIDATION_ERROR` |
| Превышен размер сообщения (например, > 32 КБ) | — | `413 MESSAGE_TOO_LARGE` | `MESSAGE_TOO_LARGE` |
| Нет прав на сессию | (от Gateway) | `403 FORBIDDEN` | `FORBIDDEN` |
| БД `chat.*` недоступна | — | `503 SERVICE_UNAVAILABLE` | `CHAT_DB_UNAVAILABLE` |
| `pending` дольше 30 секунд (per-state таймаут) | Перевести в `failed` | `status: failed` | `MESSAGE_PENDING_TIMEOUT` |
| Абсолютный таймаут 48 часов с момента создания | Scheduler → `failed` | `status: failed` | `MESSAGE_TIMEOUT` |
| Повторный `POST` с тем же `Idempotency-Key` (TTL 1 час) | Вернуть кешированный ответ | `202` (повторно) | — |

> **Per-state таймауты (см. [pipeline3-search.md §Защита от «зависших»](../pipeline3-search.md#защита-от-зависших-сообщений)):**
> - `pending`: 30с → `MESSAGE_PENDING_TIMEOUT`
> - `enriching`: 30с → пропуск обогащения, флаг `enrichment_skipped: true`
> - `searching`: 60с → `failed`
> - `generating`: 180с → retry с truncation
> - `enriching_citations`: 30с → ответ без machine-readable сносок

> **Абсолютный таймаут:** 48 часов с момента создания. Scheduler проверяет каждые 5 минут. Перевод в `failed` с `MESSAGE_TIMEOUT`.

---

## 3. Обогащение запроса: `enriching`

| Сценарий | Поведение Query Service | Результат | Код |
|----------|-------------------------|-----------|-----|
| Норма | Поиск `raw_term → standard_term` через словарь `registry.terminology`. Добавление синонимов | `enriched_query` (массив терминов + синонимы) | — |
| Словарь `registry.terminology` недоступен | **Пропустить обогащение**, продолжить с исходным запросом. В ответе `enrichment_skipped: true` | (продолжение) | `ENRICHMENT_SKIPPED` |
| Частичный результат (найдено 2 из 5 терминов) | Использовать успешно обогащённые термины. Ошибки по отдельным терминам залогировать | (продолжение) | `ENRICHMENT_PARTIAL` |
| Per-state таймаут 30с | Пропустить обогащение, перейти к поиску | (продолжение) | `ENRICHMENT_TIMEOUT` |
| Норма — обогащение завершено | Перевести в `searching` | `status: searching` | — |

---

## 4. Поиск чанков: `searching` (RAG Search)

| Сценарий | Поведение Query Service / RAG Search | Результат | Код |
|----------|--------------------------------------|-----------|-----|
| Норма — найдены чанки | `POST /rag/search` с обогащённым запросом + filters. Гибридный поиск (Dense + Sparse + pg_trgm) или `vector_rerank` (S2, prod-стратегия по умолчанию) | `chunks[]` с `document_id`, `section_id`, `page`, `clause`, `content`, `score` | — |
| RAG Search вернул 5xx | Retry 2 раза (Exponential 500мс → 1с). При исчерпании — `failed` | `status: failed` | `RAG_SEARCH_FAILED` |
| RAG Search таймаут 30с | Retry 2 раза. При исчерпании — `failed` | `status: failed` | `RAG_SEARCH_TIMEOUT` |
| RAG Search вернул пустой результат (`chunks=[]`) | **Не вызывать LLM** (нечего генерировать). Вернуть `answer: null`, `sources: []`, `empty_result: true` | `status: answered` (с `empty_result: true`) | `EMPTY_RESULT` |
| Per-state таймаут 60с | Перевести в `failed` | `status: failed` | `RAG_SEARCH_TIMEOUT` |
| Все документы в запросе не `indexed` (например, в `failed` или `pending_index`) | RAG Search фильтрует `WHERE processing_status = 'indexed'`. Возвращает пустой результат | `empty_result: true` | `NO_INDEXED_DOCUMENTS` |
| Ошибка БД (pgvector) | Retry 2 раза. Fallback на полнотекстовый поиск (если доступен) | (продолжение с fallback) | `FALLBACK_FULLTEXT` |
| Fallback тоже упал | `failed` | `status: failed` | `SEARCH_FULLY_FAILED` |
| Найдено слишком много чанков (> top_k) | Взять top_k по score (настраивается, по умолчанию 10) | (продолжение) | — |

> **Top-k стратегия:** см. `glossary.md §vector_rerank (S2)` — прод-стратегия. Экспериментальные S1–S9 задаются только в `app_settings.rag.search_strategy`, не через API (см. [glossary.md §experimental](../../glossary.md)).

---

## 5. Генерация ответа: `generating` (LLM)

| Сценарий | Поведение Query Service | Результат | Код |
|----------|-------------------------|-----------|-----|
| Норма | Сформировать промпт (вопрос + `top_k` чанков с метаданными), вызвать LLM Provider (по умолчанию `deepseek-4-flash` — см. [glossary.md](../../glossary.md)) | `raw_answer` с `[source:N]` маркерами | — |
| LLM Provider вернул 5xx | Retry 2 раза с **truncation контекста на 20%** перед каждым повтором. При исчерпании — `failed` | `status: failed` | `LLM_GENERATION_FAILED` |
| LLM Provider таймаут 120с | Retry 2 раза с truncation | `status: failed` | `LLM_TIMEOUT` |
| LLM Provider вернул ответ без `[source:N]` маркеров (P4-8) | Retry 2 раза с **усиленным указанием** в промпте. При исчерпании — вернуть ответ без machine-readable цитирований (fallback) + WARN в лог | `enriching_citations` (fallback) | `CITATION_VALIDATION_FAILED` |
| LLM Provider вернул ответ с невалидными `[source:N]` (N >= len(sources)) | Отклонить ответ, retry 2 раза. При исчерпании — fallback на ответ без цитирований | `enriching_citations` (fallback) | `INVALID_SOURCE_INDEX` |
| LLM Provider вернул ответ с пустым `answer` | Не использовать. Retry 2 раза. При исчерпании — `failed` (ответ пустой) | `status: failed` | `LLM_EMPTY_ANSWER` |
| Per-state таймаут 180с | Retry 2 раза. При исчерпании — `failed` | `status: failed` | `LLM_GENERATION_FAILED` |
| Все retry исчерпаны | **Fallback:** вернуть `sources[]` (чанки) с пустым `answer: null`, добавить `partial_answer: true` | `status: answered` (с `partial_answer: true`) | `LLM_FALLBACK_TO_SOURCES` |

> **Параметры LLM по умолчанию (см. [glossary.md §deepseek-4-flash](../../glossary.md)):** temperature 0.2, max_tokens 1024, top_p 0.95. Настраиваются через `app_settings.llm.*`.

> **Truncation на retry:** каждый повтор усекает контекст на 20% (оставляет наиболее релевантные чанки по score). Это баланс между качеством ответа и успешностью retry.

---

## 6. Обогащение цитирований: `enriching_citations`

| Сценарий | Поведение Query Service | Результат | Код |
|----------|-------------------------|-----------|-----|
| Норма | Сопоставить `[source:N]` с массивом `sources` (по индексу N). Сформировать machine-readable сноски по `document_id + section_id` (см. RS-6, [pipeline3-search.md §Этап 4](../pipeline3-search.md#этап-4-обогащение-цитирований-и-сохранение-query-service)) | `answer` с аннотированными сносками | — |
| `chunk_id` в `sources[]` | **Не включать** в сноску (это технический retrieval ID, см. [glossary.md §specificity A47](../../specificity.md)) | — | — |
| Цитирование ссылается на источник, отсутствующий в `sources` | Удалить ссылку | — | `ORPHAN_CITATION_REMOVED` |
| Все цитирования невалидны | Вернуть ответ без machine-readable сносок | `answer` (без сносок) | `ALL_CITATIONS_INVALID` |
| Per-state таймаут 30с | Вернуть ответ без machine-readable сносок | `answer` (без сносок) | `ENRICHING_CITATIONS_TIMEOUT` |
| Ошибка постобработки | Вернуть ответ без machine-readable сносок | `answer` (без сносок) | `POSTPROCESSING_ERROR` |

> **Архитектурное правило (RS-6):** цитирование строится по `document_id + section_id`. `chunk_id` — только технический retrieval ID, **не** для цитирования.

---

## 7. Сохранение и уведомление: `answered`

| Сценарий | Поведение Query Service | Результат | Код |
|----------|-------------------------|-----------|-----|
| Норма | Сохранить ответ в `chat.messages` со статусом `answered`. Вернуть UI через longpoll | `200 { message_id, status: "answered", answer, sources[] }` | — |
| `empty_result: true` (пустой RAG) | Сохранить `answer: null`, `sources: []`, `empty_result: true` | `200` (с `empty_result: true`) | — |
| `partial_answer: true` (fallback LLM) | Сохранить `sources[]` (чанки), `answer: null`, `partial_answer: true` | `200` (с `partial_answer: true`) | — |
| БД `chat.*` недоступна при сохранении | Потеря ответа. UI получит таймаут longpoll | `503 SERVICE_UNAVAILABLE` | `CHAT_DB_UNAVAILABLE` |

> **UI получает ответ через longpoll на конкретное сообщение:** `GET /chat/sessions/{session_id}/messages/{message_id}?longpoll=15`. Держит соединение до 15с.

---

## 8. Связь с Pipeline 1/2

| Сценарий | Поведение Query Service | Результат |
|----------|-------------------------|-----------|
| Документ в `indexed` (норма) | RAG Search возвращает чанки | `searching` → `generating` → `answered` |
| Документ в `indexing` или `pending_index` | RAG Search **не возвращает** чанки этого документа (фильтр `processing_status = 'indexed'`) | `empty_result: true` (если других документов нет) |
| Документ в `failed` (Pipeline 2) | RAG Search не возвращает чанки | `empty_result: true` |
| Документ в `indexed` с `INTEGRITY_CHECK_FAILED` (откат в `failed`) | RAG Search автоматически исключает (см. [pipeline2-orchestrator_details.md §4](pipeline2-orchestrator_details.md#4-integrity-check-целостность-индекса)) | `empty_result: true` |
| Документ ещё не создан (Pipeline 1 не завершён) | RAG Search не возвращает чанки | `empty_result: true` |
| Документ создан, но новая версия (через `POST /versions`) в `indexing` | RAG Search возвращает чанки **только** для `current_version_id`-версии | `answered` (с учётом текущей версии) |

> **Роль Оркестратора в координации:** если пользователь сообщает о проблеме с поиском ("не находит документ, который точно есть"), Оркестратор через `GET /documents/{doc_id}/status` показывает фактический статус (например, `failed` после integrity check). UI предлагает `reprocess` (`POST /documents/{doc_id}/reprocess mode=reindex`).

---

## 9. Роль Оркестратора в мониторинге

| Эндпоинт | Назначение | Возвращает |
|----------|------------|------------|
| `GET /documents/{doc_id}/status` | Агрегированный статус документа (Pipeline 1 + Pipeline 2) | `status: processing / approval_required / completed` (UI-агрегация) |
| `GET /documents/queue` | Очередь обработки документов (Pipeline 1 в активной фазе) | `queue[]` с `document_id`, `status`, `progress_percent`, `current_step` |
| `GET /documents/{doc_id}/errors` | История ошибок (все ретраи, финальные ошибки) | `errors[]` с `error_id`, `stage`, `error_code`, `retry_attempt`, `timestamp` |
| `GET /tasks` | Все задачи пайплайнов (admin) | `items[]` с `task_id`, `pipeline_stage`, `status` |
| `GET /tasks/{task_id}/status` | Статус конкретной задачи с longpoll | `status`, `progress_percent`, `steps[]` |
| `GET /tasks/{task_id}/steps` | Все шаги задачи (для аудита, debug) | `steps[]` с `step_name`, `service_name`, `input_data`, `output_data` |

> **Важно:** Пайплайн 3 (поиск) **не создаёт** записей в `pipeline.tasks` в текущей реализации. Эти записи принадлежат Pipeline 1/2. Мониторинг Пайплайна 3 — через `chat.messages.status` (Query Service владеет).

> **Longpoll-агрегация:** `GET /documents/{doc_id}/status` поддерживает `?longpoll=15` (см. [common_api.md](../../api/common_api.md)). Оркестратор агрегирует статусы Pipeline 1/2 и отдаёт UI. При `status=completed` — UI получает финальный ответ.

---

## 10. Висящие состояния и таймауты

| Состояние | Таймаут | Действие | Код |
|-----------|---------|----------|-----|
| `pending` | 30 с | `failed` | `MESSAGE_PENDING_TIMEOUT` |
| `enriching` | 30 с | Пропуск обогащения | `ENRICHMENT_TIMEOUT` |
| `searching` | 60 с | `failed` | `RAG_SEARCH_TIMEOUT` |
| `generating` | 180 с | Retry с truncation (до 2 раз) | `LLM_GENERATION_FAILED` |
| `enriching_citations` | 30 с | Ответ без machine-readable сносок | `ENRICHING_CITATIONS_TIMEOUT` |
| Абсолютный (любое состояние) | 48 часов | Scheduler → `failed` | `MESSAGE_TIMEOUT` |

> **Связь с L1-15 (см. [pipeline3-search.md §Защита от «зависших»](../pipeline3-search.md#защита-от-зависших-сообщений)):** per-state таймауты **и** абсолютный 48-часовой таймаут работают совместно. Per-state предотвращают зависание на конкретной стадии, абсолютный — защищает от забытых сообщений.

---

## 11. Идемпотентность и повторные вызовы

| Сценарий | Поведение Query Service | Результат | Код |
|----------|-------------------------|-----------|-----|
| Повторный `POST /messages` с тем же `Idempotency-Key` (TTL 1 час) | Вернуть кешированный `message_id` и `status` | `202` (повторно) | — |
| `GET /messages/{id}` (longpoll) с того же `Idempotency-Key` | Вернуть кешированный ответ | `200` (повторно) | — |
| UI повторно открывает сессию | Вернуть всю историю сообщений | `200` | — |
| Пользователь повторно отправляет тот же вопрос | Создать новое сообщение (без дедупликации) | `202` (новый `message_id`) | — |
| `POST /feedback` с `Idempotency-Key` | Идемпотентно сохранить feedback | `200` | — |

> **Важно:** сообщения **не редактируются** (см. [guide.md §Редактирование сообщений не поддерживается](../../guide.md#редактирование-сообщений-не-поддерживается)). Пользователь может отправить новое сообщение с правками.

---

## 12. Журналирование

| Артефакт | Хранилище | Назначение |
|----------|-----------|------------|
| `chat.sessions` | Query Service DB | Сессии чата |
| `chat.messages` | Query Service DB | Сообщения: `message_id`, `session_id`, `content`, `answer`, `sources`, `status`, `created_at` |
| `chat.message_history` | Query Service DB | История изменений (если ведётся) |
| `chat.feedback` | Query Service DB | Оценки пользователя (rating, comment) |
| `audit.events` | Audit DB | Аудит: кто, что, когда, результат |

> **Поведение Query Service:**
> - На каждом этапе — обновление `chat.messages.status`.
> - При `failed` — запись `error_code` и `error_message`.
> - При `enrichment_skipped`, `partial_answer`, `empty_result` — флаги в `chat.messages.flags` (или эквивалент).
> - `severity: ERROR` — для всех `failed` переходов и невозможности retry.
> - `severity: WARNING` — для `enrichment_skipped`, `partial_answer`, `citation_validation_failed`.

---

## 13. Сводка HTTP-кодов ошибок

| HTTP | Код | Когда |
|------|-----|-------|
| 400 | `VALIDATION_ERROR` | Некорректные поля |
| 400 | `EMPTY_CONTENT` | Пустой `content` |
| 400 | `INVALID_FEEDBACK` | Некорректный `rating` |
| 401 | `UNAUTHORIZED` | Нет JWT (от Gateway) |
| 403 | `FORBIDDEN` | Нет прав (от Gateway) |
| 404 | `SESSION_NOT_FOUND` | Нет сессии |
| 404 | `MESSAGE_NOT_FOUND` | Нет сообщения |
| 413 | `MESSAGE_TOO_LARGE` | > 32 КБ |
| 422 | `UNSUPPORTED_QUERY_TYPE` | Неподдерживаемый тип запроса |
| 500 | `LLM_GENERATION_FAILED` | LLM упал после retry |
| 500 | `LLM_EMPTY_ANSWER` | LLM вернул пустой ответ |
| 500 | `RAG_SEARCH_FAILED` | RAG Search упал |
| 500 | `SEARCH_FULLY_FAILED` | Все fallback упали |
| 502 | `LLM_PROVIDER_UNAVAILABLE` | LLM Provider 5xx |
| 502 | `RAG_SEARCH_UNAVAILABLE` | RAG Search 5xx |
| 503 | `SERVICE_UNAVAILABLE` | chat DB / pgvector недоступны |
| 504 | `LLM_TIMEOUT` | LLM Provider таймаут |
| 504 | `RAG_SEARCH_TIMEOUT` | RAG Search таймаут |
| (таймаут) | `MESSAGE_PENDING_TIMEOUT` | `pending` > 30с |
| (таймаут) | `MESSAGE_TIMEOUT` | Абсолютный 48ч |
| (fallback) | `ENRICHMENT_SKIPPED` | Словарь недоступен |
| (fallback) | `PARTIAL_ANSWER` | LLM упал, вернули sources |
| (fallback) | `EMPTY_RESULT` | RAG ничего не нашёл |
| (fallback) | `CITATION_VALIDATION_FAILED` | LLM не прошёл валидацию |

---

## 14. Связь с Оркестратором (через `pipeline.tasks`)

| Сценарий | Поведение Query Service | Поведение Оркестратора |
|----------|-------------------------|------------------------|
| Создание сообщения (`pending`) | Запись в `chat.messages`, `status=pending` | — (не участвует) |
| `searching` на документе в `failed` (Pipeline 2) | RAG Search возвращает пустой результат | — |
| Пользователь жалуется "не находит документ" | UI вызывает `GET /documents/{doc_id}/status` | Возвращает `status: failed` (после integrity check) с `error_code: INTEGRITY_CHECK_FAILED` |
| Пользователь инициирует `reprocess` | UI вызывает `POST /documents/{doc_id}/reprocess mode=reindex` | Запускает `DELETE /rag/build/{doc_id}` → `POST /rag/build`. См. [pipeline2-orchestrator_details.md §7](pipeline2-orchestrator_details.md#7-reprocess-post-documentsdoc_idreprocess-modereindex) |
| Документ переиндексирован (`indexed` снова) | — (RAG Search автоматически подхватывает новые чанки) | — |
| Сообщение `answered`, UI открывает документ | UI вызывает `GET /documents/{doc_id}` | — (Gateway → Registry) |

> **Принцип:** Query Service **не знает** о статусе Pipeline 1/2. RAG Search фильтрует `processing_status = 'indexed'` на уровне БД. Если документ не в `indexed` — RAG Search вернёт пустой результат, Query Service обработает его как `empty_result: true`. Это снижает связанность.

---

## 15. Связанные спецификации и файлы

- [Пайплайн 3: Поиск документа](../pipeline3-search.md) — основной поток
- [Сводный обзор пайплайнов](../overview.md) — общая картина
- [API Query Service](../../api/query_service_api.md) — эндпоинты
- [API RAG Search Service](../../api/rag_search_service_api.md) — детали поиска
- [API Orchestrator Service](../../api/orchestrator_service_api.md) — мониторинг
- [Пайплайн 1: сценарии поведения Оркестратора](pipeline1-orchestrator_details.md)
- [Пайплайн 2: сценарии поведения Оркестратора](pipeline2-orchestrator_details.md)
- [Разграничение ответственности](../../guide.md#разграничение-ответственности-orchestrator-vs-registry)
- [Глоссарий: RAG-стратегии, LLM, embedding](../../glossary.md) — терминология
- [Specificity.md: B6, L1-15, A46, A47](../../specificity.md) — открытые вопросы
