## API Query service

- **`/text/*`** — обработка произвольного текста пользователя через LLM (нормализация, поиск, вопрос-ответ)
- **`/chat/*`** — управление диалоговыми сессиями (создание, история, контекст, экспорт, обратная связь)

### Обработка произвольного текста пользователя

Сценарий: инженер копирует фрагмент из внешнего источника (письмо, ТЗ, заметка, статья) и хочет:

- нормализовать текст в структурированный запрос к системе
- найти релевантные документы под этот текст
- получить ответ с трассировкой, как если бы он задал вопрос вручную

| Метод | Путь           | Параметры                                       | Описание                                                                                | Возвращает                                     |
| ----- | -------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------- | ---------------------------------------------- |
| POST  | `/text/search` | Body:`text`, `document_ids`, `top_k`, `filters`  | Поиск документов, релевантных произвольному тексту (без ручной формулировки запроса)    | Результаты поиска + автосгенерированный запрос |
| POST  | `/text/ask`    | Body:`text`, `document_ids`, `options`           | Задать вопрос на основе произвольного текста — система сама выделит суть и найдёт ответ | Ответ с источниками + нормализованный вопрос   |

#### POST /text/search

Поиск документов по произвольному тексту — система сама выделяет суть, нормализует в запрос и выполняет поиск.

**Запрос**:

```json
{
  "text": "В письме заказчика просят подтвердить, что обшивка ледового пояса 14 мм соответствует Arc4. Также интересуют требования к сварке в этом районе.",
  "document_ids": null,
  "top_k": 10,
  "filters": {
    "document_type": ["normative", "drawing"]
  },
  "options": {
    "auto_decompose": true,
    "max_subqueries": 3
  }
}
```

| Поле                     | Тип      | Обязательность | Описание                                                        |
| ------------------------ | -------- | -------------- | --------------------------------------------------------------- |
| `text`                   | string   | Да             | Произвольный текст для поиска.                                  |
| `document_ids`           | string[] | Нет            | Ограничить поиск конкретными документами.                       |
| `top_k`                  | int      | Нет            | Количество результатов (по умолчанию 5).                        |
| `filters`                | object   | Нет            | Фильтры по типу документа, дате и т.д.                          |
| `options.auto_decompose` | bool     | Нет            | Автоматически разбивать сложный текст на несколько подзапросов. |
| `options.max_subqueries` | int      | Нет            | Максимальное число подзапросов при декомпозиции.                |

**Ответ `200`**:

```json
{
  "original_text": "В письме заказчика просят подтвердить...",
  "analysis": {
    "normalized_query": "толщина обшивки ледового пояса Arc4 и требования к сварке",
    "entities": [
      {"type": "ice_class", "value": "Arc4"},
      {"type": "parameter", "value": "толщина обшивки"},
      {"type": "process", "value": "сварка"}
    ],
    "subqueries": [
      "толщина обшивки ледового пояса Arc4",
      "требования к сварке ледовый пояс"
    ]
  },
  "results": [
    {
      "fragment_id": "frg-042",
      "document_id": "doc-norm-001",
      "document_title": "Правила РС, часть I",
      "page_number": 42,
      "text": "Для ледового класса Arc4 толщина обшивки...",
      "coordinates": {"x": 120, "y": 350, "width": 400, "height": 60},
      "score": 0.94,
      "document_type": "normative",
      "matched_subquery": "толщина обшивки ледового пояса Arc4"
    },
    {
      "fragment_id": "frg-128",
      "document_id": "doc-norm-001",
      "document_title": "Правила РС, часть I",
      "page_number": 58,
      "text": "Сварные швы ледового пояса должны выполняться...",
      "coordinates": {"x": 100, "y": 500, "width": 400, "height": 80},
      "score": 0.87,
      "document_type": "normative",
      "matched_subquery": "требования к сварке ледовый пояс"
    }
  ],
  "total_found": 7,
  "processing_time_ms": 1850
}
```

---

#### POST /text/ask

Задать вопрос на основе произвольного текста — система сама выделит суть, найдёт источники и сгенерирует ответ.

**Запрос**:

```json
{
  "text": "Заказчик в письме №456 спрашивает: почему в спецификации 21900M2 для кницы указана сталь 09Г2С, хотя по ГОСТ 11265-73 вроде бы требуется сталь 10ХСНД? Проверьте, пожалуйста.",
  "document_ids": null,
  "options": {
    "temperature": 0.1,
    "auto_decompose": true
  }
}
```

**Параметры**: `text` (обязательно), `document_ids` (опционально), `options` (temperature, auto_decompose).

**Ответ `200`**:

```json
{
  "original_text": "Заказчик в письме №456 спрашивает...",
  "normalized_question": "Соответствует ли марка стали 09Г2С для кницы в спецификации 21900M2 требованиям ГОСТ 11265-73? Допустима ли замена стали 10ХСНД на 09Г2С?",
  "answer": "Согласно ГОСТ 11265-73 «Кнехты. Технические условия», для деталей данного типа рекомендуется сталь 10ХСНД. Однако в спецификации 21900M2.362135.0903 указана сталь 09Г2С. \n\nАнализ показывает:\n1. ГОСТ 11265-73 регламентирует кнехты, а не кницы — возможно, заказчик ошибочно ссылается на этот стандарт.\n2. Сталь 09Г2С является допустимой заменой 10ХСНД для судовых конструкций согласно Правилам РС (Часть I, стр. 156) при условии сохранения эквивалентной прочности.\n\nРекомендуется уточнить у заказчика применимость ГОСТ 11265-73 к данному типу деталей.",
  "sources": [
    {
      "document_id": "doc-gost-001",
      "document_title": "ГОСТ 11265-73",
      "page_number": 3,
      "fragment_id": "frg-201",
      "text": "Для изготовления кнехтов применяется сталь марки 10ХСНД...",
      "score": 0.91
    },
    {
      "document_id": "doc-spec-001",
      "document_title": "21900M2.362135.0903",
      "page_number": 2,
      "fragment_id": "frg-305",
      "text": "Поз. 1 Кница — сталь 09Г2С...",
      "score": 0.95
    },
    {
      "document_id": "doc-norm-001",
      "document_title": "Правила РС, часть I",
      "page_number": 156,
      "fragment_id": "frg-410",
      "text": "Допускается замена стали 10ХСНД на 09Г2С...",
      "score": 0.83
    }
  ],
  "entities_discussed": [
    {"type": "material", "values": ["сталь 09Г2С", "сталь 10ХСНД"]},
    {"type": "document", "values": ["ГОСТ 11265-73", "21900M2.362135.0903"]},
    {"type": "part", "values": ["кница"]}
  ],
  "disclaimer": "Ответ сгенерирован на основе найденных документов. Требуется инженерная верификация.",
  "processing_time_ms": 4200,
  "model_used": "llama-3-70b"
}
```

---

### Обслуживание чата (диалоговые сессии)

Сценарий: инженер ведёт диалог с системой, переписывается в рамках одной сессии, контекст сохраняется. Нужны API для управления этим диалогом.

| Метод  | Путь                                   | Параметры                                                              | Описание                                              | Возвращает                             |
| ------ | -------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------- |
| POST   | `/chat/sessions`                       | Body:`title`, `document_ids`, `options`                                | Создать новую диалоговую сессию                       | `session_id`, `title`, `created_at`    |
| GET    | `/chat/sessions`                       | Query:`limit`, `offset`, `search`                                      | Список сессий пользователя                            | `sessions[]`, `total`                  |
| GET    | `/chat/sessions/{session_id}`          | Path:`session_id`, Query: `limit`, `before`                            | История сообщений в сессии                            | `session_id`, `messages[]`, `has_more` |
| PUT    | `/chat/sessions/{session_id}`          | Path:`session_id`, Body: `title`, `document_ids`                       | Обновить параметры сессии                             | Обновлённый объект сессии              |
| DELETE | `/chat/sessions/{session_id}`          | Path:`session_id`                                                      | Удалить сессию и историю                              | `session_id`, `deleted_at`             |
| POST   | `/chat/sessions/{session_id}/messages` | Path:`session_id`, Body: `content`, `attachments`, `options`          | Отправить сообщение в сессию (основной метод общения) | Ответ ассистента с источниками         |
| POST   | `/chat/sessions/{session_id}/context`  | Path:`session_id`, Body: `action`, `params`                            | Управление контекстом сессии                          | Результат операции                     |
| POST   | `/chat/sessions/{session_id}/export`   | Path:`session_id`, Body: `format`                                      | Экспорт диалога                                       | `export_id`, `url`                     |
| POST   | `/chat/feedback`                       | Body:`session_id`, `message_id`, `rating`, `comment`                   | Обратная связь по ответу                              | `feedback_id`, `created_at`            |

#### POST /chat/sessions

Создание новой диалоговой сессии.

**Запрос**:

```json
{
  "title": "Проверка требований Arc4 для проекта 21900M2",
  "document_ids": ["doc-norm-001", "doc-draw-001", "doc-spec-001"],
  "options": {
    "model": "llama-3-70b",
    "temperature": 0.2,
    "max_context_messages": 20,
    "system_prompt_override": null
  }
}
```

| Поле                             | Тип      | Обязательность | Описание                                                                      |
| -------------------------------- | -------- | -------------- | ----------------------------------------------------------------------------- |
| `title`                          | string   | Нет            | Человекочитаемое название сессии. Если не задано — авто из первого сообщения. |
| `document_ids`                   | string[] | Нет            | Документы, ограничивающие область поиска во всей сессии.                      |
| `options.model`                  | string   | Нет            | LLM-модель для сессии.                                                        |
| `options.temperature`            | float    | Нет            | Температура генерации.                                                        |
| `options.max_context_messages`   | int      | Нет            | Сколько последних сообщений держать в контексте (по умолчанию 20).            |
| `options.system_prompt_override` | string   | Нет            | Переопределение системного промпта для этой сессии.                           |

**Ответ `201`**:

```json
{
  "session_id": "sess-a1b2c3",
  "title": "Проверка требований Arc4 для проекта 21900M2",
  "user_id": "u-001",
  "document_ids": ["doc-norm-001", "doc-draw-001", "doc-spec-001"],
  "options": {
    "model": "llama-3-70b",
    "temperature": 0.2,
    "max_context_messages": 20
  },
  "message_count": 0,
  "created_at": "2026-04-27T14:00:00Z",
  "updated_at": "2026-04-27T14:00:00Z"
}
```

---

#### GET /chat/sessions

Список сессий текущего пользователя.

**Параметры query**: `limit`, `offset`, `search` (по title).

**Ответ `200`**:

```json
{
  "sessions": [
    {
      "session_id": "sess-a1b2c3",
      "title": "Проверка требований Arc4",
      "document_ids": ["doc-norm-001"],
      "message_count": 12,
      "last_message_preview": "Согласно Правилам РС, толщина обшивки...",
      "created_at": "2026-04-27T14:00:00Z",
      "updated_at": "2026-04-27T14:30:00Z"
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

---

#### GET /chat/sessions/ {session_id}

История сообщений в сессии.

**Параметры query**: `limit` (по умолчанию 50), `before` (cursor — ID сообщения, раньше которого загружать историю).

**Ответ `200`**:

```json
{
  "session_id": "sess-a1b2c3",
  "title": "Проверка требований Arc4",
  "document_ids": ["doc-norm-001"],
  "messages": [
    {
      "message_id": "msg-001",
      "role": "user",
      "content": "Какая толщина обшивки для Arc4?",
      "timestamp": "2026-04-27T14:01:00Z"
    },
    {
      "message_id": "msg-002",
      "role": "assistant",
      "content": "Согласно Правилам РС (Часть I, стр. 42), толщина обшивки ледового пояса для класса Arc4 должна быть не менее 12 мм.",
      "sources": [
        {
          "document_id": "doc-norm-001",
          "document_title": "Правила РС, часть I",
          "page_number": 42,
          "fragment_id": "frg-042",
          "text": "Для ледового класса Arc4 толщина обшивки...",
          "score": 0.94
        }
      ],
      "model_used": "llama-3-70b",
      "processing_time_ms": 3200,
      "feedback": null,
      "timestamp": "2026-04-27T14:01:04Z"
    },
    {
      "message_id": "msg-003",
      "role": "user",
      "content": "А какие марки стали допускаются?",
      "timestamp": "2026-04-27T14:02:00Z"
    },
    {
      "message_id": "msg-004",
      "role": "assistant",
      "content": "Для обшивки ледового пояса класса Arc4 допускаются стали категории D и E с гарантией хладостойкости (Правила РС, Часть I, стр. 44).",
      "sources": [
        {
          "document_id": "doc-norm-001",
          "document_title": "Правила РС, часть I",
          "page_number": 44,
          "fragment_id": "frg-128",
          "text": "Материал обшивки ледового пояса — сталь категории D...",
          "score": 0.89
        }
      ],
      "model_used": "llama-3-70b",
      "processing_time_ms": 2800,
      "feedback": {
        "rating": "positive",
        "comment": "Точно и быстро"
      },
      "timestamp": "2026-04-27T14:02:05Z"
    }
  ],
  "has_more": false
}
```

---

#### POST /chat/sessions/{session_id}/messages

Отправка нового сообщения в сессию. **Основной метод общения** в чате — заменяет прямые вызовы `/ask` при работе в диалоговом режиме.

**Запрос**:

```json
{
  "content": "Проверь, соответствует ли толщина обшивки 14 мм в чертеже 21900M2 этому требованию",
  "attachments": [
    {
      "type": "text_fragment",
      "text": "Обшивка ледового пояса t=14 мм",
      "source_document_id": "doc-draw-001",
      "source_page_number": 1
    }
  ],
  "options": {
    "search_in_session_docs": true,
    "use_full_context": true
  }
}
```

| Поле                               | Тип    | Обязательность | Описание                                                                 |
| ---------------------------------- | ------ | -------------- | ------------------------------------------------------------------------ |
| `content`                          | string | Да             | Текст сообщения пользователя.                                            |
| `attachments`                      | array  | Нет            | Прикреплённые фрагменты (текст, ссылки на страницы, координаты).         |
| `attachments[].type`               | string | —              | `text_fragment`, `document_reference`, `page_reference`, `external_url`. |
| `attachments[].text`               | string | —              | Текст фрагмента (для`text_fragment`).                                    |
| `attachments[].source_document_id` | string | —              | ID документа-источника.                                                  |
| `attachments[].source_page_number` | int    | —              | Номер страницы.                                                          |
| `options.search_in_session_docs`   | bool   | Нет            | Искать только в документах, привязанных к сессии.                        |
| `options.use_full_context`         | bool   | Нет            | Использовать полную историю диалога как контекст.                        |

**Ответ `200`**:

```json
{
  "message_id": "msg-005",
  "session_id": "sess-a1b2c3",
  "role": "assistant",
  "content": "Да, толщина обшивки 14 мм в чертеже 21900M2.362135.0903СБ соответствует требованию Правил РС для ледового класса Arc4 (не менее 12 мм). Превышение составляет 2 мм, что допустимо.",
  "sources": [
    {
      "document_id": "doc-norm-001",
      "document_title": "Правила РС, часть I",
      "page_number": 42,
      "fragment_id": "frg-042",
      "text": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм.",
      "score": 0.94
    },
    {
      "document_id": "doc-draw-001",
      "document_title": "21900M2.362135.0903СБ",
      "page_number": 1,
      "fragment_id": "frg-501",
      "text": "Обшивка ледового пояса t=14 мм",
      "score": 1.0
    }
  ],
  "model_used": "llama-3-70b",
  "processing_time_ms": 3800,
  "timestamp": "2026-04-27T14:03:05Z"
}
```

---

#### POST /chat/sessions/\{session_id}/context

Сервисные операции с контекстом сессии.

**Действия (`action`)**:

| action                | Описание                                      | params                      |
| --------------------- | --------------------------------------------- | --------------------------- |
| `clear`               | Очистить историю диалога, сохранить настройки | `{}`                        |
| `summarize`           | Сгенерировать краткое резюме диалога          | `{"max_length": 200}`       |
| `add_documents`       | Добавить документы в область поиска сессии    | `{"document_ids": ["..."]}` |
| `remove_documents`    | Убрать документы из области поиска            | `{"document_ids": ["..."]}` |
| `set_system_prompt`   | Переопределить системный промпт               | `{"system_prompt": "..."}`  |
| `reset_system_prompt` | Сбросить на стандартный                       | `{}`                        |

**Пример запроса** (очистка контекста):

```json
{
  "action": "clear",
  "params": {}
}
```

**Ответ `200`**:

```json
{
  "session_id": "sess-a1b2c3",
  "action": "clear",
  "status": "completed",
  "message": "История диалога очищена. Настройки сессии сохранены.",
  "timestamp": "2026-04-27T14:30:00Z"
}
```

**Пример запроса** (резюме диалога):

```json
{
  "action": "summarize",
  "params": {
    "max_length": 150
  }
}
```

**Ответ `200`**:

```json
{
  "session_id": "sess-a1b2c3",
  "action": "summarize",
  "status": "completed",
  "summary": "Обсуждались требования к обшивке ледового пояса для класса Arc4. Установлено: толщина ≥12 мм, сталь категории D/E. Чертеж 21900M2 соответствует требованиям (14 мм).",
  "message_count": 12,
  "timespan": "с 14:00 до 14:30",
  "processing_time_ms": 450
}
```

---

#### POST /chat/sessions/\{session_id}/export

Экспорт диалога в различных форматах.

**Запрос**:

```json
{
  "format": "pdf",
  "options": {
    "include_sources": true,
    "include_timestamps": true,
    "include_metadata": true,
    "page_size": "A4"
  }
}
```

| `format`   | Описание                                                   |
| ---------- | ---------------------------------------------------------- |
| `pdf`      | Структурированный PDF с вопросами, ответами и источниками. |
| `json`     | Полный JSON с историей сообщений.                          |
| `markdown` | Markdown-файл для вставки в отчёты.                        |
| `html`     | HTML-страница для просмотра в браузере.                    |

**Ответ `200`**:

```json
{
  "export_id": "exp-001",
  "session_id": "sess-a1b2c3",
  "format": "pdf",
  "status": "completed",
  "url": "/files/exports/exp-001/download",
  "expires_at": "2026-05-04T14:30:00Z",
  "created_at": "2026-04-27T14:35:00Z"
}
```

---

#### POST /chat/feedback

Обратная связь по конкретному ответу ассистента.

**Запрос**:

```json
{
  "session_id": "sess-a1b2c3",
  "message_id": "msg-004",
  "rating": "positive",
  "comment": "Точно указал страницу и марку стали, отлично",
  "aspects": [
    {"aspect": "accuracy", "rating": 5},
    {"aspect": "completeness", "rating": 4},
    {"aspect": "traceability", "rating": 5}
  ]
}
```

| Поле         | Тип    | Обязательность | Описание                                  |
| ------------ | ------ | -------------- | ----------------------------------------- |
| `session_id` | string | Да             | ID сессии.                                |
| `message_id` | string | Да             | ID сообщения ассистента.                  |
| `rating`     | string | Да             | `positive`, `negative`, `neutral`.        |
| `comment`    | string | Нет            | Текстовый комментарий (до 1000 символов). |
| `aspects`    | array  | Нет            | Оценка по отдельным аспектам (0-5).       |

**Ответ `201`**:

```json
{
  "feedback_id": "fb-001",
  "session_id": "sess-a1b2c3",
  "message_id": "msg-004",
  "rating": "positive",
  "comment": "Точно указал страницу и марку стали, отлично",
  "created_at": "2026-04-27T14:10:00Z"
}
```
