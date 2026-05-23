## API Converter-validator Service (converter-validator:8086)

Сервис конвертации и валидации документов. Объединяет конвейер преобразования сырого JSON в иерархический типизированный JSON с опциональным использованием LLM.

**Внутренний сервис.** Имеет два режима работы:
1. **Preview** — быстрые операции без записи в БД и без LLM (если не указано иное).
2. **Full** — полная конвертация с построением иерархии, LLM-обработкой, валидацией и кросс-ссылками.

**Базовый URL (внутренний)**: `http://127.0.0.1:8086/api/v1`

### Формат ответа

Успех — данные возвращаются напрямую.  
При ошибке: `{ "error": { "code": "CONVERSION_FAILED", "message": "...", "details": {} } }`

---

## Preview API

Эндпоинты предварительного просмотра. Выполняются быстро, без записи в БД, без полного цикла валидации.

### POST /converter/preview/metadata

Извлечение базовых метаданных из частичного сырого JSON.

**Вход:** частичный raw JSON (может содержать неполные данные).

**Выход:** designation, title, type, dates, revision.

**Запрос:**

```json
{
  "raw": {
    "designation": "ГОСТ Р 12345-77",
    "title": "Название документа",
    "type": "normative",
    "date_publication": "1981-01-15",
    "revision": "1"
  }
}
```

**Ответ `200`:**

```json
{
  "designation": "ГОСТ Р 12345-77",
  "title": "Название документа",
  "type": "normative",
  "dates": {
    "publication": "1981-01-15",
    "effective": null,
    "expiry": null
  },
  "revision": "1"
}
```

### POST /converter/preview/uniqueness

Проверка уникальности по первичным метаданным. Выполняет поиск возможных дубликатов.

**Вход:** первичные метаданные (designation, title, type, dates).

**Выход:** список кандидатов-дубликатов с краткими карточками.

**Запрос:**

```json
{
  "designation": "ГОСТ Р 12345-77",
  "title": "Название документа",
  "type": "normative"
}
```

**Ответ `200`:**

```json
{
  "duplicate_candidates": [
    {
      "document_id": "b3a8f1c2-...",
      "designation": "ГОСТ Р 12345-77",
      "title": "Название документа",
      "similarity": 0.98,
      "type": "normative",
      "revision": "2"
    }
  ],
  "total_candidates": 1
}
```

---

## Full API

Эндпоинты полного цикла конвертации и валидации.

### POST /converter/convert

Полная конвертация: иерархия, LLM, метаданные, кросс-ссылки.

**Вход:** полный raw JSON (все секции, таблицы, изображения, метаданные).

**Выход:** иерархический типизированный JSON.

**Процесс внутри:**

| Шаг | Действие | Зависимости |
|---|---|---|
| 1 | Построение иерархии документа | Нет |
| 2 | LLM-обработка (если `use_llm = true`) | Шаг 1 |
| 3 | Извлечение и валидация метаданных | Шаг 1–2 |
| 4 | Валидация структуры JSON | Шаг 1 |
| 5 | Классификация документа (тип, эра, юрисдикция) | Шаг 3 |
| 6 | Проверка уникальности (SHA-256, title_hash) | Шаг 3 |
| 7 | Сопоставление с существующими документами (predecessor/successor) | Шаг 3 |
| 8 | Валидация классификационных кодов (через Registry) | Шаг 5 |
| 9 | Построение кросс-ссылок | Шаг 1, 7 |

**LLM-параметры** (передаются в корне запроса):

| Поле | Тип | Описание | По умолчанию |
|---|---|---|---|
| `use_llm` | bool | Включить LLM-обработку | `false` |
| `llm_model` | string | Модель LLM (например, `gpt-4o`, `gpt-4o-mini`) | `"gpt-4o-mini"` |
| `llm_max_tokens` | int | Максимальное количество токенов на запрос | `4096` |
| `llm_timeout` | int | Таймаут LLM-запроса в секундах | `60` |

**Запрос:**

```json
{
  "task_id": "task-8a3f2b",
  "version_id": "c4b9f2d3-...",
  "use_llm": true,
  "llm_model": "gpt-4o-mini",
  "llm_max_tokens": 4096,
  "llm_timeout": 60,
  "structure": {
    "type": "normative",
    "title": "ГОСТ Р 12345-77",
    "sections": [ ... ],
    "tables": [ ... ],
    "images": [ ... ]
  },
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null,
    "udk_code": "629.5.021",
    "year": "1981"
  },
  "quality": {
    "confidence": 0.94,
    "pages_processed": 12,
    "pages_failed": 0
  }
}
```

**Ответ `200`:**

```json
{
  "conversion_id": "conv-001",
  "document_id": "b3a8f1c2-...",
  "hierarchy": {
    "type": "normative",
    "title": "ГОСТ Р 12345-77",
    "children": [ ... ]
  },
  "metadata": {
    "designation": "ГОСТ Р 12345-77",
    "title": "Название документа",
    "type": "normative",
    "dates": {
      "publication": "1981-01-15",
      "effective": null,
      "expiry": null
    },
    "revision": "1"
  },
  "validation": {
    "validation_id": "val-001",
    "structure_valid": true,
    "classification": {
      "mks_oks_code": "47.020",
      "mks_status": "CONFIRMED",
      "okstu_status": "NOT_USED",
      "udk_code": "629.5.021",
      "overall_status": "CONFIRMED"
    },
    "uniqueness": {
      "is_duplicate_file": false,
      "is_duplicate_document": false,
      "content_hash_sha256": "abc123...",
      "title_hash_sha256": "def456..."
    },
    "matching": {
      "predecessor_doc_id": null,
      "successor_doc_id": null
    },
    "cross_references": [
      {
        "type": "replaces",
        "target_document_id": "doc-...",
        "target_designation": "ГОСТ Р 12234-76"
      }
    ],
    "decision": "auto",
    "status": "completed"
  },
  "llm_usage": {
    "model": "gpt-4o-mini",
    "tokens_used": 2048,
    "processing_time_ms": 3200
  }
}
```

| Поле | Тип | Описание |
|---|---|---|
| `conversion_id` | string | ID конвертации |
| `document_id` | string | ID документа. Назначается при конвертации: извлекается существующий для дубликата, либо генерируется новый. |
| `hierarchy` | object | Построенная иерархическая структура документа |
| `metadata` | object | Извлечённые метаданные |
| `validation` | object | Результаты полной валидации (структура, классификация, уникальность, сопоставление, кросс-ссылки) |
| `llm_usage` | object | Статистика использования LLM (если `use_llm = true`) |

---

## Отдельные эндпоинты валидации (`/validate/*`)

Эндпоинты валидации могут вызываться как часть полного цикла `/converter/convert` (шаги 4–8), так и отдельно для проверки отдельных аспектов документа.

### POST /validate/document

Комплексная валидация документа.  
Принимает JSON-контейнер, выполняет все проверки (структура, классификация, уникальность, сопоставление).

**Запрос:**

```json
{
  "task_id": "task-8a3f2b",
  "version_id": "c4b9f2d3-...",
  "structure": {
    "type": "normative",
    "title": "ГОСТ Р 12345-77",
    "sections": [ ... ],
    "tables": [ ... ],
    "images": [ ... ]
  },
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null,
    "udk_code": "629.5.021",
    "year": "1981"
  },
  "quality": {
    "confidence": 0.94,
    "pages_processed": 12,
    "pages_failed": 0
  }
}
```

**Ответ `200`:**

```json
{
  "validation_id": "val-001",
  "document_id": "b3a8f1c2-...",
  "structure_valid": true,
  "classification": {
    "mks_oks_code": "47.020",
    "mks_status": "CONFIRMED",
    "okstu_status": "NOT_USED",
    "udk_code": "629.5.021",
    "overall_status": "CONFIRMED"
  },
  "uniqueness": {
    "is_duplicate_file": false,
    "is_duplicate_document": false,
    "content_hash_sha256": "abc123...",
    "title_hash_sha256": "def456..."
  },
  "matching": {
    "predecessor_doc_id": null,
    "successor_doc_id": null
  },
  "decision": "auto",
  "status": "completed"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `validation_id` | string | ID валидации |
| `document_id` | string | ID документа. Назначается валидацией: извлекается существующий для дубликата, либо генерируется новый. |
| `structure_valid` | bool | Результат проверки структуры |
| `classification` | object | Статусы классификационных кодов |
| `uniqueness` | object | Результаты проверки на дубликаты |
| `matching` | object | Связи с существующими документами |
| `decision` | string | `auto` — автоматическое продвижение, `review_required` — требуется ручное подтверждение |
| `status` | string | Статус: `completed`, `failed` |

---

### POST /validate/classifiers

Валидация классификационных кодов по справочнику Registry.

**Запрос:**

```json
{
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null,
    "udk_code": "629.5.021"
  }
}
```

**Ответ `200`:**

```json
{
  "mks_status": "CONFIRMED",
  "mks_display_name": "Конструкция корпуса",
  "okstu_status": "NOT_USED",
  "udk_valid": true,
  "overall_status": "CONFIRMED"
}
```

**Статусы:**

| Статус | Значение |
|---|---|
| `CONFIRMED` | Код найден в справочнике и верифицирован |
| `PENDING_REVIEW` | Код не найден в справочнике — требует ручного разбора |
| `NOT_FOUND` | Парсер не обнаружил код на первых страницах |
| `NOT_USED` | Не применяется для данной эры/типа документа |
| `UNASSIGNED` | Начальное состояние — классификация ещё не выполнялась |

---

### POST /validate/check

Проверка текста на соответствие набору правил.

**Запрос:**

```json
{
  "text": "Обшивка ледового пояса 10 мм",
  "rules": ["min_thickness_12mm"],
  "document_type": "drawing"
}
```

**Ответ `200`:**

```json
{
  "passed": false,
  "checks": [
    { "rule": "min_thickness_12mm", "status": "ERROR", "message": "Толщина 10 мм меньше требования 12 мм" }
  ],
  "processing_time_ms": 50
}
```

### POST /validate/extract/parameters

Извлечение структурированных параметров из документов.

**Запрос:**

```json
{
  "document_id": "doc-8a3f2b",
  "page_id": null,
  "document_type": "specification"
}
```

**Ответ `200`**: структура параметров (спецификация, материалы, размеры).

---

## Сводная информация

| Аспект | Значение |
|---|---|
| Доступ к БД | **Нет** (сервис не пишет и не читает БД напрямую; при необходимости данные передаются через Orchestrator) |
| LLM | Опционально (управляется параметром `use_llm`) |
| Режимы | Preview (быстрые проверки) + Full (полный цикл конвертации и валидации) |
| Пайплайн | 1 (Формирование документа), Этап 1.5 (Converter-validator) |
| Вход | Raw JSON (частичный — для Preview, полный — для Full) |
| Выход | Иерархический типизированный JSON с результатами валидации |

### Матрица эндпоинтов

| Метод | Путь | Режим | Описание | Запись в БД |
|---|---|---|---|---|
| `POST` | `/converter/preview/metadata` | Preview | Извлечение базовых метаданных | Нет |
| `POST` | `/converter/preview/uniqueness` | Preview | Проверка уникальности, поиск дубликатов | Нет |
| `POST` | `/converter/convert` | Full | Полная конвертация + валидация + LLM + кросс-ссылки | Нет |
| `POST` | `/validate/document` | Full / Standalone | Комплексная валидация документа | Нет |
| `POST` | `/validate/classifiers` | Full / Standalone | Валидация классификационных кодов | Нет |
| `POST` | `/validate/check` | Full / Standalone | Проверка правил | Нет |
| `POST` | `/validate/extract/parameters` | Full / Standalone | Извлечение параметров | Нет |
