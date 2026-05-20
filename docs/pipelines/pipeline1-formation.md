## 1. Пайплайн 1: Формирование документа

Назначение: преобразовать исходный файл в структурированную карточку документа в БД.

```mermaid
sequenceDiagram
    participant UI as UI / API
    participant Orch as Orchestrator
    participant Pars as Parsing
    participant Val as Validation
    participant Reg as Registry

    UI->>Orch: POST /documents (файл)
    activate Orch
    Orch->>Orch: Загрузка, SHA-256, MinIO
    Orch-->>UI: 202 {document_id, status: uploaded}
    deactivate Orch

    UI->>Orch: GET /documents/{id}/status
    activate Orch

    %% Этап 1: Parsing (изоляция от БД)
    Orch->>Pars: POST /ocr/process (file_ref)
    activate Pars
    Pars-->>Orch: JSON-контейнер (структура документа)
    deactivate Pars
    Orch-->>UI: status: parsing_completed

    %% Этап 2: Validation (читает БД)
    Orch->>Val: POST /validate (JSON-контейнер)
    activate Val
    Val->>Val: Проверка структуры
    Val->>Val: Классификация, уникальность
    Val->>Val: Сопоставление
    Val-->>Orch: JSON с оценкой (auto / review)
    deactivate Val

    %% Этап 3: Registry (пишет БД)
    Orch->>Reg: POST /registry/documents (JSON)
    activate Reg
    Reg->>Reg: Преобразование, карточка, БД
    Reg-->>Orch: JSON со ссылками в БД
    deactivate Reg

    Orch-->>UI: status: completed
    deactivate Orch

    Orch->>Orch: Запуск Пайплайна 2 (Индексация)
```

---

#### Этап 1: Parsing (полная изоляция от БД)

**Сервис:** Parsing / OCR Service

**Вход:** ссылка на файл в MinIO (изображение или PDF).

**Процесс:**

| Шаг | Действие | Результат |
|---|---|---|
| 1.1 | Скачать файл из MinIO | — |
| 1.2 | Очистка, нормализация изображения | Улучшение качества, ориентация |
| 1.3 | Распознавание документа (OCR / docling) | Текст, таблицы, изображения |
| 1.4 | Парсинг данных документа | Заголовки, разделы, метаданные |
| 1.5 | Построение структуры документа по оригиналу в виде JSON | Типизированная структура согласно типу документа |
| 1.6 | Оценка качества распознавания | confidence, статусы |

**Особенность:** полная изоляция от базы данных — сервис не имеет доступа к БД.

**Выход:** JSON-контейнер со структурой документа (`structure`), классификационными кодами (`classification`) и оценкой качества распознавания (`quality`). Детальный формат — в спецификации сервиса OCR.

> **Примечание:** JSON-формат известен только сервису Parsing и downstream-сервисам. Оркестратор оперирует им как непрозрачным контейнером.

---

#### Этап 2: Validation (читает БД)

**Сервис:** Validation Service

**Вход:** структурированный JSON от этапа Parsing.

**Процесс:**

| Шаг | Действие | Результат |
|---|---|---|
| 2.1 | Валидация структуры JSON | Проверка корректности и полноты |
| 2.2 | Классификация документа | Определение типа, эры, юрисдикции |
| 2.3 | Проверка уникальности в БД | Поиск дубликатов (SHA-256, title_hash) |
| 2.4 | Сопоставление с существующими документами | Связи преемственности (predecessor/successor) |
| 2.5 | Валидация классификационных кодов | По справочнику Registry (MKS, OKSTU, UDK) |

**Особенность:** единственный этап, который **читает** из базы данных.

**Выход:** JSON от Parsing, обогащённый результатами валидации — флаг `structure_valid`, статусы классификационных кодов (`classifiers`), результаты проверки уникальности (`uniqueness`) и сопоставления (`matching`), а также итоговое решение (`decision`: `auto` / `review_required`). Структура документа передаётся сквозным потоком.

---

#### Этап 3: Registry (пишет БД)

**Сервис:** Registry Service

**Вход:** JSON от этапа Validation (содержит структуру документа + результаты валидации).

**Процесс:**

| Шаг | Действие | Результат |
|---|---|---|
| 3.1 | Сохранение карточки документа в `nsi_documents` (doc_code, title, order, validity_status) | `document_id`, ссылки на ресурсы |
| 3.2 | Сохранение секций в `nsi.document_sections` (type, content JSONB), простановка `id` | Каждая секция получает DB-идентификатор |
| 3.3 | Сохранение табличных секций в `nsi_document_sections` (type='table') | Таблицы сохраняются как секции |
| 3.4 | Сохранение секций-изображений в `nsi_document_sections` (type='image') | Изображения получают прямые ссылки |
| 3.5 | Сохранение перекрёстных ссылок в `nsi_document_references` | Связи между элементами документа |
| 3.6 | Запись в `nsi_document_history` (event_type='promoted') | Фиксация факта публикации документа |

**Особенность:** единственный этап, который **пишет** в базу данных. Структура документа не меняется — только проставляются DB-ссылки.

**Выход:** тот же JSON, что и на входе, но с проставленными `id` для секций, `file_key` для изображений и блоком `registry` со ссылками на ресурсы в БД. Эти данные используются RAG для построения чанков и цитирования.

---

#### Примеры трансформации данных

Ниже показано, какие изменения вносятся в JSON-контейнер на каждом этапе Пайплайна 1. Оркестратор передаёт контейнер как непрозрачный артефакт — структура JSON известна только сервисам.

##### Этап 1 → 2: Parsing → Validation (обогащение результатами валидации)

**Вход Validation (выход Parsing):**

```json
{
  "document_id": "b3a8f1c2-...",
  "document": { ... },
  "structure": { ... },
  "classification": { ... },
  "quality": { ... }
}
```

**Выход Validation (добавляется блок `validation`):**

```json
{
  "document_id": "b3a8f1c2-...",
  "document": { ... },          // без изменений
  "structure": { ... },         // без изменений
  "classification": { ... },    // без изменений
  "quality": { ... },           // без изменений
  "validation": {               // ← ДОБАВЛЕНО
    "structure_valid": true,
    "decision": "auto",
    "classifiers": { ... },
    "uniqueness": { ... },
    "matching": { ... }
  }
}
```

**Что изменилось:** добавлен блок `validation` с решением (`auto` / `review_required`), статусами классификаторов, результатами проверки уникальности и сопоставления.

##### Этап 2 → 3: Validation → Registry (простановка DB-ссылок)

**Вход Registry (выход Validation):** JSON с блоками `structure`, `classification`, `quality`, `validation`.

**Выход Registry (добавляются `id` секций, `file_key`, блок `registry`):**

```json
{
  "document_id": "b3a8f1c2-...",
  "document": { ... },          // без изменений
  "structure": {
    "sections": [
      {
        "section_id": "sec-intro",  // ← ДОБАВЛЕНО (DB-идентификатор)
        "type": "text",
        "title": "Общие положения",
        "content": "...",
        "level": 1,
        "path": "/1"
      },
      {
        "section_id": "sec-table-1",  // ← ДОБАВЛЕНО
        "type": "table",
        "title": "Таблица 1 — Минимальные толщины",
        "content": { ... },
        "level": 2,
        "path": "/1/4.2/t1",
        "file_key": "b3a8f1c2/v1/table-1003.png"  // ← ДОБАВЛЕНО
      },
      ...
    ]
  },
  "classification": { ... },    // без изменений
  "quality": { ... },           // без изменений
  "validation": { ... },        // без изменений
  "registry": {                 // ← ДОБАВЛЕНО
    "document_id": "b3a8f1c2-...",
    "version_id": "ver-001",
    "created_at": "2026-05-15T12:00:18Z",
    "sections_count": 3,
    "references_count": 0
  }
}
```

**Что изменилось:**
- У каждой секции появился `section_id` (DB-идентификатор в `nsi_document_sections`)
- Для таблиц добавлен `file_key` (ссылка на изображение в MinIO)
- Добавлен блок `registry` с метаданными записи в БД
Этот обогащённый JSON передаётся в **Пайплайн 2 (Индексация)** как входной контейнер

---

#### Статусная модель (FSM)

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> uploaded : POST /documents
    uploaded --> parsing : запуск Parsing
    parsing --> validation : Parsing завершён
    validation --> ready_for_promotion : Validation пройдена (auto)
    validation --> review_required : требуется ручное подтверждение
    review_required --> validation : повторная Validation
    review_required --> approved : approve оператора
    ready_for_promotion --> registry : промотирование в Registry
    approved --> registry : промотирование в Registry
    
    registry --> [*] : документ сформирован
    registry --> archived
```

**Описание состояний:**

| Состояние | Описание |
|---|---|
| `draft` | Черновик после загрузки файла в MinIO |
| `uploaded` | Файл загружен, ожидание запуска парсинга |
| `parsing` | Выполняется OCR и распознавание структуры |
| `validation` | Валидация структуры, классификация, уникальность |
| `ready_for_promotion` | Авто-валидация пройдена, ожидание записи в Registry |
| `review_required` | Требуется ручное подтверждение оператором |
| `approved` | Оператор подтвердил, ожидание записи в Registry |
| `registry` | Документ записан в реестр (nsi_documents) |
| `archived` | Документ архивирован |

---

#### Обработка ошибок и компенсационные потоки

| Этап | Действие | При ошибке | Компенсация |
|---|---|---|---|
| Пре-стейдж (загрузка) | Сохранение в MinIO, создание записи в БД | Ошибка MinIO | Удалить запись из БД, вернуть ошибку UI |
| 1. Parsing | Распознавание и парсинг | Ошибка OCR/таймаут | Повтор (до 3 раз), при превышении — статус `failed` |
| 2. Validation | Валидация JSON, классификация | Ошибка структуры JSON | Вернуть `validation.errors`, статус `review_required` |
| 3. Registry | Запись карточки в БД | Ошибка записи | Откат транзакции, повтор (до 2 раз) |

```mermaid
graph TD
    subgraph "Пайплайн 1: Формирование"
        Upload[Загрузка файла] -->|Ошибка MinIO| Comp1[Компенсация: удалить запись из БД]
        Upload -->|Успех| Pars[Parsing]
        Pars -->|Ошибка OCR| Retry1[Повтор до 3 раз]
        Retry1 -->|Все попытки исчерпаны| Fail1[failed]
        Retry1 -->|Успех| Val[Validation]
        Pars -->|Успех| Val
        Val -->|Ошибка структуры| Review[review_required]
        Val -->|Успех| Reg[Registry]
        Reg -->|Ошибка записи| Retry2[Повтор до 2 раз]
        Retry2 -->|Все попытки исчерпаны| Fail1
        Retry2 -->|Успех| Done[Готово]
    end
```

---

#### Политики повторных попыток и таймаутов

| Этап | Таймаут (max) | Retry | Стратегия | Backoff |
|---|---|---|---|---|
| Загрузка файла в MinIO | 60с | 0 | — | — |
| OCR / Parsing | 300с (5 мин) | 3 | Exponential | 1с → 2с → 4с |
| Validation (JSON) | 30с | 1 | Immediate | — |
| Validation (уникальность) | 60с | 2 | Exponential | 1с → 2с |
| Registry (запись) | 30с | 2 | Exponential | 500мс → 1с |
