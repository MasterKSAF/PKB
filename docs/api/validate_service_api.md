## API Validation Service (validation-service:8082)

Сервис валидации, извлечения параметров и сопоставления.

*Внутренний сервис. Не предназначен для прямого вызова из frontend. Публичный API — в Orchestrator Service.*

Базовый путь: `/api/v1`

### Группы

| Группа | Описание |
|--------|----------|
| `extract` | Извлечение параметров из документов |
| `check` | Проверка текста по правилам |
| `compare` | Сопоставление нормы и проектных данных |
| `calculate` | Арифметический движок |
| `recommend` | Рекомендации по исправлению |

### POST /extract/parameters

Извлечение структурированных параметров из документов.

**Запрос**:

```json
{
  "document_id": "doc-8a3f2b",
  "page_id": null,
  "document_type": "specification"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `document_id` | string | Да | ID документа |
| `page_id` | string | Нет | ID страницы (опционально) |
| `document_type` | string | Да | Тип документов |

**Ответ `200`**: Структура параметров (см. `GET /documents/{doc_id}/parameters`) + `processing_time_ms`.

### POST /check

Выполнение заданного набора проверок над текстом.

**Запрос**:

```json
{
  "text": "Обшивка ледового пояса 10 мм",
  "rules": ["min_thickness_12mm"],
  "document_type": "drawing"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `text` | string | Да | Текст для проверки |
| `rules` | string[] | Да | Список правил |
| `document_type` | string | Да | Тип документов |

**Ответ `200`**:

```json
{
  "passed": false,
  "checks": [
    {
      "rule": "min_thickness_12mm",
      "status": "fail",
      "message": "Толщина 10 мм меньше требования 12 мм",
      "details": "..."
    }
  ],
  "processing_time_ms": 50
}
```

### POST /calculate

Арифметический движок для вычислений.

**Запрос**:

```json
{
  "expression": "(1200 + 2*10) / 2",
  "context": {"переменная": 10}
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `expression` | string | Да | Математическое выражение |
| `context` | object | Нет | Переменные для подстановки |

**Ответ `200`**:

```json
{
  "expression": "(1200 + 2*10) / 2",
  "result": 610,
  "unit": "мм",
  "steps": ["1200 + 20 = 1220", "1220 / 2 = 610"]
}
```

### POST /recommend

Рекомендации по исправлению ошибок проверки.

**Запрос**:

```json
{
  "failures": [
    {"rule": "min_thickness_12mm", "status": "fail"}
  ],
  "document_type": "drawing"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `failures` | array | Да | Список ошибок |
| `document_type` | string | Да | Тип документов |

**Ответ `200`**:

```json
{
  "recommendations": [
    {
      "failure_ref": "min_thickness_12mm",
      "recommendation_text": "Увеличить толщину обшивки до 12 мм согласно Правилам РС, часть I, стр.42.",
      "severity": "critical",
      "reference_document": "doc-norm-001"
    }
  ]
}
```

### POST /compare

Сопоставление нормы и проектных данных (одиночное).

**Запрос**:

```json
{
  "normative_text": "Толщина обшивки ледового пояса ≥ 12 мм",
  "project_text": "Обшивка ледового пояса 14 мм",
  "document_type": "drawing"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `normative_text` | string | Да | Текст нормативного требования |
| `project_text` | string | Да | Текст проектного параметра |
| `document_type` | string | Да | Тип документов |

**Ответ `200`**: Объект сопоставления + `comparison_id`.

### GET /compare/{comparison_id}

Получение ранее созданного сопоставления.

**Ответ `200`**: Объект сопоставления.

### POST /compare/batch

Массовое сопоставление пар фрагментов.

**Запрос**:

```json
{
  "pairs": [
    {"normative_chunk_id": "frg-42", "project_chunk_id": "frg-5"}
  ]
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `pairs` | array | Да | Пары для сопоставления |
| `pairs[].normative_chunk_id` | string | Да | ID фрагмента нормы |
| `pairs[].project_chunk_id` | string | Да | ID фрагмента проекта |

**Ответ `200`**:

```json
{
  "batch_id": "batch-001",
  "comparisons": [
    {
      "comparison_id": "cmp-007",
      "match_status": "match",
      "summary": "Толщина 14 мм соответствует требованию ≥12 мм"
    }
  ],
  "total_pairs": 1,
  "matched": 1,
  "discrepancies_found": 0,
  "insufficient_data": 0
}