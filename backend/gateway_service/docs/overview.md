## Пайплайны обработки документов (v3.0)

Оркестратор координирует сквозную обработку документов через **два пайплайна** (Формирование и Индексация). Пайплайн 3 (Поиск) работает **независимо**.

**Контроль доступа:** все внешние запросы от UI проходят через **Nginx** (:443), который проксирует их на внутренний **Gateway Service** (:8080). Gateway проверяет JWT-токен и права доступа (RBAC) перед тем, как запрос попадёт к внутренним сервисам. Без валидного токена — `401`, без прав на операцию — `403`.

```mermaid
graph LR
    subgraph "Внешняя сеть"
        Nginx[Nginx<br/>:443 / HTTPS]
        UI[UI]
    end

    subgraph "Внутренняя сеть"
        GW[Gateway Service<br/>:8080 / JWT / RBAC]
    end

    subgraph "Оркестратор (Пайплайны 1 и 2)"
        direction TB
        P1[Пайплайн 1: Формирование документа] --> P2[Пайплайн 2: Индексация документа]
    end

    subgraph "Пайплайн 1: Формирование"
        A[MinIO] -->|file_ref| B[OCR Service]
        B -->|JSON| C[Parser Service]
        C -->|JSON| D[Converter-validator]
        D -->|JSON| E[Registry]
        E -->|JSON со ссылками| F[(PostgreSQL)]

        A -.->|preview ref| PB[OCR/Parser preview]
        PB -.->|preview JSON| PC[Converter-validator preview]
        PC -.->|preview result| UI{UI Decision}
        UI -.->|approve| D
    end

    subgraph "Пайплайн 2: Индексация"
        E -->|обогащённый JSON| G[RAG Builder]
        G --> H[(pgvector)]
    end

    subgraph "Пайплайн 3: Поиск"
        J[Query Service]
        K[RAG Search]
        J -->|query| K
        K -->|чанки| J
    end

    %% Все запросы — через Nginx → Gateway
    UI -->|1. HTTPS| Nginx
    Nginx -->|2. proxy :8080| GW
    GW -->|3. JWT / RBAC| J
    GW -->|3. JWT / RBAC| D
    GW -->|3. JWT / RBAC| E
    J -->|answer| GW
    GW -->|4. Ответ| Nginx
    Nginx -->|5. HTTPS| UI

    style Nginx fill:#555,color:#fff
    style GW fill:#e74c3c,color:#fff
    style B fill:#e6f3ff
    style C fill:#e6f3ff
    style D fill:#fff3e6
    style E fill:#e6ffe6
    style G fill:#ffe6f3
    style J fill:#fffacd
    style K fill:#f3e6ff
    style PB fill:#e6f3ff,stroke-dasharray: 5 5
    style PC fill:#fff3e6,stroke-dasharray: 5 5
    style UI fill:#fff,stroke:#333
```

**Роль Оркестратора:** управляет последовательностью вызовов **Пайплайнов 1 и 2**, передаёт JSON-контейнеры между этапами как **непрозрачные артефакты** (структура JSON известна только сервисам). Помимо координации, Оркестратор:

- Выполняет пре-стейдж загрузки: сохраняет файл в MinIO, вычисляет SHA-256, создаёт запись в БД
- Ведёт историю обработки документа (`GET /documents/{doc_id}/history`)
- Управляет статусной моделью FSM для каждого пайплайна независимо

**Роль Gateway:** внутренний сервис, принимает запросы от Nginx, проверяет JWT-токен (аутентификация) и права доступа (авторизация) на основе роли пользователя и матрицы RBAC. После успешной проверки перенаправляет запрос к соответствующему внутреннему сервису.

**Роль Nginx:** внешний веб-сервер, принимает HTTPS-запросы от UI и проксирует их на внутренний Gateway (`:8080`). Единственная точка входа из внешней сети. Подробнее — [gateway_service_api.md](gateway_service_api.md).

Детальное описание пайплайнов:

- [Пайплайн 1: Формирование документа](pipeline1-formation.md)
- [Пайплайн 1: Детальное описание preview-фазы](pipeline1-formation_detail.md)
- [Пайплайн 2: Индексация документа](pipeline2-indexation.md)
- [Пайплайн 3: Поиск документа](pipeline3-search.md)

---

### 3. Сводная таблица доступа к БД

| Пайплайн     | Этап                      | Доступ к БД                   | Направление данных                                                 |
| ------------ | ------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| Формирование | 1. OCR / Parser (альтернативно) | **Нет** (изоляция)        | Вход: ссылка MinIO → Выход: JSON                                   |
| Формирование | 2. Converter-validator    | **Читает**                    | Вход: JSON → Выход: JSON с решением                                |
| Формирование | 3. Registry               | **Пишет**                     | Вход: JSON → Выход: JSON со ссылками                               |
| Формирование | Preview OCR/Parser        | **Нет** (изоляция)            | Вход: preview ref MinIO → Выход: preview JSON                      |
| Формирование | Preview Converter-validator | **Читает** (Registry)       | Вход: preview JSON → Выход: preview результат                      |
| Индексация   | 1. RAG Builder            | **Пишет**                     | Вход: обогащённый JSON → Выход: статус                             |
| Поиск        | 1. Приём сообщения        | **Пишет** (история чата)      | Вход: content → Выход: 202 + message_id                            |
| Поиск        | 2. Обогащение терминами   | **Читает** (словарь терминов) | Вход: текст → Выход: обогащённый запрос                            |
| Поиск        | 3. RAG Search             | **Читает**                    | Вход: query + filters → Выход: массив чанков                       |
| Поиск        | 3b. Генерация ответа LLM  | **Нет**                       | Вход: чанки → Выход: текст ответа                                  |
| Поиск        | 4. Обогащение цитирований | **Нет**                       | Вход: текст LLM + чанки → Выход: answer с аннотированными сносками |

---

### 4. Статусная модель (FSM)

Детальные FSM-диаграммы и описание состояний — в соответствующих документах:

- **Пайплайн 1 (Формирование):** `uploaded → previewing → awaiting_decision → parsing → validation → ready_for_promotion / review_required → approved → registry` — [FSM и таблица состояний](pipeline1-formation.md#статусная-модель-fsm)
- **Пайплайн 2 (Индексация):** `pending_index → indexing → indexed` — [FSM и таблица состояний](pipeline2-indexation.md#статусная-модель-fsm)
- **Пайплайн 3 (Поиск):** `idle → pending → enriching → searching → generating → enriching_citations → answered` — [FSM и таблица состояний](pipeline3-search.md#статусная-модель-fsm)

---

### 5. Матрица ответственности сервисов

| Операция                                       | Пайплайн | Этап              | Сервис                    | Доступ к БД  | Контроль доступа |
| ---------------------------------------------- | -------- | ----------------- | ------------------------- | ------------ | ---------------- |
| **Аутентификация** (проверка JWT)              | Все      | Вход              | **Gateway**               | Нет          | Все запросы      |
| **Авторизация** (проверка прав RBAC)           | Все      | Вход              | **Gateway**               | Нет          | Все запросы      |
| Загрузка файла, SHA-256, MinIO                 | 1        | Пре-стейдж        | **Orchestrator**          | Пишет        | `can_upload_documents` |
| Preview-фаза, хранение preview-данных          | 1        | Preview           | **Orchestrator**          | Пишет        | Аутентификация   |
| Распознавание (OCR)                            | 1        | 1. OCR            | **OCR Service**           | Нет          | Внутренний вызов |
| Парсинг структуры                              | 1        | 2. Parser         | **Parser Service**        | Нет          | Внутренний вызов |
| Валидация JSON, классификация                  | 1        | 3. Converter-validator | **Converter-validator Service** | Читает | Внутренний вызов |
| Проверка кодов по справочнику                  | 1        | 3. Converter-validator | **Registry Service**      | Читает       | Внутренний вызов |
| Запись карточки документа в БД                 | 1        | 4. Registry       | **Registry Service**      | Пишет        | `can_manage_registry` |
| Чанкинг + Embeddings + Индекс                  | 2        | 1. RAG Builder    | **RAG Builder Service**   | Пишет        | Внутренний вызов |
| Приём сообщения                                | 3        | 1. Query Service  | **Query Service**         | Пишет        | Аутентификация   |
| Обогащение терминами                           | 3        | 2. Query Service  | **Query Service**         | Читает       | Внутренний вызов |
| RAG поиск чанков                               | 3        | 3. RAG Search     | **RAG Search Service**    | Читает       | Внутренний вызов |
| Генерация ответа LLM                           | 3        | 3b. Query Service | **Query Service**         | Нет          | Внутренний вызов |
| Обогащение цитирований                         | 3        | 4. Query Service  | **Query Service**         | Нет          | Внутренний вызов |
| Управление файлами, экспорт во внешние системы | —        | Вспомогательный   | **Integration Service**   | Читает/Пишет | Аутентификация   |
| Сопоставление норм и проектов, расчёты         | —        | Вспомогательный   | **Analyse Service**       | Читает       | Аутентификация   |

> **Контроль доступа:**
> - **«Все запросы»** — Gateway проверяет JWT и RBAC на каждый внешний запрос. Без токена — `401`, без прав — `403`.
> - **«Аутентификация»** — требуется только валидный JWT-токен (любая аутентифицированная роль).
> - **«Внутренний вызов»** — сервис вызывается Orchestrator'ом в рамках пайплайна, внешний доступ отсутствует.
> - Конкретные permissions (`can_upload_documents`, `can_manage_registry` и др.) проверяются Gateway на соответствующих эндпоинтах.

---

### 6. Эндпоинты внутренних сервисов

Детальное описание API каждого сервиса — в соответствующих документах:

| Сервис                  | Документация                                                          | Базовый URL (внутренний) |
| ----------------------- | --------------------------------------------------------------------- | ------------------------ |
| **Nginx** (внешний)     | —                                                                     | `https://{host}:443`     |
| **Gateway** (внутренний) | [gateway_service_api.md](gateway_service_api.md)                      | `http://127.0.0.1:8080`  |
| Orchestrator            | [orchestrator_service_api.md](../api/orchestrator_service_api.md)     | `http://127.0.0.1:8081`  |
| Auth                    | [auth_service_api.md](../api/auth_service_api.md)                     | `http://127.0.0.1:8082`  |
| Query Service           | [query_service_api.md](../api/query_service_api.md)                   | `http://127.0.0.1:8083`  |
| Registry                | [registry_service_api.md](../api/registry_service_api.md)             | `http://127.0.0.1:8084`  |
| Integration             | [integration_service_api.md](../api/integration_service_api.md)       | `http://127.0.0.1:8085`  |
| Converter-validator     | [converter_validator_service_api.md](../api/converter_validator_service_api.md) | `http://127.0.0.1:8086`  |
| Parser                  | [parser_service_api.md](../api/parser_service_api.md)                 | `http://127.0.0.1:8087`  |
| OCR                     | [ocr_service_api.md](../api/ocr_service_api.md)                       | `http://127.0.0.1:8088`  |
| Analyse                 | [analyse_service_api.md](../api/analyse_service_api.md)               | `http://127.0.0.1:8089`  |
| RAG Builder             | [rag_builder_service_api.md](../api/rag_builder_service_api.md)       | `http://127.0.0.1:8090`  |
| RAG Search              | [rag_search_service_api.md](../api/rag_search_service_api.md)         | `http://127.0.0.1:8091`  |

---

### 7. Поток данных (Data Flow)

Все внешние запросы от UI проходят через **Nginx** (внешний веб-сервер, :443), который проксирует их на внутренний **Gateway Service** (:8080). Gateway выполняет аутентификацию (JWT) и авторизацию (RBAC). Только после успешной проверки запрос направляется к соответствующему внутреннему сервису.

```mermaid
flowchart LR
    subgraph "Внешняя сеть"
        UI[User Interface]
        Nginx[Nginx<br/>:443 / HTTPS]
    end

    subgraph "Внутренняя сеть"
        GW[Gateway<br/>:8080 / JWT / RBAC]
    end

    subgraph "Пайплайн 1: Формирование документа"
        MinIO[(MinIO)] -->|"file_ref"| Type{Тип файла}
        Type -->|"скан/изображение"| OCR[OCR Service]
        Type -->|"цифровой PDF/DOC"| Pars[Parser Service]
        OCR -->|"JSON"| CV[Converter-validator]
        Pars -->|"JSON"| CV
        CV -->|"JSON (opaque)"| Reg[Registry]
        Reg -->|"JSON со ссылками"| DB[(PostgreSQL Registry)]

        MinIO -.->|"preview ref"| Preview{Preview}
        Preview -.->|"скан"| P_OCR[OCR preview]
        Preview -.->|"цифровой"| P_Pars[Parser preview]
        P_OCR -.->|"preview JSON"| P_CV[Converter-validator preview]
        P_Pars -.->|"preview JSON"| P_CV
        P_CV -.->|"preview result"| UID{UI Decision}
        UID -.->|"approve"| CV
    end

    subgraph "Пайплайн 2: Индексация документа"
        Reg -->|"Обогащённый JSON"| RAGi[RAG Builder]
        RAGi -->|"status"| DB
        RAGi --> Vec[(Векторный индекс pgvector)]
    end

    subgraph "Пайплайн 3: Поиск документа"
        QS[Query Service]
        RAGs[RAG Search]
        QS -->|"query + filters"| RAGs
        Vec --> RAGs
        RAGs -->|"чанки"| QS
    end

    %% Все запросы — через Nginx → Gateway
    UI -->|"1. HTTPS"| Nginx
    Nginx -->|"2. proxy :8080"| GW
    GW -->|"3. JWT проверен, RBAC ок"| QS
    GW -->|"3. JWT проверен, RBAC ок"| Reg
    GW -->|"3. JWT проверен, RBAC ок"| CV
    QS -->|"4. answer + сноски"| GW
    GW -->|"5. Ответ"| Nginx
    Nginx -->|"6. HTTPS"| UI

    style Nginx fill:#555,color:#fff,stroke:#333
    style GW fill:#e74c3c,color:#fff,stroke:#333
    style OCR fill:#e6f3ff,stroke:#333
    style Pars fill:#e6f3ff,stroke:#333
    style CV fill:#fff3e6,stroke:#333
    style Reg fill:#e6ffe6,stroke:#333
    style RAGi fill:#ffe6f3,stroke:#333
    style RAGs fill:#f3e6ff,stroke:#333
    style QS fill:#fffacd,stroke:#333
    style P_OCR fill:#e6f3ff,stroke:#333,stroke-dasharray: 5 5
    style P_Pars fill:#e6f3ff,stroke:#333,stroke-dasharray: 5 5
    style P_CV fill:#fff3e6,stroke:#333,stroke-dasharray: 5 5
    style UID fill:#fff,stroke:#333
    style Preview fill:#fff,stroke:#333

```

**Форматы передачи между этапами:**

| Между                                | Формат                                         | Протокол      | Примечание                                      |
| ------------------------------------ | ---------------------------------------------- | ------------- | ----------------------------------------------- |
| Orchestrator → OCR Service           | `file_ref` (ссылка MinIO)                      | JSON via HTTP | Выбор сервиса по типу файла (см. прим.)         |
| OCR Service → Orchestrator           | **JSON-контейнер** (распознанный текст)        | JSON via HTTP | Непрозрачен для Orchestrator                    |
| Orchestrator → Parser Service        | `file_ref` (ссылка MinIO)                      | JSON via HTTP | Выбор сервиса по типу файла (см. прим.)         |
| Parser Service → Orchestrator        | **JSON-контейнер** (структура документа)       | JSON via HTTP | Непрозрачен для Orchestrator                    |
| Orchestrator → Converter-validator   | **JSON-контейнер** (от OCR _или_ Parser)       | JSON via HTTP | Непрозрачен для Orchestrator                    |
| Converter-validator → Orchestrator   | **JSON с решением** (auto / review)            | JSON via HTTP | Непрозрачен для Orchestrator                    |
| Orchestrator → Registry              | **JSON с решением** (от Converter-validator)   | JSON via HTTP | Непрозрачен для Orchestrator                    |
| Registry → Orchestrator              | **Обогащённый JSON (структура + ссылки в БД)** | JSON via HTTP | —                                               |
| Orchestrator → RAG Builder          | **Обогащённый JSON от Registry**               | JSON via HTTP | —                                               |
| RAG Builder → Orchestrator          | Статус завершения                              | JSON via HTTP | —                                               |
| Orchestrator → OCR/Parser preview    | `preview ref` (ссылка MinIO)                   | JSON via HTTP | Preview-фаза                                    |
| OCR/Parser preview → Orchestrator    | **preview JSON**                               | JSON via HTTP | Непрозрачен для Orchestrator                    |
| Orchestrator → Converter-validator preview | **preview JSON**                         | JSON via HTTP | Preview-фаза                                    |
| Converter-validator preview → Orchestrator | **preview результат**                    | JSON via HTTP | Содержит решение для UI                         |
| UI → Orchestrator (decision)         | **approve / reject**                           | JSON via HTTP | User decision point                             |
| UI → Query Service                   | Вопрос / поисковый запрос                      | JSON via HTTP | —                                               |
| Query Service → RAG Search           | **query + filters**                            | JSON via HTTP | Поиск чанков (без генерации)                    |
| RAG Search → Query Service           | **Массив чанков с полным содержимым**          | JSON via HTTP | Query Service формирует контекст и вызывает LLM |
| Query Service → UI                   | **answer + аннотированные сноски**             | JSON via HTTP | Обогащение цитирований идентификаторами         |

> **Важно:** OCR Service и Parser Service — **альтернативные**, не последовательные.
> Orchestrator выбирает сервис на основе MIME-типа / `source_type` файла:
> - `image/*`, `application/pdf` (сканированный) → **OCR Service**
> - `application/pdf` (цифровой), `application/msword`, `application/vnd.openxmlformats-officedocument.*` → **Parser Service**
> - Неподдерживаемый тип → ответ `422` с кодом `UNSUPPORTED_FILE_TYPE`
>
> JSON-контейнеры обоих сервисов имеют единый формат (`raw_ocr_v4`),
> поэтому Converter-validator не зависит от того, какой сервис выполнил первичную обработку.

#### Асинхронное ожидание (Longpoll)

Все внутренние вызовы между сервисами, помеченные как асинхронные (`202`), используют **longpoll-механизм** для ожидания результата:

1. Orchestrator отправляет запрос на запуск операции → получает `202 {task_id}`
2. Orchestrator вызывает `GET .../{task_id}/status?longpoll=15`
3. Сервис держит соединение до 15 секунд:
   - **Операция завершилась** → немедленный ответ с результатом
   - **Статус изменился** → ответ с текущим прогрессом
   - **Таймаут 15c** → ответ с текущим прогрессом
4. При нефинальном статусе — повторный longpoll

Это справедливо для всех этапов: OCR, Parser, Converter-validator, Registry (проверка уникальности), RAG Builder, Analyse.

Подробнее — [Модель выполнения](../api/common_api.md#модель-выполнения-sync--async).

---

### 8. Ключевые архитектурные решения

| Решение                                        | Обоснование                                                                                                                                                                                                                                                                                                                                               |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Два независимых пайплайна + поиск**          | Оркестратор координирует формирование документа (бизнес-логика) и индексацию для поиска (RAG). Пайплайн 3 (Поиск/генерация ответа) работает независимо — пользователь обращается напрямую к Query Service. Каждый пайплайн имеет изоляцию по доступу к БД и свою FSM. Позволяет индексировать повторно без повторного распознавания                       |
| **Чанкинг в RAG Builder, а не в Parsing**     | Parsing отвечает только за распознавание и структурирование. Чанкинг — задача RAG для оптимизации поиска. Разные стратегии чанкинга не влияют на карточку документа                                                                                                                                                                                       |
| **Изоляция доступа к БД по этапам**            | Parsing не зависит от БД — может масштабироваться горизонтально. Validation читает, Registry пишет — исключены гонки и каскадные锁. RAG Builder пишет, RAG Search читает — консистентность данных                                                                                                                                                         |
| **Оркестратор оперирует JSON как контейнером** | Структура JSON известна только сервисам. Orchestrator не имеет доступа к БД (кроме пре-стейджа загрузки). Снижает связанность, упрощает тестирование и замену сервисов                                                                                                                                                                                    |
| **CAS-пути для файлов**                        | `{doc_id}/v{n}/{hash}.{ext}` — гарантирует целостность и исключает дубликаты                                                                                                                                                                                                                                                                              |
| **Бизнес-ключ `title_hash_sha256`**            | Учитывает `era`, `source_type`, коды классификации — исключает коллизии (ГОСТ СССР vs ГОСТ РФ с одинаковым номером)                                                                                                                                                                                                                                       |
| **Единый `document_id`**                       | `document_id` назначается на этапе Validation (Пайплайн 1, Этап 2) после проверки уникальности: для дубликатов — извлекается существующий, для новых документов — генерируется. Этот же `document_id` используется как первичный ключ во всех последующих сервисах — Registry и RAG. Registry не создаёт свой numeric ID, а пишет `document_id` как есть. Это исключает маппинг идентификаторов на стыке пайплайнов и упрощает трассировку документа от загрузки до поиска. |
| **Gateway — единая точка авторизации**         | Все внешние запросы приходят через Nginx (:443) на внутренний Gateway (:8080), который проверяет JWT-токен и права доступа (RBAC) до того, как запрос попадёт во внутренний сервис. Это позволяет отсечь неавторизованные запросы на границе системы, не нагружая внутренние сервисы. Разные эндпоинты требуют разных permissions (`can_upload_documents`, `can_manage_classifiers`, `can_manage_terminology`, `can_manage_registry`), что даёт гибкое управление доступом. Анонимный доступ — только к `/auth/*` и `/system/health`. |
| **RBAC-матрица на Gateway**                    | Gateway централизованно проверяет права доступа по матрице RBAC. Внутренние сервисы могут не реализовывать свою проверку прав (доверяют Gateway), что упрощает их логику. Однако для критичных операций внутренние сервисы могут выполнять дополнительную проверку. |
| **Двухфазный пайплайн с user decision point** | Пайплайн 1 разделён на две фазы: preview (быстрый проход OCR/Parser → Converter-validator) и commit (основной проход). После preview пользователь принимает решение — утвердить или отклонить результат. Это позволяет отсеивать ошибочные документы до записи в Registry и индексации. |
| **Preview-данные в журнале Оркестратора**     | Результаты preview-фазы сохраняются в журнале Оркестратора (`/documents/{doc_id}/history`). При утверждении preview-данные используются как основа для основного прохода, что исключает повторное распознавание. |
| **OCR и Parser — независимые сервисы с единым контрактом** | Разделение OCR (распознавание изображения/PDF в текст) и Parser (структурирование текста в JSON) позволяет заменять OCR-движок без влияния на парсинг. Единый JSON-контракт между сервисами обеспечивает слабую связанность. |
| **Таймауты для «зависших» состояний (Scheduler)** | Для состояний `awaiting_decision` и `review_required` установлены таймауты (24ч и 48ч), по истечении которых документ переводится в `failed`. Scheduler проверяет зависшие документы каждые 5 минут. |
| **Проверка уникальности через `POST /registry/documents/check-uniqueness`** | Выделенный эндпоинт Registry для быстрой проверки уникальности по метаданным, вызываемый **Оркестратором** на preview- и full-этапах перед записью документа. Позволяет отделить логику поиска дубликатов от логики создания документа и обеспечивает единый механизм duplicate-детекции. |
| **Rate Limiting для всех публичных эндпоинтов** | Единая политика ограничения запросов с разными лимитами для разных групп эндпоинтов. Redis для распределённого rate limiting. Код ошибки `429 TOO_MANY_REQUESTS`. |

---

### 9. End-to-end (сквозной поток)

Детальные sequence-диаграммы для каждого пайплайна — в соответствующих документах:

- **Пайплайн 1 (Формирование):** загрузка файла → preview (OCR/Parser → Converter-validator) → решение UI → OCR → Parser → Converter-validator → Registry — [sequence-диаграмма](pipeline1-formation.md)
- **Пайплайн 2 (Индексация):** запуск RAG Builder → чанкинг → embeddings → векторный индекс — [sequence-диаграмма](pipeline2-indexation.md)
- **Пайплайн 3 (Поиск):** сообщение → обогащение → RAG Search → LLM → цитирование — [sequence-диаграмма](pipeline3-search.md)

**Ключевые наблюдения:**

- **Nginx** принимает все внешние запросы и проксирует их на **Gateway**, который проверяет JWT и RBAC — ни один запрос от UI не попадает к внутренним сервисам без аутентификации и авторизации
- Оркестратор координирует только Пайплайны 1 и 2
- Пайплайн 1 включает двухфазный процесс: preview (OCR/Parser → Converter-validator → UI decision) и commit (OCR → Parser → Converter-validator → Registry)
- Пайплайн 3 работает независимо, но также проходит через Gateway
- Все асинхронные вызовы используют longpoll-механизм (таймаут 15с)
- Единый `document_id` проходит через Пайплайны 1 и 2 без трансформации
- JSON-контейнер передаётся между этапами Пайплайнов 1 и 2 как непрозрачный артефакт

---

### 10. Сводная статусная модель жизненного цикла документа

Объединённая FSM, показывающая полный жизненный цикл документа от загрузки до готовности к поиску.

```mermaid
stateDiagram-v2
    state "Пайплайн 1: Формирование" as P1 {
        [*] --> uploaded : POST /documents
        uploaded --> previewing : запуск preview
        previewing --> awaiting_decision : preview завершён
        previewing --> failed : ошибка распознавания
        awaiting_decision --> parsing : решение = proceed
        awaiting_decision --> duplicate : решение = stop_duplicate
        awaiting_decision --> new_version : решение = force_new_version
        awaiting_decision --> failed : таймаут 24ч
        parsing --> validation : OCR/Parser завершён
        parsing --> failed : таймаут 15 мин
        validation --> ready_for_promotion : авто-валидация
        validation --> review_required : требуется подтверждение
        validation --> failed : таймаут 30 мин
        review_required --> approved : approve оператора
        review_required --> validation : повторная валидация
        review_required --> failed : отклонено оператором
        review_required --> archived : таймаут 48ч
        ready_for_promotion --> registry : промотирование
        ready_for_promotion --> failed : таймаут 24ч
        approved --> registry : промотирование
        registry --> pending_index : запуск индексации
        registry --> failed : ошибка записи
        registry --> archived
    }

    state "Пайплайн 2: Индексация" as P2 {
        pending_index --> indexing : чанкинг + embeddings
        indexing --> indexed : индексация завершена
        indexing --> failed : ошибка индексации
    }

    state "Пайплайн 3: Поиск (сообщение)" as P3 {
        [*] --> idle
        idle --> pending : новое сообщение
        pending --> enriching : обогащение терминами
        enriching --> searching : поиск чанков
        searching --> generating : генерация LLM
        generating --> answered : цитирование
        pending --> failed
        enriching --> failed
        searching --> failed
        generating --> failed
    }

    %% Terminal
    indexed --> [*] : готов к поиску
    answered --> [*] : ответ отправлен

    %% Дополнительно
    indexed --> pending_index : реиндексация
    failed --> uploaded : reprocess
```

**Карта соответствия состояний:**

| Состояние             | Пайплайн | Описание                                                 |
| --------------------- | -------- | -------------------------------------------------------- |
| `uploaded`            | 1        | Файл загружен в MinIO, ожидание preview                  |
| `previewing`          | 1        | Выполняется preview OCR/Parser и Converter-validator     |
| `awaiting_decision`   | 1        | Preview завершён, ожидание решения пользователя          |
| `parsing`             | 1        | Выполняется OCR и распознавание структуры                |
| `validation`          | 1        | Валидация структуры, классификация, уникальность         |
| `review_required`     | 1        | Ожидание ручного подтверждения оператором                |
| `ready_for_promotion` | 1        | Автоматическое подтверждение, ожидание записи в Registry |
| `approved`            | 1        | Оператор подтвердил, ожидание записи в Registry          |
| `registry`            | 1        | Документ записан в реестр (registry.documents)                |
| `pending_index`       | 2        | Ожидание начала индексации                               |
| `indexing`            | 2        | Выполняется чанкинг и построение векторного индекса      |
| `indexed`             | 2        | Документ проиндексирован, готов к поиску                 |
| `duplicate`           | 1        | Документ-дубликат, обработка завершена                  |
| `new_version`         | 1        | Создана новая версия существующего документа             |
| `failed`              | 1/2/3    | Ошибка на одном из этапов                                |
| `archived`            | 1        | Документ архивирован (неактивен)                         |

---

### 11. Обработка ошибок и компенсационные потоки (Saga)

Каждый пайплайн реализует паттерн Saga для обеспечения консистентности данных при сбоях. Детальные таблицы компенсаций и диаграммы — в соответствующих документах:

- **Пайплайн 1 (Формирование):** компенсации для этапов загрузки, Parsing, Validation, Registry — [подробнее](pipeline1-formation.md#обработка-ошибок-и-компенсационные-потоки)
- **Пайплайн 2 (Индексация):** компенсации для этапов JSON Parsing, Chunking, Embeddings, Vector Index — [подробнее](pipeline2-indexation.md#обработка-ошибок-и-компенсационные-потоки)
- **Пайплайн 3 (Поиск):** компенсации для этапов приёма сообщения, обогащения, RAG Search, LLM, цитирования — [подробнее](pipeline3-search.md#обработка-ошибок-и-компенсационные-потоки)

---

### 12. Топология развёртывания (Deployment Topology)

```mermaid
graph TB
    subgraph "Внешняя сеть"
        Nginx[Nginx<br/>:443 / HTTPS]
        UI[Web UI]
    end

    subgraph "Сеть приложений"
        subgraph "API Gateway"
            GW[Gateway Service<br/>JWT, RBAC, Routing<br/>:8080]
        end

        subgraph "Оркестратор"
            Orch[Orchestrator Service<br/>:8081]
        end

        subgraph "Пайплайн 1: Формирование"
            OCR[OCR-сервис<br/>:8088]
            Pars[Parser-сервис<br/>:8087]
            CV[Converter-validator<br/>:8086]
            Reg[Registry<br/>:8084]
            RAGb[RAG Builder<br/>:8090]
        end

        subgraph "Пайплайн 2: Индексация"
            RAGi[RAG Builder
:8090]
        end

        subgraph "Пайплайн 3: Поиск"
            QS[Query Service<br/>:8083]
            RAGs[RAG Search
:8091]
        end

        subgraph "Вспомогательные сервисы"
            AS[Analyse Service<br/>:8089]
            IS[Integration Service<br/>:8085]
            Auth[Auth Service<br/>:8082]
        end
    end

    subgraph "Хранилища"
        PG[(PostgreSQL
Registry DB<br/>:5432)]
        VEC[(PostgreSQL
pgvector<br/>:5432)]
        MinIO[(MinIO
Object Storage<br/>:9000)]
    end

    subgraph "Внешние системы"
        LLM[LLM Provider
OpenAI / Custom]
        Meridian[ИС Меридиан]
    end

    %% Соединения
    UI -->|HTTPS| Nginx
    Nginx -->|proxy :8080| GW
    GW -->|JWT / RBAC| Auth
    GW --> Orch
    GW --> QS

    Orch --> OCR
    Orch --> Pars
    Orch --> CV
    Orch --> Reg
    Orch --> RAGb

    CV -->|Чтение| PG
    Reg -->|Запись| PG
    RAGb -->|Запись| VEC
    RAGs -->|Чтение| VEC
    QS -->|Чтение/Запись| PG
    QS -->|Чтение| MinIO
    QS -->|Вызов LLM| LLM

    IS -->|Экспорт| Meridian
    AS -->|Чтение| PG

    Orch --> MinIO
    Orch --> PG

    %% Стили
    style GW fill:#e74c3c,color:#fff
    style Orch fill:#4a90d9,color:#fff
    style OCR fill:#e6f3ff
    style Pars fill:#e6f3ff
    style CV fill:#fff3e6
    style Reg fill:#e6ffe6
    style RAGb fill:#ffe6f3
    style RAGi fill:#ffe6f3
    style RAGs fill:#f3e6ff
    style QS fill:#fffacd
    style PG fill:#f9f9f9
    style VEC fill:#f0f0ff
    style MinIO fill:#ffe0e0
    style LLM fill:#e0ffe0
```

**Сводная таблица сервисов и портов:**

| Сервис              | Порт | Пайплайн | Доступ к БД        | Зависимости                        |
| ------------------- | ---- | -------- | ------------------ | ---------------------------------- |
| **Gateway**         | 8080 | —        | Нет                | Auth (JWT), Orchestrator, Query, Registry, Integration |
| **Nginx**           | 443  | —        | Нет                | Gateway (прокси) |
| Orchestrator        | 8081 | 1, 2     | Пишет (пре-стейдж) | OCR, Parser, Converter-validator, Registry, RAG Builder |
| Auth                | 8082 | —        | Читает             | PostgreSQL                         |
| Query Service       | 8083 | 3        | Читает/Пишет       | RAG Search, LLM, PostgreSQL        |
| Registry            | 8084 | 1        | Пишет              | PostgreSQL                         |
| Integration         | 8085 | —        | Читает/Пишет       | MinIO, Меридиан                    |
| Converter-validator | 8086 | 1        | Читает             | Registry (справочники)             |
| Parser              | 8087 | 1        | Нет                | MinIO                              |
| OCR                 | 8088 | 1        | Нет                | MinIO                              |
| Analyse             | 8089 | —        | Читает             | PostgreSQL                         |
| RAG Builder         | 8090 | 2        | Пишет              | PostgreSQL (pgvector)              |
| RAG Search          | 8091 | 3        | Читает             | PostgreSQL (pgvector)              |

**Требования к окружению:**

| Компонент           | Технология          | Версия | Примечание                          |
| ------------------- | ------------------- | ------ | ----------------------------------- |
| База данных         | PostgreSQL          | 15+    | С расширением pgvector              |
| Векторный индекс    | pgvector            | 0.7+   | Для хранения эмбеддингов            |
| Объектное хранилище | MinIO               | LATEST | Для файлов документов               |
| Кэш и очереди       | Redis               | 7+     | Для кэширования и асинхронных задач |
| LLM                 | OpenAI API / Custom | —      | Для генерации ответов               |

---

### 13. Политики повторных попыток и таймаутов (Retry / Timeout)

Детальные таблицы таймаутов и retry для каждого этапа — в соответствующих документах:

- **Пайплайн 1 (Формирование):** [политики retry](pipeline1-formation.md#политики-повторных-попыток-и-таймаутов)
- **Пайплайн 2 (Индексация):** [политики retry](pipeline2-indexation.md#политики-повторных-попыток-и-таймаутов)
- **Пайплайн 3 (Поиск):** [политики retry](pipeline3-search.md#политики-повторных-попыток-и-таймаутов)

#### Глобальные настройки longpoll

| Параметр                    | Значение                  | Описание                                                  |
| --------------------------- | ------------------------- | --------------------------------------------------------- |
| `longpoll_timeout`          | 15 секунд                 | Максимальное время ожидания на один longpoll-запрос       |
| `poll_interval`             | 1 секунда (серверная)     | Минимальный интервал между проверками статуса             |
| `max_retries_per_stage`     | 3                         | Максимальное количество retry на этап (по умолчанию)      |
| `jitter`                    | ±10%                      | Случайное отклонение для предотвращения "Thundering Herd" |
| `circuit_breaker_threshold` | 5 последовательных ошибок | Порог для Circuit Breaker (отключение этапа на 30с)       |

**Принципы:**

1. **Exponential backoff с jitter** — каждый повтор увеличивает задержку с добавлением случайности
2. **Immediate retry** — только для быстрых операций (< 100мс) с гарантированным идемпотентным эффектом
3. **Circuit Breaker** — при 5 последовательных ошибках этап отключается на 30 секунд
4. **Truncation on LLM error** — при ошибке генерации контекст усекается на 20% перед повтором
5. **No retry for idempotent writes** — запись в Registry и RAG Builder не повторяется при успешном HTTP-статусе, только при таймауте или сетевой ошибке
6. **Все retry логируются** — каждое повторение фиксируется в истории ошибок документа (`GET /documents/{doc_id}/errors`)
