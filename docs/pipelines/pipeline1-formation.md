## 1. Пайплайн 1: Формирование документа (двухфазный: preview → решение → full)

Назначение: преобразовать исходный файл в структурированную карточку документа в БД.  
Пайплайн состоит из двух фаз: **Preview** (быстрая проверка, метаданные, решение пользователя) и **Full** (полная обработка).

**Черновик (draft) — обязательная точка входа:** `POST /drafts` всегда создаёт черновик. Без черновика загрузить документ невозможно. Из черновика данные передаются на конвертацию (Converter-validator) и после — в Registry (чистовик).

```mermaid
sequenceDiagram
    participant UI as Web UI
    participant Orch as Orchestrator
    participant OCR as OCR-сервис
    participant Pars as Parser-сервис
    participant Conv as Converter-validator
    participant Reg as Registry


    %% Фаза Preview
    UI->>Orch: POST /drafts/{draft_id}/preview
    activate Orch
    Orch->>Orch: Определение типа файла (скан/цифровой)
    alt Скан/изображение
        Orch->>OCR: POST /ocr/preview (max_pages=3)
        activate OCR
        OCR-->>Orch: Частичный сырой JSON (первые N стр.)
        deactivate OCR
    else Цифровой PDF/DOC
        Orch->>Pars: POST /parser/preview (max_pages=3)
        activate Pars
        Pars-->>Orch: Частичный сырой JSON (первые N стр.)
        deactivate Pars
    end
    Orch->>Conv: POST /converter/preview/metadata
    activate Conv
    Conv-->>Orch: Первичные метаданные
    deactivate Conv
    Orch->>Reg: POST /registry/documents/check-uniqueness (метаданные + file_size_bytes)
    activate Reg
    Reg-->>Orch: Список кандидатов-дубликатов
    deactivate Reg
    Orch-->>UI: Preview-данные (метаданные, дубликаты)
    deactivate Orch

    Note over UI,Orch: Пользователь принимает решение

    UI->>Orch: PATCH /drafts/{draft_id}/decide
    activate Orch
    alt action = approve
        Orch-->>UI: 202 {status: proceeding}

        %% Фаза Full
        alt Скан/изображение
            Orch->>OCR: POST /ocr/process (full)
            activate OCR
            OCR-->>Orch: Полный сырой JSON
            deactivate OCR
        else Цифровой PDF/DOC
            Orch->>Pars: POST /parser/process (full)
            activate Pars
            Pars-->>Orch: Полный сырой JSON
            deactivate Pars
        end

        Orch->>Conv: POST /converter/convert
        activate Conv
        Conv->>Conv: Построение иерархии, LLM, метаданные
        Conv-->>Orch: Иерархический типизированный JSON
        deactivate Conv

        Orch->>Reg: POST /registry/documents/check-uniqueness (метаданные + file_size_bytes)
        activate Reg
        Reg-->>Orch: { is_duplicate, candidates }
        deactivate Reg
        alt is_duplicate = true
            Orch-->>UI: status: duplicate (финальная проверка)
        else
            Orch->>Reg: POST /registry/documents (JSON)
            activate Reg
            Reg->>Reg: Сохранение карточки, сегментация на секции
            Reg-->>Orch: JSON со ссылками в БД
            deactivate Reg
            Orch-->>UI: status: completed
        end
    else action = reject (duplicate)
        Orch-->>UI: status: duplicate
    else action = reject (force_new_version)
        Orch->>Orch: Принудительное создание новой версии
        Orch-->>UI: status: new_version_created
    end
    deactivate Orch
```

---

### Фаза Preview

**Цель:** быстро получить первичные метаданные и проверить уникальность документа до полной обработки.

| Шаг | Действие | Сервис | Результат |
|-----|----------|--------|-----------|
| P.1 | Определение типа файла (скан/цифровой) | Оркестратор | Выбор OCR или Parser |
| P.2 | Preview-распознавание (первые N страниц) | OCR-сервис или Parser-сервис | Частичный сырой JSON |
| P.3 | Извлечение первичных метаданных | Converter-validator (preview API) | Обозначение, наименование, тип, даты |
| P.4 | Проверка уникальности (по метаданным + размеру) | Оркестратор → `POST /registry/documents/check-uniqueness` | Список кандидатов-дубликатов |
| P.5 | Отображение preview пользователю | UI | Метаданные + дубликаты |
| P.6 | Решение пользователя | UI → Оркестратор (`PATCH /drafts/{draft_id}/decide`) | approve / reject |

**Параметры preview:**

| Параметр | Значение по умолчанию | Описание |
|----------|----------------------|----------|
| `max_pages` | 3 | Количество страниц для preview-обработки |
| `preview_timeout` | 60с (OCR) / 30с (Parser) | Таймаут на preview-этап |
| `preview_llm_timeout` | 15с | Таймаут на LLM-вызов при извлечении метаданных |

---

### Фаза Full (полная обработка)

Запускается после решения пользователя `approve` (через `PATCH /drafts/{draft_id}/decide`). Черновик завершается, документ записывается в Registry через конвертацию. Состоит из трёх этапов.

### Форматы входных/выходных данных Full-фазы

| № | Сервис | Входной формат | Выходной формат |
|---|--------|---------------|----------------|
| 1.1 | OCR-сервис (`:8088`) / Parser-сервис (`:8087`) | `file_key` → бинарный файл из MinIO | `raw_ocr_v4` (JSON) — плоский массив блоков |
| 1.2 | Converter-validator (`:8086`) | `raw_ocr_v4` (JSON) | `validated_v3` (JSON) — иерархический типизированный |
| 1.3 | Registry (`:8084`) — `POST /check-uniqueness` | `file_hash_sha256`, `title_hash_sha256` | `{is_unique: bool, duplicate_of: bigint/null}` |
| 1.4 | Registry (`:8084`) — `POST /documents` | `validated_v3` + метаданные | `document_id` (bigint) |
| 1.5 | Orchestrator → Scheduler (RAG Builder) | `document_id` | Статус `pending_index` → Pipeline 2 |
| 1.6 | Orchestrator (очистка preview-артефактов) | `draft_id` | Удаление preview-данных (preview_metadata, preview_blobs) |

#### Этап 1: OCR-сервис и Parser-сервис (распознавание и извлечение сырых данных)

**Сервисы:** OCR-сервис (скан/изображения), Parser-сервис (цифровые PDF/DOC)

Два независимых сервиса с **единым контрактом выходных данных**.

**Вход:** ссылка на файл в MinIO.

**Процесс (единый для обоих сервисов):**

| Шаг | Действие | Вход | Выход | Результат |
|-----|----------|------|-------|-----------|
| 1.1 | Скачать файл из MinIO | `file_key` (из запроса Оркестратора) | Бинарный файл (PDF/TIFF/JPEG/PNG) | — |
| 1.2 | Очистка, нормализация изображения | Бинарный файл (изображение/PDF) | Нормализованное изображение (deskewed, cropped) | Улучшение качества, ориентация |
| 1.3 | Распознавание документа (OCR/docling) | Нормализованное изображение | Распознанные блоки (текст, таблицы, фигуры) | Текст, таблицы, изображения |
| 1.4 | Извлечение сырых блоков | Распознанные блоки | Плоский JSON-массив блоков | Плоский массив блоков (текст, таблица, фигура, формула) |
| 1.5 | Сохранение бинарных объектов в MinIO | Бинарные объекты (изображения из документа) | `fileKey` в MinIO | fileKey для изображений |
| 1.6 | Оценка качества распознавания | Плоский JSON-массив блоков | `confidence` (0..1), статусы (ok/warning/error) | confidence, статусы |

**Особенность:** полная изоляция от базы данных — сервис не имеет доступа к БД.  
**LLM не используется.**  
**Выход:** плоский сырой JSON (без иерархии, без заголовков).

> **Примечание:** JSON-формат известен только сервисам и downstream-сервисам. Оркестратор оперирует им как непрозрачным контейнером.

#### Этап 2: Converter-validator (конвертация и валидация)

**Сервис:** Converter-validator

**Вход:** полный сырой JSON от OCR или Parser.

**Процесс:**

| Шаг | Действие | Результат |
|-----|----------|-----------|
| 2.1 | Построение иерархии | Плоские блоки → разделы, подразделы, заголовки |
| 2.2 | Объединение таблиц, разорванных на страницах | Целостные таблицы |
| 2.3 | Извлечение метаданных (LLM, эвристики) | Обозначение, наименование, тип, даты, редакция |
| 2.4 | Распознавание перекрёстных ссылок | Нормализованные ссылки на ГОСТ/ТУ |
| 2.5 | Валидация структуры и полноты | Проверка соответствия схеме |
| 2.6 | — | Вычисление хэшей SHA-256 (content_hash, title_hash). Проверка уникальности выполняется Оркестратором после получения JSON (через `POST /registry/documents/check-uniqueness`) |

**Особенность:** использует LLM для иерархии, классификации и метаданных.  
**Выход:** иерархический типизированный JSON, близкий к итоговому документу.

#### Этап 3: Registry (сервис реестра документов)

**Сервис:** Registry Service

**Вход:** иерархический JSON от Converter-validator.

**Процесс:**

| Шаг | Действие | Результат |
|-----|----------|-----------|
| 3.1 | Сохранение карточки документа в `registry.documents` | `document_id`, ссылки на ресурсы |
| 3.2 | **Сегментирование:** разбиение на секции (`registry.document_sections`) | Каждая секция получает DB-идентификатор |
| 3.3 | Сохранение перекрёстных ссылок в `registry.document_references` | Связи между элементами документа |
| 3.4 | Запись в `registry.document_history` | Фиксация факта публикации документа |

**Выход:** плоский JSON со списком **секций** (не чанков) с метаданными и ссылками в БД.
**Далее:** статус `pending_index` → **передано в Пайплайн 2 (Индексация)**.

---

#### Примеры трансформации данных

##### Preview-фаза: сырой JSON → preview-метаданные + кандидаты в дубликаты

**Вход Converter-validator (preview):** частичный сырой JSON (первые N страниц).

**Выход preview/metadata:**
```json
{
  "doc_code": "ГОСТ 20868-81",
  "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
  "document_type": "normative",
  "year": "1981",
  "revision": null
}
```

##### Проверка уникальности (Оркестратор → Registry)

**Ответ `POST /registry/documents/check-uniqueness`:**
```json
{
  "is_duplicate": false,
  "is_duplicate_file": false,
  "candidates": [],
  "file_hash_sha256": "a1b2c3d4...",
  "title_hash_sha256": "e5f6a7b8...",
  "checked_at": "2026-05-15T12:00:00Z"
}
```

**title_hash_sha256** = SHA-256(`era` | `source_type` | `doc_code` | `normalized_title`)

где `normalized_title` — `title` в нижнем регистре с удалёнными лишними пробелами.

> **⚠️ Race condition**: Проверка уникальности через `check-uniqueness` неатомарна с последующей записью. Между check и write может быть вставлен другой документ. 
> **Решение**: использовать уникальный индекс `UNIQUE (file_hash_sha256)` в БД + `INSERT ... ON CONFLICT DO NOTHING` для атомарной проверки при записи.

##### Этап 1 → 2: OCR/Parser → Converter-validator (обогащение)

**Вход:** плоский сырой JSON (блоки страниц).  
**Выход:** иерархический JSON с разделами, метаданными, ссылками.

##### Этап 2 → 3: Converter-validator → Registry (простановка DB-ссылок)

**Вход:** иерархический JSON.  
**Выход:** JSON с проставленными `section_id`, `file_key`, блоком `registry`.

---

#### Статусная модель (FSM)

```mermaid
stateDiagram-v2
    [*] --> uploaded : POST /drafts
    uploaded --> previewing : запуск preview
    previewing --> awaiting_decision : Preview завершён
    previewing --> failed : ошибка распознавания

    awaiting_decision --> parsing : decision = proceed
    awaiting_decision --> duplicate : decision = stop_duplicate
    awaiting_decision --> new_version : decision = force_new_version
    awaiting_decision --> failed : таймаут 24ч

    parsing --> validation : OCR/Parser завершён
    parsing --> failed : таймаут 15 мин

    validation --> ready_for_promotion : авто-валидация пройдена
    validation --> review_required : требует ручного подтверждения
    validation --> failed : таймаут 30 мин

    review_required --> approved : approve оператора
    review_required --> validation : повторная валидация
    review_required --> failed : отклонено оператором
    review_required --> archived : таймаут 48ч

    ready_for_promotion --> registry : запись в Registry
    ready_for_promotion --> failed : таймаут 24ч

    approved --> registry : запись в Registry

    registry --> pending_index : запуск RAG Builder
    registry --> failed : ошибка записи в БД
    registry --> archived

    pending_index --> indexing : запуск индексации
    indexing --> indexed : индексация завершена
    indexing --> failed : ошибка индексации
    indexed --> [*] : готов к поиску

    failed --> uploaded : reprocess
```

**Описание состояний:**

| Состояние | Описание |
|---|---|
| `uploaded` | Файл загружен в MinIO, ожидание запуска preview |
| `previewing` | Выполняется preview-фаза (OCR/Parser preview + Converter preview) |
| `awaiting_decision` | Preview завершён, ожидание решения пользователя |
| `parsing` | Выполняется полный OCR/Parser |
| `validation` | Конвертация и валидация (Converter-validator) |
| `ready_for_promotion` | Авто-валидация пройдена, ожидание записи в Registry |
| `review_required` | Требуется ручное подтверждение оператором |
| `approved` | Оператор подтвердил, ожидание записи в Registry |
| `registry` | Документ записан в реестр (registry.documents) |
| `pending_index` | Ожидание запуска RAG Builder (Пайплайн 2) |
| `duplicate` | Документ-дубликат, обработка завершена |
| `new_version` | Создана новая версия существующего документа |
| `indexing` | Выполняется чанкинг, вычисление эмбеддингов, построение индекса |
| `indexed` | Документ проиндексирован, готов к поиску |
| `failed` | Ошибка на одном из этапов обработки |
| `archived` | Документ архивирован |

**Процесс создания новой версии (`force_new_version`):**
1. Документ в статусе `awaiting_decision` получает новый `version_number` (текущий + 1)
2. Все поля документа (название, коды, метаданные) копируются из предыдущей версии
3. `document_id` остаётся неизменным (логический документ тот же)
4. Новая версия индексируется заново (Pipeline 2)
5. Предыдущая версия доступна для просмотра через `GET /documents/{doc_id}/versions`

**Триггер `registry → archived`:** Документ архивируется автоматически через N дней после создания новой версии (настраиваемый параметр, по умолчанию 365 дней). Также архивация может быть инициирована вручную `system_admin`. Архивированный документ доступен только для чтения.

> **Черновики (drafts):** Черновик — основной элемент управления загрузкой документа. `file_key` — у черновика (`pipeline.drafts.file_key`). `raw_data` — в `pipeline.drafts.raw_data` (JSONB, результат Parser или OCR). MinIO — только для бинарных файлов (PDF, изображения). OCR/Parser выполняется **полностью** уже в черновике; Converter-validator — только извлечение метаданных. Полная конвертация (validated_v3) запускается при approve, после чего документ записывается в Registry. Решение пользователя принимается через `PATCH /drafts/{draft_id}/decide`. `task_id` — внутренний сквозной ID задачи (internal). Детальная реализация — см. [`docs/plans/drafts_storage_plan.md`](../plans/drafts_storage_plan.md).

**Жизненный цикл черновика (Draft FSM):**

```mermaid
stateDiagram-v2
    [*] --> new : POST /drafts
    new --> preview_ready : preview-фаза завершена
    new --> discarded : ошибка preview

    preview_ready --> promoted : approve
    preview_ready --> discarded : reject
    preview_ready --> discarded : автозавершение не прошло

    promoted --> [*] : документ в Registry
    discarded --> [*]
```

**Связь состояний черновика с состояниями документа:**

| Статус черновика | Статус документа | Описание |
|---|---|---|
| `new` | `uploaded` / `previewing` | Черновик создан при загрузке файла, выполняется preview-фаза |
| `preview_ready` | `awaiting_decision` | Preview завершён, метаданные извлечены. Если уникально и чисто — автозавершение; иначе — ожидание решения человека |
| `promoted` | `parsing` → `validation` → `registry` | Черновик утверждён. Запускается полная конвертация (validated_v3) и запись документа в Registry |
| `discarded` | `failed` / `archived` | Черновик отклонён (человеком или автоматом). Можно загрузить файл повторно для новой попытки (новый draft) |

---

#### Обработка ошибок и компенсационные потоки

| Этап | Действие | При ошибке | Компенсация |
|---|---|---|---|
| Пре-стейдж (загрузка) | Сохранение в MinIO, создание записи в БД | Ошибка MinIO | Удалить запись из БД, вернуть ошибку UI |
| Preview OCR/Parser | Распознавание первых N страниц | Ошибка распознавания | Статус `preview_failed` |
| Preview Converter-validator | Извлечение метаданных | Ошибка извлечения метаданных | `awaiting_decision` с флагом ошибки |
| Preview проверка уникальности (Оркестратор → Registry) | Проверка по метаданным через `check-uniqueness` | Ошибка Registry | `awaiting_decision` (повтор при доступности) |
| Full OCR/Parser | Распознавание и парсинг | Ошибка OCR/таймаут | Повтор (до 3 раз), при превышении — статус `failed` |
| Full Converter-validator | Конвертация, валидация | Ошибка структуры JSON | Вернуть `validation.errors`, статус `review_required` |
| Full проверка уникальности (Оркестратор → Registry) | Финальная верификация через `check-uniqueness` | Ошибка Registry / дубликат | `duplicate` (если дубликат) / повтор (если ошибка Registry) |
| Registry | Запись карточки в БД | Ошибка записи | Откат транзакции, повтор (до 2 раз) |

```mermaid
graph TD
    subgraph "Пайплайн 1: Формирование"
        Upload[Загрузка файла] -->|Ошибка MinIO| Comp1[Компенсация: удалить запись из БД]
        Upload -->|Успех| Prev[Preview]
        Prev -->|Ошибка OCR/Parser| PrevFail[preview_failed]
        Prev -->|Ошибка метаданных| AwaitDec[awaiting_decision с флагом ошибки]
        Prev -->|Успех| AwaitDec
        AwaitDec -->|proceed| Pars[OCR/Parser Full]
        AwaitDec -->|stop| Dup[duplicate]
        AwaitDec -->|force_new| NewVer[new_version]
        Pars -->|Ошибка OCR| Retry1[Повтор до 3 раз]
        Retry1 -->|Все попытки исчерпаны| Fail[failed]
        Retry1 -->|Успех| Val[Converter-validator]
        Pars -->|Успех| Val
        Val -->|Ошибка структуры| Review[review_required]
        Val -->|Успех| Uniq{Проверка уникальности}
        Uniq -->|Ошибка Registry| RetryUniq[Повтор]
        RetryUniq -->|Успех| Uniq
        RetryUniq -->|Все попытки| Fail
        Uniq -->|Дубликат| Dup
        Uniq -->|Уникален| Reg[Registry]
        Reg -->|Ошибка записи| Retry2[Повтор до 2 раз]
        Retry2 -->|Все попытки исчерпаны| Fail
        Retry2 -->|Успех| Done[Готово]
    end
```

---

#### Политики повторных попыток и таймаутов

| Этап | Таймаут (max) | Retry | Стратегия | Backoff |
|---|---|---|---|---|
| Загрузка файла в MinIO | 60с | 0 | — | — |
| OCR preview | 60с | 1 | Immediate | — |
| Parser preview | 30с | 1 | Immediate | — |
| Converter preview (metadata) | 15с | 0 | — | — |
| Registry check-uniqueness (preview) | 15с | 1 | Immediate | — |
| Registry check-uniqueness (full) | 15с | 1 | Immediate | — |
| OCR Full | 300с (5 мин) | 3 | Exponential | 1с → 2с → 4с |
| Parser Full | 300с (5 мин) | 3 | Exponential | 1с → 2с → 4с |
| Converter-validator (full) | 120с (2 мин) | 2 | Exponential | 1с → 2с |
| Registry (запись) | 30с | 2 | Exponential | 500мс → 1с |

#### Защита от «зависших» состояний (тупиковые таймауты)

Для состояний, требующих действия человека или внешнего триггера, установлены **таймауты ожидания**,
по истечении которых документ автоматически переводится в `failed` (или `archived`) с соответствующим кодом ошибки:

| Состояние | Таймаут ожидания | Действие по истечении | Код ошибки |
|---|---|---|---|
| `awaiting_decision` | 24 часа | Перевод в `failed` | `DECISION_TIMEOUT` |
| `review_required` | 48 часов | Перевод в `archived` | `REVIEW_TIMEOUT` |
| `pending_index` | 1 час | Перевод в `failed` | `INDEX_TRIGGER_TIMEOUT` |
| `parsing` | 15 минут | Перевод в `failed` | `PARSING_TIMEOUT` |
| `validation` | 30 минут | Перевод в `failed` | `VALIDATION_TIMEOUT` |
| `uploaded` | 1 час | Перевод в `failed` | `PREVIEW_TRIGGER_TIMEOUT` |

Таймауты отсчитываются с момента входа в состояние и проверяются **Scheduler-сервисом** (или CRON-задачей),
запускаемым каждые 5 минут. При переводе в `failed`:
- В `registry.document_history` создаётся запись с указанием причины.
- Система отправляет уведомление ответственному пользователю (email/внутреннее).
- Документ доступен для повторной загрузки (не удаляется).

#### Кэширование результатов preview-фазы

Preview-фаза обрабатывает первые N страниц документа (OCR/Parser preview + Converter-validator preview).
Чтобы избежать двойного распознавания одних и тех же страниц при переходе к полной обработке:

1. Результаты preview (частичный сырой JSON от OCR/Parser, метаданные от Converter-validator) **сохраняются**
   в журнале Оркестратора (`GET /documents/{doc_id}/history`) как временный артефакт.
2. При запуске полной фазы (`proceed`) Оркестратор **передаёт preview-результаты** в full-этапы:
   - OCR/Parser full начинает обработку со страницы `max_pages + 1`, избегая повторной обработки preview-страниц.
   - Converter-validator full использует preview-метаданные как основу, дообогащая их полными данными.
3. Если preview-результаты по какой-то причине недоступны (очищены по TTL), full-фаза запускается
   с самого начала (все страницы).

**TTL preview-артефактов:** 7 дней с момента создания. По истечении — автоматическая очистка.

> **Примечание:** Повторный вызов `PATCH /drafts/{draft_id}/decide` для черновиков в терминальных статусах
(`promoted`, `discarded`) возвращает ошибку `409 CONFLICT` с кодом `DRAFT_ALREADY_DECIDED`.
Пользователь должен создать новый документ (новый черновик).
