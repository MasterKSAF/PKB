## API Validation Service (validation-service:8086)

Сервис сопоставления норм и проекта, проверки правил и арифметических вычислений.  
**Внутренний сервис.** Вызывается Orchestrator для бизнес-валидации проектных решений.

**Базовый URL (внутренний)**: `http://127.0.0.1:8086/api/v1`

### Формат ответа

Успех — данные возвращаются напрямую.  
При ошибке: `{ "error": { "code": "VALIDATION_FAILED", "message": "...", "details": {} } }`

### POST /validate/extract/parameters

Извлечение структурированных параметров из документов.

**Запрос**:
```json
{
  "document_id": "doc-8a3f2b",
  "page_id": null,
  "document_type": "specification"
}
```

**Ответ `200`**: структура параметров (спецификация, материалы, размеры).

### POST /validate/check

Проверка текста на соответствие набору правил.

**Запрос**:
```json
{
  "text": "Обшивка ледового пояса 10 мм",
  "rules": ["min_thickness_12mm"],
  "document_type": "drawing"
}
```

**Ответ `200`**:
```json
{
  "passed": false,
  "checks": [
    { "rule": "min_thickness_12mm", "status": "ERROR", "message": "Толщина 10 мм меньше требования 12 мм" }
  ],
  "processing_time_ms": 50
}
```

### POST /validate/calculate

Арифметический движок для вычислений.

**Запрос**:
```json
{
  "expression": "(1200 + 2*10) / 2",
  "context": { "переменная": "10" },
  "document_type": "drawing"
}
```

**Ответ `200`**:
```json
{
  "expression": "(1200 + 2*10) / 2",
  "result": 610,
  "unit": "мм",
  "steps": ["1200 + 20 = 1220", "1220 / 2 = 610"]
}
```

### POST /validate/recommend

Рекомендации по исправлению ошибок проверки.

**Запрос**:
```json
{
  "failures": [{ "rule": "min_thickness_12mm", "status": "fail" }],
  "document_type": "drawing"
}
```

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

### POST /validate/compare

Сопоставление нормы и проектных данных (асинхронное).

**Запрос** (по тексту):
```json
{
  "normative_text": "Толщина обшивки ледового пояса ≥ 12 мм",
  "project_text": "Обшивка ледового пояса 14 мм",
  "document_type": "drawing"
}
```

**Ответ `202`**:
```json
{
  "comparison_id": "cmp-007",
  "status": "processing",
  "created_at": "2026-05-15T12:00:00Z"
}
```

### GET /validate/compare/{comparison_id}

Результат сопоставления. Опрос до статуса `completed` / `failed`.

**Ответ `200`**:
```json
{
  "comparison_id": "cmp-007",
  "status": "completed",
  "match_status": "match",
  "summary": "Толщина 14 мм соответствует требованию ≥12 мм",
  "processing_time_ms": 3200
}
```

**Статусы `match_status`**: `match`, `possible_discrepancy`, `not_found_in_project`, `not_found_in_norm`, `insufficient_data`.

### POST /validate/compare/batch

Массовое сопоставление пар фрагментов.

**Запрос**:
```json
{
  "pairs": [
    { "normative_chunk_id": "frg-42", "project_chunk_id": "frg-5" }
  ]
}
```

**Ответ `200`**:
```json
{
  "batch_id": "batch-001",
  "comparisons": [
    { "comparison_id": "cmp-007", "match_status": "match", "summary": "..." }
  ],
  "total_pairs": 1,
  "matched": 1,
  "discrepancies_found": 0
}
```
