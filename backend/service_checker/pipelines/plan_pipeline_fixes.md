# План: синхронизация pipeline-шагов со спецификацией 19.06.2026

**Дата:** 20.06.2026
**Проблема:** Pipeline-шаги используют старые форматы запросов (без новых полей из задач 19.06). API Coverage Test обновлён — показывает failures. Pipeline проходит, потому что шлёт старые тела.

---

## 1. `pipelines/document_processing.py` (Parser → Converter → Registry → RAG)

### 1.1 Шаг «Запуск парсинга» (строка 139)
```python
# СЕЙЧАС — нет draft_id
body = {"task_id": ..., "file_key": ..., "version_id": "1", "mode": "full"}

# НАДО — добавить draft_id (PS-3)
body = {"task_id": ..., "draft_id": 1, "file_key": ..., "version_id": "1", "mode": "full"}
```

### 1.2 Шаг «Конвертация JSON» (строка 223)
```python
# СЕЙЧАС — body без version_id
body = {"task_id": str(...), "raw_json": {...}}

# НАДО — добавить version_id (CV-9 убирает из ответа, не из запроса)
body = {"task_id": str(...), "version_id": "1", "raw_json": {...}}
```

### 1.3 Шаг «Сохранение документа в Registry» (строка 238)
```python
# СЕЙЧАС — без source_draft_id, без mks_oks_code/okstu_code
body = {"title": ..., "doc_code": ..., "source_type": ..., "era": ..., "validity_status": ...}

# НАДО — добавить source_draft_id (RG-9), mks_oks_code (DB-9), title_key (DB-28)
body = {"title": ..., "doc_code": ..., "source_type": ..., "era": ...,
        "validity_status": ..., "source_draft_id": 1,
        "mks_oks_code": "47.020", "title_key": "GOST|RF|...|2026"}
```

---

## 2. `pipelines/chat_inference.py` (Auth → Query → RAG Search)

### 2.1 Шаг «Создание чат-сессии» (строка 61)
```python
# СЕЙЧАС — без document_ids, project_id
body = {"title": f"Pipeline тестовая сессия ..."}

# НАДО — добавить document_ids и project_id (QS-3)
body = {"title": ..., "document_ids": [], "project_id": 1}
```

### 2.2 Шаг «Проверка enrichment_skipped» (строка 103)
```python
# СЕЙЧАС — жёсткая проверка, падает если поле не реализовано (QS-8)
check = check_json_field("enrichment_skipped", bool)

# НАДО — сделать skip_if для случая, когда сервис не обновлён
# Добавить on_error или изменить check на tolerant
```
**Вариант:** заменить `check` на мягкую проверку: если поле есть — проверить тип, если нет — warning, не error.

### 2.3 Шаг «Текстовый поиск» (строка 92)
```python
# СЕЙЧАС — тело с top_k (уже не критично, но для консистентности убрать)
body = {"text": ..., "valid_at": ..., "top_k": 5, "filters": ...}
```

---

## 3. `pipelines/orchestrator_draft_lifecycle.py` (Auth → Orchestrator)

### 3.1 Шаг «Создание черновика» (строка 80)
```python
# СЕЙЧАС — form_body без source_draft_id
form_body = {"document_key": ..., "title": ...}

# Проверить: OR-11 требует source_draft_id? Да, RG-9 — source_draft_id опционален.
# Оставить как есть (source_draft_id не обязателен при создании).
```

### 3.2 Шаг «Детали черновика» (строка 112)
```python
# СЕЙЧАС — проверяет только draft_id
check = check_json_field("draft_id", int)

# НАДО — проверить document_id, version_id, is_new_document (OR-7)
check = check_json_fields({"draft_id": int, "document_id": (int, type(None)),
                           "version_id": (int, type(None)), "is_new_document": bool})
```

### 3.3 Шаг «Статус задачи» (строка 100)
```python
# СЕЙЧАС — статус задачи
# OR-1 требует GET /tasks/{task_id}/status — уже есть.
# Добавить expected_status=404? Нет, статус задачи должен быть 200 если задача есть.
```

---

## 4. `pipelines/full_document_lifecycle.py` (Auth → Registry → RAG)

### 4.1 Шаг «Создание документа в Registry» (строка 88)
```python
# СЕЙЧАС — без source_draft_id
body = {"title": ..., "doc_code": ..., "source_type": ..., "era": ..., "validity_status": ...}

# НАДО — добавить source_draft_id, mks_oks_code, title_key (как в п.1.3)
```

### 4.2 Шаги «Первая/повторная/финальная индексация» (строки 101, 141, 241)
```python
# СЕЙЧАС — ожидает 200/201
expected_status = {200, 201}

# НАДО — ожидать 200/202 (RB-7: 201 → 202 для асинхронного запуска)
expected_status = {200, 202}
```

### 4.3 Шаг «Обновление метаданных документа» (строка 131)
```python
# СЕЙЧАС — PATCH /registry/documents/{doc_id}/status/ с trailing slash
# RG-1: PATCH /registry/documents/{id}/status — internal-эндпоинт
# Путь корректный, но body должно быть {"processing_status": "uploaded"}, а не {"status": "uploaded"}
```
**Проверить:** поле в БД называется `processing_status`, не `status`.

---

## 5. `pipelines/admin_user_lifecycle.py` (Auth → Query)

### 5.1 Шаг «Создание чат-сессии» (строка 130)
```python
# СЕЙЧАС — без document_ids, project_id
body = {"title": f"User pipeline сессия ..."}

# НАДО — добавить document_ids и project_id (QS-3)
body = {"title": ..., "document_ids": [], "project_id": 1}
```

### 5.2 Шаг «Проверка блокировки после 5 неудач» (строка 190)
```python
# СЕЙЧАС — ожидает {429, 423}, но сервис возвращает 401 (AU-3 не реализован)
expected_status = {429, 423}

# НАДО — добавить 401 как допустимый (сервис может не иметь брутфорс-защиты)
expected_status = {401, 429, 423}
```
Или добавить `skip_if`, чтобы пропускать проверку, если сервис не обновлён.

---

## 6. `pipelines/multi_document_cross_search.py` (Auth → MinIO → Parser → Converter → Registry → RAG)

### 6.1 Шаги «Запуск парсинга #1/#2» (строки 117, 239)
```python
# СЕЙЧАС — нет draft_id
body = {"task_id": ..., "file_key": ..., "version_id": "1", "mode": "full"}

# НАДО — добавить draft_id (PS-3)
body = {"task_id": ..., "draft_id": 1, "file_key": ..., "version_id": "1", "mode": "full"}
```

### 6.2 Шаги «Конвертация JSON #1/#2» (строки 160, 280)
```python
# СЕЙЧАС — body без version_id
body = {"task_id": str(...), "raw_json": {...}}

# НАДО — добавить version_id
body = {"task_id": str(...), "version_id": "1", "raw_json": {...}}
```

### 6.3 Шаги «Сохранение документа в Registry #1/#2» (строки 174, 293)
```python
# СЕЙЧАС — без source_draft_id
body = {"title": ..., "doc_code": ..., "source_type": ..., "era": ..., "validity_status": ...}

# НАДО — добавить source_draft_id, mks_oks_code, title_key
```

### 6.4 Шаги «Построение индекса #1/#2» (строки 193, 312)
```python
# СЕЙЧАС — ожидает 200/201
expected_status = {200, 201}

# НАДО — ожидать 200/202 (RB-7)
expected_status = {200, 202}
```

---

## 7. Общие замечания

### 7.1 `version_id` в парсинге
Все pipeline-шаги парсинга передают `"version_id": "1"`. PS/OC задачи не отменяли `version_id` — его оставить. Проверить только, что он строковый, как ожидает сервис.

### 7.2 `draft_id` — обязательное поле
PS-3 и OC-4 требуют обязательный `draft_id`. Во все шаги `POST /parser/process` и `POST /ocr/process` добавить `"draft_id": 1`. Если сервис не реализовал — шаг упадёт с 422. Это **правильное поведение**: pipeline должен честно показать, что сервис не обновлён.

### 7.3 RB-7: 201 → 202
RAG Builder build должен возвращать 202 (асинхронный запуск). Два pipeline используют `{200, 201}`. Заменить на `{200, 202}`. Если сервис вернёт 201 — шаг упадёт. Это покажет, что сервис не обновлён.

### 7.4 Толерантность к необновлённым сервисам
Некоторые проверки (enrichment_skipped, brute-force lock, preview_snapshot) должны использовать `skip_if` или tolerant check, потому что сервисы могут быть не обновлены. Это уже частично реализовано через `skip_if` в `orchestrator_draft_lifecycle.py`.

---

## Приоритеты

| # | Файл | Изменение | P-задача | Приоритет |
|---|------|-----------|----------|-----------|
| 1 | document_processing, multi_doc | `draft_id` в парсинг | PS-3/OC-4 | 🔴 |
| 2 | chat_inference, admin_user | `document_ids`, `project_id` в сессию | QS-3 | 🔴 |
| 3 | full_doc_lifecycle, multi_doc | `expected_status` 200/201 → 200/202 | RB-7 | 🟠 |
| 4 | document_processing, multi_doc | `source_draft_id`, `mks_oks_code` в Registry | RG-9, DB-9 | 🟠 |
| 5 | document_processing, multi_doc | `version_id` в converter | CV-9 | 🟡 |
| 6 | admin_user_lifecycle | 401 в brute-force check | AU-3 | 🟡 |
| 7 | chat_inference | tolerant enrichment_skipped check | QS-8 | 🟡 |
| 8 | orchestrator_draft_lifecycle | OR-7 поля в деталях черновика | OR-7 | 🟡 |
