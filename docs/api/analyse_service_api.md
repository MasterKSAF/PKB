## API Analyse Service (analyse-service:8089)

Сервис анализа проектных решений на соответствие нормам и стандартам.  
Выполняет длительные операции сопоставления данных из спецификаций, ГОСТов и расчётов.

**Внутренний сервис.** Вызывается Orchestrator для операций анализа.

**Базовый URL (внутренний)**: `http://127.0.0.1:8089/api/v1`

### Формат ответа

Успех — данные возвращаются напрямую.
При ошибке: `{ "error": { "code": "ANALYSIS_FAILED", "message": "...", "details": {} } }`

> Полный формат ответа и ошибок — см. [common_api.md](../common_api.md#формат-ответа).

### Группы

| Группа | Описание |
|--------|----------|
| `compare` | Сопоставление норм и проектных данных |
| `calculate` | Арифметический движок для вычислений |
| `recommend` | Рекомендации по исправлению ошибок |

---

### POST /analyse/compare

Сопоставление нормы и проектных данных (асинхронное).

Идентификатор сравнения (`comparison_id`) генерируется Оркестратором и передаётся в запросе.

**Запрос:**

```json
{
  "comparison_id": "cmp-007",
  "normative_query": "Толщина обшивки ледового пояса ≥ 12 мм",
  "project_document_id": "doc-proj-001",
  "document_type": "drawing"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `comparison_id` | string | Да | Идентификатор сравнения (генерируется Оркестратором) |
| `normative_query` | string | Да | Нормативный запрос |
| `project_document_id` | string | Да | ID проектного документа |
| `document_type` | string | Нет | Категория контента (`normative`, `technical`, `drawing`, `specification`, `archival_scan`) |

**Ответ `202`:**

```json
{
  "comparison_id": "cmp-007",
  "status": "processing",
  "created_at": "2026-05-15T12:00:00Z"
}
```

---

### GET /analyse/compare/{comparison_id}

Результат сопоставления. При статусе `processing` Оркестратор ожидает завершения через longpoll.

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
| -------- | --- | ------------ | -------- |
| `longpoll` | int | `15` | Время ожидания в секундах. Сервер держит соединение, возвращая ответ при завершении сравнения или по таймауту. |

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

### POST /analyse/compare/batch

Массовое сопоставление пар фрагментов.

**Запрос:**

```json
{
  "pairs": [
    { "normative_chunk_id": 420042, "project_chunk_id": 420005 }
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

### POST /analyse/calculate

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

---

### POST /analyse/recommend

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

## Сводная информация

| Аспект | Значение |
|---|---|
| Доступ к БД | **Читает** (документы, классификаторы) |
| Пайплайн | Независимый (пост-обработка, анализ) |
| Вход | JSON с запросом на анализ |
| Выход | JSON с результатами анализа |

### Матрица эндпоинтов

| Метод | Путь | Описание | Доступ к БД |
|---|---|---|---|
| `POST` | `/analyse/compare` | Сопоставление норм и проектов | **Читает** |
| `POST` | `/analyse/compare/batch` | Пакетное сравнение | **Читает** |
| `GET` | `/analyse/compare/{comparison_id}` | Результат сравнения | **Читает** |
| `POST` | `/analyse/calculate` | Вычисления | Нет |
| `POST` | `/analyse/recommend` | Рекомендации | **Читает** |
