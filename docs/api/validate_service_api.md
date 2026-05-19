## API Validation Service / Валидация (validation-service:8086)

Сервис комплексной валидации документов.  
Соответствует этапу **«Валидация» Пайплайна 1 (Формирование документа)** — **читает** базу данных для проверки уникальности, классификации и сопоставления.

**Внутренний сервис.** Вызывается Orchestrator для валидации JSON-контейнера после этапа Парсинга.

**Базовый URL (внутренний)**: `http://127.0.0.1:8086/api/v1`

### Формат ответа

Успех — данные возвращаются напрямую.  
При ошибке: `{ "error": { "code": "VALIDATION_FAILED", "message": "...", "details": {} } }`

---

### POST /validate/document

Комплексная валидация документа. Основной эндпоинт этапа «Валидация».  
Принимает JSON-контейнер от этапа Парсинга, выполняет все проверки.

**Процесс внутри:**

| Шаг | Действие | Доступ к БД |
|---|---|---|
| 1 | Валидация структуры JSON | Нет |
| 2 | Классификация документа (тип, эра, юрисдикция) | Нет |
| 3 | Проверка уникальности (SHA-256, title_hash) | **Читает** |
| 4 | Сопоставление с существующими документами (predecessor/successor) | **Читает** |
| 5 | Валидация классификационных кодов (через Registry) | **Читает** |

**Запрос:**

```json
{
  "document_id": "b3a8f1c2-...",
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

---

### POST /validate/compare

Сопоставление нормы и проектных данных (асинхронное).

**Запрос:**

```json
{
  "normative_query": "Толщина обшивки ледового пояса ≥ 12 мм",
  "project_document_id": "doc-proj-001",
  "document_type": "drawing"
}
```

**Ответ `202`:**

```json
{
  "comparison_id": "cmp-007",
  "status": "processing",
  "created_at": "2026-05-15T12:00:00Z"
}
```

### GET /validate/compare/{comparison_id}

Результат сопоставления.

**Ответ `200`:**

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

---

### POST /validate/compare/batch

Массовое сопоставление пар фрагментов.

**Запрос:**

```json
{
  "pairs": [
    { "normative_chunk_id": "frg-42", "project_chunk_id": "frg-5" }
  ]
}
```

**Ответ `200`:**

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

### POST /validate/calculate

Арифметический движок для вычислений.

**Запрос:**

```json
{
  "expression": "(1200 + 2*10) / 2",
  "context": { "переменная": "10" },
  "document_type": "drawing"
}
```

**Ответ `200`:**

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

**Запрос:**

```json
{
  "failures": [{ "rule": "min_thickness_12mm", "status": "fail" }],
  "document_type": "drawing"
}
```

**Ответ `200`:**

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

---

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
| Доступ к БД | **Читает** (классификаторы, документы для проверки уникальности) |
| Пайплайн | 1 (Формирование документа), Этап 2 |
| Вход | JSON-контейнер от этапа Парсинга |
| Выход | JSON с решением (auto / review_required) |

### Матрица эндпоинтов

| Метод | Путь | Описание | Доступ к БД |
|---|---|---|---|
| `POST` | `/validate/document` | Комплексная валидация документа | **Читает** |
| `POST` | `/validate/classifiers` | Валидация классификационных кодов | **Читает** |
| `POST` | `/validate/compare` | Сопоставление норм и проектов | **Читает** |
| `POST` | `/validate/compare/batch` | Пакетное сравнение | **Читает** |
| `GET` | `/validate/compare/{comparison_id}` | Результат сравнения | **Читает** |
| `POST` | `/validate/check` | Проверка правил | Нет |
| `POST` | `/validate/calculate` | Вычисления | Нет |
| `POST` | `/validate/recommend` | Рекомендации | **Читает** |
| `POST` | `/validate/extract/parameters` | Извлечение параметров | **Читает** |
