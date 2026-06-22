# API Нейроассистента ПКБ (v1.0)

### Общие положения

- Базовый URL (через Gateway): `http://127.0.0.1:8080/api/v1`

- Базовый URL для внутренних запросов (напрямую к сервису): `http://127.0.0.1:{port}/api/v1`

- Формат данных: `application/json`, для загрузки файлов – `multipart/form-data`

### HTTP-заголовки

| Заголовок | Обязательность | Описание |
|-----------|---------------|----------|
| `Authorization: Bearer <token>` | Да (кроме `/auth/*` и `/system/health`) | JWT-токен доступа |
| `Content-Type` | Да | `application/json` (для JSON), `multipart/form-data` (для загрузки файлов) |
| `Accept` | Нет | `application/json` (по умолчанию) |
| `Idempotency-Key` | Для POST /drafts и POST /chat/* | UUIDv4 для идемпотентности |
| `X-Request-ID` | Нет | Correlation ID для трассировки |

### Версионирование API

- Путь: `/api/v{major}.{minor}` в URL (например, `/api/v1`).
- **Breaking changes** (несовместимые изменения) — новая major-версия (`/api/v2`).
- **Backward-compatible changes** (добавление полей, новых эндпоинтов) — minor-версия без смены URL.
- Предыдущая major-версия поддерживается не менее 6 месяцев после выхода новой.
- Между внутренними сервисами версионирование не применяется — все внутренние вызовы используют `/api/v1`.

### Порты сервисов

| Сервис | Порт |
|--------|------|
| **Gateway** | **`8080`** |
| Orchestrator | `8081` |
| Auth | `8082` |
| Query | `8083` |
| Registry | `8084` |
| Integration | `8085` |
| Converter-Validator | `8086` |
| Parser | `8087` |
| OCR | `8088` |
| Analyse | `8089` |
| RAG Builder | `8090` |
| RAG Search | `8091` |

### Мониторинг (Health Check)

Каждый микросервис предоставляет endpoint `GET /health` для проверки своего состояния.
Эндпоинт используется:
- **Orchestrator** — для агрегации статусов в `GET /health`;
- **Инфраструктурными системами** (Kubernetes liveness/readiness probes, системы мониторинга).

**Формат ответа (`200 OK`):**

```json
{
  "status": "ok",
  "service": "auth-service",
  "version": "1.0.0"
}
```

**Возможные значения `status`:**

| Статус | Описание |
|--------|----------|
| `ok` | Сервис работает нормально |
| `degraded` | Сервис работает с ограничениями (например, недоступна зависимость) |
| `error` | Сервис не может обрабатывать запросы |

**Поля ответа:**

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | Статус сервиса: `ok`, `degraded`, `error` |
| `service` | string | Идентификатор сервиса (см. таблицу портов) |
| `version` | string | Версия сервиса |

**Эндпоинты по сервисам:**

| Сервис | Внутренний URL | URL через Gateway |
|--------|----------------|-------------------|
| Gateway | `http://127.0.0.1:8080/api/v1/system/health` | — (собственный) |
| Gateway | `http://127.0.0.1:8080/api/v1/monitor/metrics` | — (собственный) |
| Orchestrator | `http://127.0.0.1:8081/api/v1/health` | — (внутренний) |
| Auth | `http://127.0.0.1:8082/api/v1/health` | — (внутренний) |
| Query | `http://127.0.0.1:8083/api/v1/health` | — (внутренний) |
| Registry | `http://127.0.0.1:8084/api/v1/health` | — (внутренний) |
| Integration | `http://127.0.0.1:8085/api/v1/health` | — (внутренний) |
| Converter-Validator | `http://127.0.0.1:8086/api/v1/health` | — (внутренний) |
| Parser | `http://127.0.0.1:8087/api/v1/health` | — (внутренний) |
| OCR | `http://127.0.0.1:8088/api/v1/health` | — (внутренний) |
| Analyse | `http://127.0.0.1:8089/api/v1/health` | — (внутренний) |
| RAG Builder | `http://127.0.0.1:8090/api/v1/health` | — (внутренний) |
| RAG Search | `http://127.0.0.1:8091/api/v1/health` | — (внутренний) |

> **Примечание:** Эндпоинт `/health` Orchestrator'а агрегирует статусы внутренних сервисов,
> обращаясь к их `/health` и возвращая сведённый результат. Для внутренних сервисов
> эндпоинт `/health` не имеет ограничений rate limiting и не требует аутентификации.

> **⚠️ Безопасность**: Health endpoint (`/system/health`) должен возвращать минимальный ответ `{"status": "ok"}` для неаутентифицированных запросов. Полная информация о версиях сервисов — только для `system_admin`.

### Идентификаторы

| Идентификатор | Тип | Назначается | Используется в URL |
|---|---|---|---|
| `draft_id` | bigint (sequence) | Registry при создании записи черновика (`registry.drafts`) | `/drafts/{draft_id}/...` (через Gateway → Orchestrator) |
| `task_id` | bigint (sequence) | Оркестратором при создании задачи (`pipeline.tasks`) | Внутренний (internal) — `/tasks/{task_id}/...` |
| `document_id` | bigint (sequence) | Registry при создании карточки документа | `/documents/{document_id}/...` (после записи в Registry) |
| `version_id` | bigint (sequence) | Оркестратором при создании новой версии | В ответах `POST /documents/{doc_id}/versions` |
| `project_id` | bigint (sequence) | Query Service при создании проекта | `/chat/projects/{project_id}/...` |
| `section_id` | bigint | Registry (sequence) при сохранении секции | В ответах Registry, RAG Builder |
| `chunk_id` | bigint | RAG Builder при индексации | В ответах RAG Search |
| `session_id` | bigint | Query Service при создании сессии чата | `/chat/sessions/{session_id}/...` |
| `message_id` | bigint | Query Service при создании сообщения | `/chat/sessions/{session_id}/messages/{message_id}` |
| `history_id` | bigint (sequence) | Registry при записи события аудита | В ответах API аудита/истории |

**Жизненный цикл идентификаторов:**
1. `draft_id` (bigint) — назначается Registry при создании записи черновика (`registry.drafts`). Внешний ID для preview и решения через `/drafts/{draft_id}/...`
2. `task_id` (bigint) — назначается Оркестратором при создании задачи (`pipeline.tasks`). Внутренний ID задачи, агрегирует этапы (`task_steps`) с входными/выходными данными сервисов
3. `document_id` (bigint) — назначается Registry при создании карточки документа
4. После записи в Registry все операции переключаются на `/documents/{document_id}/...`
5. Оркестратор хранит маппинг `draft_id → task_id → document_id`

Аутентификация:
  - **Эндпоинты через Gateway:** все запросы, кроме `/auth/*`, требуют заголовок
    `Authorization: Bearer <access_token>`. Токен получается через `/auth/token`.
  - **Внутренние сервисы (межсервисное взаимодействие):** вызовы между микросервисами выполняются
    по внутренней сети `127.0.0.1:{port}`.

---

### Межсервисное взаимодействие

Авторизацию контролирует только Gateway. Внутренние сервисы не имеют своей аутентификации — доверенные, общаются напрямую.

#### Заголовки для сквозной трассировки

| Заголовок | Генерирует | Передаётся | Описание |
|-----------|------------|------------|----------|
| `X-Request-ID` | Gateway (если отсутствует) | Через все сервисы | UUIDv4, уникальный для каждого внешнего запроса |
| `X-Trace-ID` | OpenTelemetry SDK | Все спаны | Соответствует trace_id в OTLP |
| `X-Draft-ID` | Orchestrator | Internal services | Текущий draft_id в обработке (если применимо) |
| `X-Document-ID` | Orchestrator/Registry | Internal services | Текущий document_id в обработке |
| `X-Version-ID` | Orchestrator | Internal services | Текущий version_id в обработке |

---

## Обзор конвейера обработки документов
### Формат ответа

#### API Gateway (внутренние сервисы, доступные через Gateway)
> **Примечание:** RAG Builder и RAG Search — внутренние сервисы. Доступ к RAG-функциональности осуществляется через Query Service (далее через Gateway).

Успех — данные возвращаются напрямую (без обёртки). Поле `data` / `items` / именованная коллекция опционально — используется для группировки с `meta` или когда ответ не является списком/объектом напрямую.

Поле `meta` на верхнем уровне содержит пагинацию:

```json
{
  "items": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "page_size": 50
  }
}
```



#### Формат ошибок

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Документ не найден",
    "details": {}
  }
}
```

**Политика локализации:**
- `error.message` — человекочитаемое описание на **русском языке** для отображения в UI конечному пользователю.
- `error.code` — машиночитаемый идентификатор (на английском, `UPPER_SNAKE_CASE`) для обработки в клиентской логике.
- При добавлении мультиязычности `message` будет определяться по заголовку `Accept-Language`, `code` остаётся неизменным.

**Поля `details`:**

| Поле | Тип | Когда присутствует | Описание |
|------|-----|--------------------|----------|
| `retry_after_seconds` | int | HTTP `429 Too Many Requests` | Время ожидания до следующей попытки |
| `validation_errors` | array | HTTP `400 VALIDATION_ERROR` | Спислок ошибок валидации полей: `[{field, reason, value?, constraint?}]` |
| `conflict_document_id` | bigint | HTTP `409 DUPLICATE_DOCUMENT` | ID документа-дубликата |
| `failed_endpoint` | string | HTTP `502 BAD_GATEWAY` / `504 GATEWAY_TIMEOUT` | Эндпоинт, на котором произошла ошибка |
| `failed_service` | string | HTTP `502 BAD_GATEWAY` / `504 GATEWAY_TIMEOUT` | Сервис, на котором произошла ошибка |

**Пример ошибки валидации (`400 VALIDATION_ERROR`):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Ошибка валидации полей",
    "details": {
      "validation_errors": [
        {"field": "title", "reason": "max_length", "value": "... (очень длинный текст)", "constraint": "1024"},
        {"field": "era", "reason": "invalid_enum", "value": "ussr", "constraint": "USSR, CIS, RF, CURRENT"}
      ]
    }
  }
}
```

**Запрещено включать в `details`:** `stack_trace`, `internal_message`, `sql_query`, `file_path`, `config_value` — любые внутренние данные сервера.

Если дополнительных данных нет — `details: {}` (пустой объект).

---

### Пагинация

Параметры пагинации для всех list-эндпоинтов:

| Параметр    | Тип | По умолчанию | Описание                      |
| ----------- | --- | ------------ | ----------------------------- |
| `page`      | int | 1            | Номер страницы                |
| `page_size` | int | 50           | Записей на странице (max 200) |

Поля `meta`:

| Поле        | Тип | Описание                 |
| ----------- | --- | ------------------------ |
| `total`     | int | Общее количество записей |
| `page`      | int | Текущая страница         |
| `page_size` | int | Размер страницы          |

---

### Модель выполнения (sync / async)

API поддерживает две модели выполнения:

| Модель                         | HTTP-код ответа | Описание                                                                                                         | Примеры                                                 |
| ------------------------------ | --------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Синхронная**                 | `200` / `201`   | Результат готов в теле ответа                                                                                    | `GET /documents`, `POST /chat/sessions/{session_id}/messages`, `POST /auth/token`  |
| **Асинхронная (longpoll)**     | `202`           | Запрос принят, сервер возвращает идентификатор отслеживания (для `POST /drafts` — `draft_id`, для внутренних операций — `task_id`). Клиент ожидает результат через longpoll-запрос с переданным таймаутом. | `POST /drafts`, `POST /documents/{doc_id}/reprocess` |

#### Асинхронная модель (longpoll)

После получения `202 Accepted` клиент вызывает GET-статус endpoint с параметром `longpoll`:

```
GET .../{doc_id}/status?longpoll=15
```

| Параметр    | Тип | По умолчанию | Описание                                                                                 |
| ----------- | --- | ------------ | ---------------------------------------------------------------------------------------- |
| `longpoll`  | int | `15`         | Максимальное время ожидания в секундах. Допустимые значения: `0` (синхронный режим) — `60`. При `0` сервер возвращает текущий статус немедленно. При превышении `60` сервер ограничивает до `60`. Если задача завершится раньше — ответ придёт сразу. |

**Логика сервера:**

1. Получить текущий статус задачи.
2. Если задача уже завершена — сразу вернуть результат.
3. Если задача выполняется — ожидать до `longpoll` секунд:
   - **Статус изменился / задача завершилась** → вернуть ответ с прогрессом или результатом.
   - **Таймаут истёк** → вернуть текущий статус и прогресс.
4. Клиент, получив нефинальный статус, повторяет longpoll-запрос с тем же таймаутом.

**Ответы сервера:**

| Сценарий | HTTP | Ответ |
| -------- | ---- | ----- |
| Задача завершилась | `200` | `{"status": "completed", "result": {...}}` |
| Статус изменился | `200` | `{"status": "processing", "progress_percent": 60}` |
| Таймаут истёк | `200` | `{"status": "processing", "progress_percent": 45}` |

---

### Коды ответов HTTP и ошибок

| HTTP-код | Код ошибки (`error.code`) | Описание                                          | Сервис                 |
| -------- | ------------------------- | ------------------------------------------------- | ---------------------- |
| 200      | —                         | Успех                                             | все                    |
| 201      | —                         | Создан ресурс                                     | все                    |
| 202      | —                         | Запрос принят (асинхронная обработка)             | Orchestrator           |
| 400      | `BAD_REQUEST`             | Неверные параметры запроса                        | все                    |
| 400 | `VALIDATION_ERROR` | Ошибка валидации полей запроса (некорректный JSON, неверный тип, обязательное поле отсутствует) | все                    |
| 401      | `UNAUTHORIZED`            | Нет доступа — клиент не известен                  | все                    |
| 401      | `INVALID_TOKEN`           | Токен недействителен или истёк                    | Auth                   |
| 403      | `FORBIDDEN`               | Нет доступа — нет прав на ресурс                  | все                    |
| 404      | `NOT_FOUND`               | Ресурс не найден                                  | все                    |
| 404      | `USER_NOT_FOUND`          | Пользователь не найден                            | Auth                   |
| 404      | `CLASSIFIER_NOT_FOUND`    | Узел классификатора не найден                     | Registry               |
| 404      | `TERM_NOT_FOUND`          | Термин не найден                                  | Registry               |
| 404      | `DOCUMENT_NOT_FOUND`      | Документ не найден (реестр НСИ или файловый)      | Registry, Orchestrator |
| 404      | `SESSION_NOT_FOUND`       | Сессия чата не найдена                                    | Query                  |
| 404      | `MESSAGE_NOT_FOUND`       | Сообщение чата не найдено                                 | Query                  |
| 404      | `FILE_NOT_FOUND`          | Файл не найден                                    | Integration            |
| 408      | `INDEX_TRIGGER_TIMEOUT`   | Таймаут триггера индексации                       | Orchestrator           |
| 408      | `DECISION_TIMEOUT`        | Таймаут ожидания решения по черновику             | Orchestrator           |
| 408      | `PREVIEW_TRIGGER_TIMEOUT` | Таймаут запуска preview-фазы                      | Orchestrator           |
| 408      | `LLM_GENERATION_TIMEOUT`  | Таймаут генерации LLM                             | Query                  |
| 409      | `HAS_CHILDREN`            | Нельзя удалить узел с дочерними                   | Registry               |
| 409      | `DUPLICATE_CODE`          | Код классификатора уже существует                 | Registry               |
| 409      | `DUPLICATE_TERM`          | Термин уже существует                             | Registry               |
| 409      | `DUPLICATE_DOCUMENT`      | Документ с таким бизнес-ключом уже существует     | Registry               |
| 409      | `DUPLICATE_EMAIL`         | Email уже используется                            | Auth                   |
| 409      | `HAS_DOCUMENTS`           | Есть документы, ссылающиеся на код классификатора | Registry               |
| 409      | `CROSS_SYSTEM_PARENT`     | Родитель в другой системе классификации           | Registry               |
| 410      | `TASK_EXPIRED`            | Результат задачи удалён (старше N дней)           | OCR                    |
| 400      | `EMPTY_FILE`              | Загружен пустой файл (0 байт)                     | Orchestrator           |
| 400      | `FILE_TOO_SMALL`          | Файл менее 1 КБ — нецелесообразный документ       | Orchestrator           |
| 400      | `EMPTY_MESSAGE`           | Пустое сообщение в чате                           | Query                  |
| 400      | `INVALID_DATE_RANGE`      | date_from позже date_to                           | Query, Orchestrator    |
| 400      | `INVALID_STATE_TRANSITION`| Недопустимый переход статуса                     | Orchestrator, Registry |
| 409      | `DUPLICATE_FILE`          | Файл с таким SHA-256 уже обрабатывается           | Orchestrator           |
| 409      | `ALREADY_PROCESSING`      | Документ уже в обработке (reprocess)              | Orchestrator           |
| 413      | `FILE_TOO_LARGE`          | Превышение лимита размера файла (>= 100 МБ)       | Integration, OCR       |
| 422      | `VALIDATION_FAILED`       | Ошибка семантической валидации (данные корректны по структуре, но противоречат бизнес-правилам) | Converter-validator   |
| 429      | `TOO_MANY_REQUESTS`       | Превышен лимит запросов (rate limit)              | все                    |
| 502      | `BAD_GATEWAY`             | Ошибка при вызове внутреннего сервиса              | Orchestrator           |
| 502      | `LLM_GENERATION_FAILED`   | Ошибка генерации LLM (все retry исчерпаны)        | Query                  |
| 503      | `SERVICE_UNAVAILABLE`     | Недоступен внешний сервис (MinIO, БД)             | все                    |
| 422      | `UNSUPPORTED_FILE_TYPE`   | Неподдерживаемый тип файла                        | Orchestrator           |
| 500      | `INTERNAL_ERROR`          | Внутренняя ошибка сервера                         | все                    |
| 500      | `BUILD_FAILED`            | Ошибка построения чанков/эмбеддингов              | RAG Builder            |
| 500      | `SEARCH_FAILED`           | Ошибка поиска чанков                              | RAG Search             |
| 500      | `INDEXING_FAILED`         | Ошибка индексации документа                       | RAG                    |
| 500      | `OCR_FAILED`              | Ошибка OCR-распознавания                          | OCR, Orchestrator      |
| 500      | `ANALYSIS_FAILED`         | Ошибка анализа/сопоставления                      | Analyse                |
| 500      | `CONVERSION_FAILED`       | Ошибка конвертации документа                     | Converter-validator    |
| 500      | `CONVERSION_VALIDATION_FAILED` | Ошибка семантической валидации конвертации (внутренняя, не 422)    | Converter-validator    |
| 503      | `CIRCUIT_BREAKER_OPEN`    | Этап временно отключён (Circuit Breaker)          | Orchestrator           |
| 501      | `NOT_IMPLEMENTED`         | Метод не реализован                               | все                    |
| 504      | `GATEWAY_TIMEOUT`         | Таймаут при вызове внутреннего сервиса            | Orchestrator           |

**D24 — дополнительные специфичные коды (сверка 12 API-файлов, 17.06):**

| HTTP | `error.code` | Описание | Сервис |
|------|--------------|----------|--------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не найден (проксируется через Gateway) | Registry, Gateway |
| 404 | `CATEGORY_NOT_FOUND` | Категория не найдена | Registry |
| 409 | `CATEGORY_HAS_DOCUMENTS` | Нельзя удалить категорию с привязанными документами | Registry |
| 409 | `DUPLICATE_CATEGORY_NAME` | Категория с таким именем уже существует | Registry |
| 409 | `DRAFT_ALREADY_DECIDED` | По черновику уже принято решение | Registry, Gateway |
| 409 | `DRAFT_ALREADY_PREVIEWED` | Preview уже выполнен | Registry |
| 422 | `EMPTY_DOCUMENT` | Документ пустой (0 страниц) | Registry, Gateway |
| 500 | `PARSER_FAILED` | Ошибка парсинга | Parser |
| 415 | `UNSUPPORTED_FORMAT` | Неподдерживаемый формат файла (отличается от `UNSUPPORTED_FILE_TYPE` 422) | Parser, OCR |
| 503 | `ENGINE_UNAVAILABLE` | OCR-движок недоступен | OCR |
| 500 | `STORAGE_ERROR` | Ошибка хранилища (MinIO) | Parser, OCR |
| 404 | `TASK_NOT_FOUND` | Задача не найдена | Parser, OCR |
| 422 | `INVALID_INPUT` | Некорректные входные данные | Converter-validator |
| 500 | `METADATA_EXTRACTION_FAILED` | Ошибка извлечения метаданных | Converter-validator |
| 504 | `LLM_TIMEOUT` | Таймаут LLM-запроса | Converter-validator |
| 504 | `REGISTRY_TIMEOUT` | Таймаут вызова Registry | Converter-validator |
| 400 | `EMPTY_QUERY` | Пустой поисковый запрос | RAG Search |
| 422 | `INVALID_PARAMETER` | Некорректный параметр | RAG Search |

> **Не подтверждено**: `PAGE_NOT_FOUND` — не существует ни в одном из 12 API-файлов. Источник не найден, удалено из плана.

---

### Матрица доступа (RBAC)

| Группа / Эндпоинт                                          | `engineer` | `knowledge_admin` | `system_admin` |
| ---------------------------------------------------------- | ---------- | ----------------- | -------------- |
| `GET /auth/me`, `POST /auth/token`, `/refresh`, `/revoke`  | ✓          | ✓                 | ✓              |
| `POST /drafts`                                              | ✓          | ✓                 | ✓              |
| `GET /documents` (+ `/{doc_id}`, `/status`, `/file`, `/pages`) | ✓          | ✓                 | ✓              |
| `DELETE /documents/{doc_id}`                                   | ✗          | ✓                 | ✓              |
| `POST /documents/{doc_id}/reprocess`                           | ✗          | ✓                 | ✓              |
| `GET /documents/{doc_id}/history` | ✓ | ✓ | ✓ |
| `GET /documents/{doc_id}/errors` | ✓ | ✓ | ✓ |
| `GET /documents/queue` | ✓ | ✓ | ✓ |
| `GET /documents/{doc_id}/versions` | ✓ | ✓ | ✓ |
| `POST /documents/{doc_id}/versions` | ✗ | ✓ | ✓ |
| `GET /documents/{doc_id}/parameters` | ✓ | ✓ | ✓ |

| `POST /chat/sessions`, `GET /chat/sessions` (+ `/{id}`)   | ✓          | ✓                 | ✓              |
| `PUT /chat/sessions/{id}`, `DELETE /chat/sessions/{id}`   | ✓          | ✓                 | ✓              |
| `POST /chat/sessions/{id}/messages`                        | ✓          | ✓                 | ✓              |
| `POST /chat/sessions/{id}/messages/search`                 | ✓          | ✓                 | ✓              |
| `POST /chat/sessions/{id}/context`                         | ✓          | ✓                 | ✓              |
| `POST /chat/sessions/{id}/export`                          | ✓          | ✓                 | ✓              |
| `POST /chat/feedback`                                      | ✓          | ✓                 | ✓              |
| `GET /chat/history` (+ `/export`)                          | ✓          | ✓                 | ✓              |
| `POST /text/search`                                        | ✓          | ✓                 | ✓              |

| `GET /drafts`                                                | ✓          | ✓                 | ✓              |
| `GET /drafts/{draft_id}`                                    | ✓          | ✓                 | ✓              |
| `GET /drafts/{draft_id}/preview`                            | ✓          | ✓                 | ✓              |
| `POST /drafts/{draft_id}/preview`                           | ✓          | ✓                 | ✓              |
| `GET /drafts/{draft_id}/preview/status`                     | ✓          | ✓                 | ✓              |
| `PATCH /drafts/{draft_id}/decide`                           | ✓          | ✓                 | ✓              |
| `DELETE /drafts/{draft_id}`                                 | ✗          | ✓                 | ✓              |
| `GET /tasks/{task_id}/status`                              | ✗          | ✗                 | ✓              |

| `POST /analyse/compare`, `GET /analyse/compare/{id}`       | ✓          | ✓                 | ✓              |
| `POST /analyse/calculate`                                  | ✓          | ✓                 | ✓              |
| `POST /analyse/recommend`                                  | ✓          | ✓                 | ✓              |

| `POST /meridian/export`                                    | ✗          | ✓                 | ✓              |
| `GET /admin/users`, `POST/PUT/PATCH/DELETE /admin/users` | ✗ | ✗ | ✓ |
| `GET /admin/roles`, `POST /admin/roles` | ✗ | ✗ | ✓ |
| `GET /admin/audit` | ✗ | ✗ | ✓ |
| `GET /monitor/metrics` | ✗ | ✓ | ✓ |
| `GET /tasks/{task_id}/status` | ✗ | ✗ | ✓ |
| `GET /tasks/{task_id}/steps` | ✗ | ✗ | ✓ |
| `GET /drafts/{draft_id}/tasks` | ✗ | ✓ | ✓ |
| `GET /registry/classifiers/*` | ✓ | ✓ | ✓ |
| `POST /PUT /PATCH /DELETE /registry/classifiers/*` | ✗ | ✓ | ✓ |
| `GET /registry/terminology/*` | ✓ | ✓ | ✓ |
| `POST /PUT /PATCH /DELETE /registry/terminology/*` | ✗ | ✓ | ✓ |
| `GET /registry/documents/*` | ✓ | ✓ | ✓ |
| `POST /registry/documents/search` | ✓ | ✓ | ✓ |
| `POST /PUT /PATCH /DELETE /registry/documents/*` (кроме search) | ✗ | ✓ | ✓ |
| `GET /registry/common/*` | ✓ | ✓ | ✓ |
| `GET /registry/categories/*` | ✓ | ✓ | ✓ |
| `POST /PUT /DELETE /registry/categories/*` | ✗ | ✓ | ✓ |

> **Примечания:**
> - Роли: `engineer` — инженер-конструктор; `knowledge_admin` — администратор НСИ; `system_admin` — системный администратор.
> - Матрица применяется ко всем эндпоинтам через Gateway. Внутренние сервисы вызываются через Gateway; RBAC проверяется на Gateway.
> - `GET /api/v1/system/health` доступен без аутентификации для использования инфраструктурными системами мониторинга.

---

### Rate Limiting (ограничение запросов)

> **⚠️ Статус реализации**: Лимиты, описанные ниже, вступают в силу после настройки Nginx (`limit_req`) в production. В текущей (мок) реализации rate limiting не применяется.
>
> **⏳ Требует реализации в коде**: настройка Nginx `limit_req` модуль. Ответ `429 Too Many Requests` в мок-режиме не возвращается.

Для защиты от перегрузок и DoS-атак на все эндпоинты через Gateway действуют следующие лимиты:

| Эндпоинт / Группа                     | Лимит                     | Блокировка          | Примечание                         |
| ------------------------------------- | ------------------------- | ------------------- | ---------------------------------- |
| `POST /auth/token`                    | 10 запросов / мин         | 5 мин               | Защита от брутфорса                |
| `POST /auth/refresh`                  | 20 запросов / мин         | 5 мин               |                                    |
| `POST /drafts`                        | 10 запросов / мин         | 1 мин               | Загрузка документов                |
| `GET /documents` (+ `/{id}`, `/status`, `/file`, `/pages`) | 100 запросов / мин | 1 мин |                                    |
| `POST /chat/sessions`, `POST /chat/sessions/{id}/messages`, `POST /chat/sessions/{id}/messages/search`      | 30 запросов / мин         | 1 мин               | Чат и текстовые запросы            |
| `POST /chat/sessions/{id}/context`, `POST /chat/sessions/{id}/export` | 30 запросов / мин | 1 мин |
| `POST /chat/feedback` | 30 запросов / мин | 1 мин |
| `POST /text/search` | 30 запросов / мин | 1 мин | Текстовый поиск |
| `GET /admin/*`                        | 60 запросов / мин         | 1 мин               | Административные                   |
| `POST /admin/*`                       | 20 запросов / мин         | 1 мин               |                                    |
| Остальные эндпоинты                   | 60 запросов / мин         | 1 мин               | По умолчанию                       |

При превышении лимита возвращается HTTP `429 Too Many Requests` с телом:

```json
{
  "error": {
    "code": "TOO_MANY_REQUESTS",
    "message": "Превышен лимит запросов. Попробуйте через N секунд",
    "details": {
      "retry_after_seconds": 60
    }
  }
}
```

Лимиты настраиваются через переменные окружения.

---

### Edge Cases (граничные случаи)

#### Пустой / нулевой документ
- При загрузке файла размером **0 байт** возвращается `400 BAD_REQUEST` с кодом `EMPTY_FILE`.
- При загрузке файла размером **менее 1 КБ** (нецелесообразный документ) — `400 BAD_REQUEST` с кодом `FILE_TOO_SMALL`.
- Если документ после распознавания содержит **0 страниц** (пустой PDF/изображение):
  - Черновик переводится в статус `discarded` с кодом ошибки `EMPTY_DOCUMENT`.
  - Такой черновик **не может быть завершён** — документ не будет создан в Registry. Решение `approve` недоступно.
  - Пользователь может отклонить черновик (`reject`) или удалить его.
- Лимит размера файла: строго **< 100 МБ**. При `>= 100 МБ` возвращается `413 FILE_TOO_LARGE`.

#### Пустое сообщение в чате
- `POST /chat/sessions/{id}/messages` с пустым `content` (пустая строка или только пробелы)
  возвращает `400 BAD_REQUEST` с кодом `EMPTY_MESSAGE`.
- `POST /chat/sessions`, `POST /chat/sessions/{id}/messages`, `POST /text/search` — аналогичная проверка.

#### Документы с максимальной длиной полей

| Поле | Максимальная длина | Действие при превышении |
|------|--------------------|-------------------------|
| `title` | 1024 символа | `400 VALIDATION_ERROR` |
| `doc_code` | 128 символов | `400 VALIDATION_ERROR` |
| `content` (сообщение чата) | 65536 символов | `400 VALIDATION_ERROR` |
| `comment` (любой) | 4096 символов | `400 VALIDATION_ERROR` |

#### Граничные значения дат
- `date_from` должен быть раньше `date_to`. Иначе — `400 BAD_REQUEST` с кодом `INVALID_DATE_RANGE`.
- **Максимальный диапазон дат**: 100 лет (настраивается через `MAX_DATE_RANGE_YEARS`, по умолчанию `100`). Ограничение защищает от нецелевого использования и избыточной нагрузки на БД.

#### Конкуренция (concurrent requests)
- **Конкурентная загрузка файла**: При одновременной загрузке файла с одинаковым SHA-256:
  - Первый завершивший транзакцию запрос проходит
  - Остальные получают `409 CONFLICT`
  - Механизм: уникальный индекс `UNIQUE (file_hash_sha256)` + `INSERT ... ON CONFLICT DO NOTHING`
  - Если файл уже обрабатывается (статус `uploaded`/`previewing`/`parsing`), новый запрос с тем же SHA-256 отклоняется
- Одновременный вызов `POST /documents/{doc_id}/reprocess` для одного документа — второй запрос
  получает `409 CONFLICT` с кодом `ALREADY_PROCESSING`.
- Idempotency-Key: при повторном запросе с тем же ключом в течение 1 часа возвращается
  сохранённый результат первого запроса.

#### Поведение при недоступности внешних сервисов

| Внешний сервис | Эндпоинт | Поведение | HTTP-код |
|---|---|---|---|
| MinIO | `POST /drafts`, `GET /documents/{id}/file` | Ошибка загрузки/получения файла | `503 SERVICE_UNAVAILABLE` |
| Redis | Все эндпоинты (кэш/очереди) | **Redis недоступен**: Idempotency-Key не проверяется (запросы проходят без защиты от дублей), кэш не работает. Rate limiting через Nginx не зависит от Redis. Инцидент логируется как WARN. В production Redis должен быть развёрнут в кластере (минимум 2 реплики). | — (WARN-лог) |
| LLM | `POST /chat/*`, `POST /text/*` | Retry 2 раза с усечением контекста; при всех неудачах — `502 BAD_GATEWAY` | `502 BAD_GATEWAY` |
| PostgreSQL | Все эндпоинты с доступом к БД | Connection pool исчерпан — `503 SERVICE_UNAVAILABLE` | `503 SERVICE_UNAVAILABLE` |
| Меридиан | `POST /meridian/export` | Экспорт ставится в очередь, повтор раз в 10 минут; статус `deferred` | `202` |

---

### Координаты блоков (bbox)

Система координат bbox различается на этапах обработки:

| Этап | Формат | Единицы | Порядок |
|---|---|---|---|
| OCR / Parser (сырой JSON) | `[x1, y1, x2, y2]` | пиксели (px) — нормирование выполняет Converter-validator | Левая верхняя (0,0), Y вниз |
| Converter-validator | `[x1, y1, x2, y2]` | нормализованные (0..1) | Левая верхняя (0,0), Y вниз |
| Registry (БД) | `[x1, y1, x2, y2]` | нормализованные (0..1) | Левая верхняя (0,0), Y вниз |
| Orchestrator (через Gateway) | `[x1, y1, x2, y2]` | нормализованные (0..1) | Левая верхняя (0,0), Y вниз |

> **Нормирование bbox:** OCR/Parser выдают bbox в пикселях (px) относительно размеров страницы (`page.width`, `page.height`). Converter-validator выполняет нормирование в диапазон [0,1]. Начиная с Converter-validator и далее (Registry, Orchestrator через Gateway) bbox передаётся в нормализованном виде (0..1).

---

### Примечания по реализации

**Категории контента (`document_type`)** строго фиксированы: `normative`, `technical`, `drawing`, `specification`, `archival_scan`. Именно эти значения ожидаются в полях `document_type`.

- **Обработка полным документом:** API не содержит методов для ручного выделения областей. Распознавание запускается для всего документа сразу после загрузки; пользователь не может отметить фрагмент для OCR. Просмотр страниц возможен только в режиме чтения.

- **Пороговые значения confidence:** система помечает страницы с низким качеством OCR и логирует их (UC-02, UC-09). Пороговые значения задаются через переменные окружения каждого сервиса:
  - `OCR_MIN_CONFIDENCE` — минимальный порог confidence для страницы (по умолчанию `0.5`).
  - `OCR_AVG_MIN_CONFIDENCE` — минимальный средний confidence по документу (по умолчанию `0.6`).

- **Трассируемость ответов:** все ответы поиска и вопросно-ответной системы обязательно содержат `document_id` и `page`. Прямая ссылка на страницу формируется согласно API просмотра (`/documents/{doc_id}/pages/{page_num}`).

- **Дисклеймер** о необходимости инженерной верификации присутствует в ответах `/validate/compare`.

- **Именование полей источников** (единый стандарт для всех сервисов):
  
  | Концепция            | Единое имя поля    |
  | -------------------- | ------------------ |
  | ID документа         | `document_id`      |
  | Номер страницы       | `page`             |
  | ID фрагмента         | `fragment_id`      |
  | URL превью страницы  | `page_preview_url` |
  | URL документа        | `document_url`     |
  | Оценка релевантности | `score`            |
  
  Допускаются синонимы в ответах внутренних сервисов, но API (через Gateway) **обязан** маппить поля к единым именам.

- **Лимиты загрузки:** максимальный размер файла — 100 МБ. Поддерживаемые MIME-типы: `application/pdf`, `image/png`, `image/jpeg`, `image/tiff`. При превышении лимита возвращается `413 PAYLOAD_TOO_LARGE`.

- **Идемпотентность:** опциональный заголовок `Idempotency-Key` поддерживается для `POST /drafts` (создание черновика). При повторном запросе с тем же ключом в течение 1 часа возвращается сохранённый результат.

---

### Безопасность и логирование

#### Защита чувствительных данных (PII)

Все сервисы обязаны соблюдать следующие правила при обработке чувствительных данных:

| Поле | Правило обработки |
|------|-------------------|
| `password` | Не логировать, не возвращать в ответах API, не передавать в промежуточные сервисы. Хранить только в хэшированном виде (bcrypt, cost factor ≥ 12). |
| `refresh_token` | Не логировать. Хранить в БД в хэшированном виде. |
| `access_token` | Не логировать. |

**CSRF защита**: JWT передаётся только через заголовок `Authorization: Bearer <token>`, не через cookie. Это обеспечивает защиту от CSRF-атак, так как браузер не подставляет custom header автоматически.

**XSS защита**: Все строковые поля, заполняемые пользователем (названия документов, сообщения чата, комментарии, feedback), должны экранироваться при отображении в UI. API возвращает `Content-Type: application/json` и `X-Content-Type-Options: nosniff`. Сервер не выполняет санитизацию контента — это ответственность UI.

**Чувствительные данные в URL** (P3-4, уточнение): **запрещено** передавать в query-string:
- `password`, `access_token`, `refresh_token`, любые `*_token`, `*_secret`, `*_key` (аутентификационные данные).
- `email`, `phone`, `passport`, `inn`, `snils`, `ogrn` (PII — персональные данные).
- Полные SQL-запросы, stack-trace, file paths, config values (уже запрещены в `details`, P3-4).

`user_id` (внутренний bigint) в query-параметрах допустим. URL с query-параметрами логируется полностью. При попытке передать запрещённые поля (из списка выше) возвращается `400 BAD_REQUEST` с кодом `PII_IN_QUERY_STRING`.

#### Логирование

- Поля `password`, `refresh_token`, `access_token` должны быть **отфильтрованы или замаскированы** (например, заменены на `***`) во всех логах сервисов.
- Запрещено логировать **тело запроса/ответа** эндпоинтов `/auth/*`, `/internal/auth/*`.
- **Должно быть использовано** структурное логирование с явным списком полей, исключённых из вывода (PII filter).
  Конфигурация PII filter задаётся через `LOG_PII_FIELDS` (список полей через запятую, по умолчанию:
  `password, access_token, refresh_token`).

### Структурированное логирование — стандарт полей (P11-1, 17.06.2026)

> **Обязательные поля** каждой записи лога (JSON):

| Поле | Тип | Описание |
|------|-----|----------|
| `timestamp` | string (ISO 8601) | Время события (`2026-06-18T14:30:00.123Z`) |
| `level` | string | Уровень: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `service` | string | Имя сервиса: `gateway`, `orchestrator`, `auth`, `query`, `registry`, `integration`, `converter-validator`, `parser`, `ocr`, `rag-builder`, `rag-search`, `analyse` |
| `trace_id` | string | OpenTelemetry trace_id (32 hex) |
| `span_id` | string | OpenTelemetry span_id (16 hex) |
| `request_id` | string (UUID) | Корреляционный ID, генерируется Gateway при отсутствии (P11-2) |
| `user_id` | bigint \| null | ID пользователя (если аутентифицирован) |
| `path` | string | HTTP-путь запроса (без query-string для PII, P3-4) |
| `method` | string | HTTP-метод: `GET`, `POST`, ... |
| `status` | int | HTTP-статус ответа |
| `latency_ms` | int | Длительность обработки в мс |
| `message` | string | Человекочитаемое сообщение |
| `error_code` | string \| null | Код ошибки (если применимо) |
| `error_message` | string \| null | Текст ошибки (без stack-trace) |
| `extra` | object | Дополнительные контекстные поля |

**Маскирование** — настраивается через `LOG_PII_FIELDS`, по умолчанию маскируются только пароли и секретные данные: `password, access_token, refresh_token`.

### Корреляционные идентификаторы (P11-2, 17.06.2026)

| Заголовок | Генерирует | Передаётся | Описание |
|-----------|------------|------------|----------|
| `X-Request-ID` | Gateway (если отсутствует) | Через все сервисы | UUIDv4, уникальный для каждого внешнего запроса. Кладётся в `request_id` каждой записи лога |
| `X-Trace-ID` | OpenTelemetry SDK | Все спаны | Соответствует `trace_id` в OTLP |
| `X-Draft-ID` | Orchestrator | Internal services | Текущий `draft_id` в обработке (если применимо) |
| `X-Document-ID` | Orchestrator/Registry | Internal services | Текущий `document_id` в обработке |
| `X-Version-ID` | Orchestrator | Internal services | Текущий `version_id` в обработке |
| `X-User-ID` | Gateway (после JWT-валидации) | Internal services | ID пользователя (для логирования без повторной валидации) |

**Правила:**
- Gateway **обязан** сгенерировать `X-Request-ID`, если он не пришёл от клиента.
- Все downstream-сервисы обязаны пробрасывать `X-Request-ID` и `X-Trace-ID` в каждый исходящий запрос.
- При ошибке `request_id` возвращается в теле ответа (`details.request_id`) для быстрого поиска в логах.

### Уровни логирования и правила эскалации (P11-3, 17.06.2026)

| Уровень | Когда использовать | Примеры |
|---------|-------------------|---------|
| `DEBUG` | Детальная отладочная информация (только в dev/staging) | SQL-запросы, содержимое переменных, trace вызовов |
| `INFO` | Нормальная работа системы | Успешный запрос (`status=200`), запуск задачи, смена статуса FSM |
| `WARNING` | Нештатные ситуации, не приводящие к сбою | PDF-security warning (P3-5), Lama fallback (P3-6), нештатные распарсенные блоки, `enrichment_skipped` (P1-15), rate limit близок к лимиту (80%) |
| `ERROR` | Ошибка, требующая вмешательства | Падение задачи, невозможность записать в БД/CAS, `LLM_GENERATION_FAILED`, `INDEXING_FAILED` |
| `CRITICAL` | Потеря консистентности или катастрофический сбой | Дубликат после approve (`DUPLICATE_FILE_AFTER_APPROVE`), потеря соединения с БД, потеря CAS-ссылки, повреждение индекса |

**Эскалация:**
- `WARNING` → событие попадает в SigNoz-дашборд `warnings` (P11-8).
- `ERROR` → SigNoz-алерт + уведомление в Slack/email.
- `CRITICAL` → SigNoz-алерт + PagerDuty (для on-call).

**Связь с аудитом (P11-4):** системные логи (этот раздел) **отдельно** от пользовательского аудита (`audit.events`). Системные логи — для отладки и мониторинга, аудит — для compliance и расследования инцидентов.

#### Планы развития

- **Краткосрочно:** вынести смену пароля пользователя в отдельный эндпоинт `POST /admin/users/{user_id}/reset-password` с обязательной аудит-записью.
- **Среднесрочно:** переход с Password Grant (`POST /auth/token` с `username` + `password`) на **Authorization Code + PKCE** — пароль перестаёт передаваться API, аутентификация выполняется на стороне клиента с одноразовым code.

---


## Обзор конвейера обработки документов

### Пайплайн 1: Формирование документа (двухфазный)

```
uploaded → previewing → ready_for_approve → approved → created
```

1. **Загрузка**: пользователь загружает файл через `POST /drafts` → статус черновика `uploaded`.
2. **Preview**: запуск предварительной обработки (OCR/Parser preview) → статус `previewing`.
3. **Решение**: после preview черновик переходит в `ready_for_approve`. Если документ уникален и не требует ручного вмешательства — автозавершение. Иначе — решение пользователя через `PATCH /drafts/{draft_id}/decide`.
4. **Завершение**: при `approve` выполняется Converter-validator. Если на preview был частичный JSON — перед этим запускается полный OCR/Parser (`mode=full`). Если preview уже вернул полный JSON (`preview_not_supported: true`) — OCR/Parser пропускается. Результат записывается в Registry (статус документа `created`).
5. **Отклонение**: при `reject` или ошибке черновик переводится в `discarded`.

### Пайплайн 2: Индексация документа

```
created → pending_index → indexing → indexed / failed
```

Документ со статусом `created` передаётся в RAG Builder для чанкования и построения векторного индекса.

### Пайплайн 3: Поиск документа

1. **Приём сообщения** (пишет БД) — сохранение запроса в истории чата, возврат `message_id`
2. **Обогащение терминами** (читает БД) — нормализация запроса через словарь терминов Registry
3. **RAG Search** (читает БД) — гибридный поиск релевантных чанков
3b. **Генерация ответа LLM** (нет доступа) — синтез ответа на основе чанков
4. **Обогащение цитирований** (нет доступа) — замена ссылок на machine-readable идентификаторы

Детальное описание этапов, FSM, матрица ответственности и архитектурные решения — в [overview.md](../pipelines/overview.md).

---

## Стек технологий

| Компонент              | Технология                    |
| ---------------------- | ----------------------------- |
| **Язык**               | Python 3.13                   |
| **API-фреймворк**      | FastAPI                       |
| **Очереди задач**      | Celery + Redis (broker)       |
| **База данных**        | PostgreSQL + pgvector         |
| **Файловое хранилище** | MinIO (CAS-пути)              |
| **AI / NLP**           | Внутренние компоненты         |
| **OCR-движки**         | Внутренние компоненты         |
| **Аутентификация**     | JWT (access + refresh tokens) |
| **Контейнеризация**    | Docker, Docker Compose        |