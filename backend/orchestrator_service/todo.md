# Todo — Общее решение валидации данных на границах сервисов — ВЫПОЛНЕНО

## Задача
Данные передаются между слоями (endpoint → client → mock/HTTP) без валидации типов.
Pydantic-аннотации не работают в runtime — ошибки типа `created_by: CurrentUser` вместо `str` не отлавливаются.

## Что сделано

### 1. JSON serialization guard в `base_client.call()` ✅
- **Файл:** `app/services/base_client.py`
- `json.dumps()` проверка для всех `json` kwargs — защита для ВСЕХ 5 клиентов
- Срабатывает ДО ветвления mock/real — ошибка не уходит никуда

### 2. Pydantic request_model в `base_client.call()` ✅
- Опциональный параметр `request_model: Type[BaseModel]`
- `model_validate()` → `model_dump()` — структурная валидация до отправки
- Ошибка: `TypeError("... Pydantic validation: ...")`

### 3. Pydantic request schemas для всех клиентов ✅
**Новый файл:** `app/schemas/requests.py` — 8 схем:

| Схема | Клиент | Метод |
|-------|--------|-------|
| `CreateDraftRequest` | Registry | `create_draft` |
| `UpdateDraftStatusRequest` | Registry | `update_draft_status` |
| `CheckUniquenessRequest` | Registry | `check_uniqueness` |
| `OcrProcessRequest` | OCR | `process_document` |
| `ParserPreviewRequest` | Parser | `process_preview` |
| `ParserProcessRequest` | Parser | `process_full` |
| `RagIndexRequest` | RAG | `index_document` |
| `RagSearchRequest` | RAG | `search` |
| `RagGenerateRequest` | RAG | `generate` |

Converter — generic `data: dict`, защищён JSON guard-ом.

### 4. Тесты ✅
- **Новые:** `TestServiceClientDataValidation` (4 теста) — guard + request_model
- **Все тесты:** 353 passed (13s)

### 5. Зафиксировано в specificity.md ✅
- **П. 1.5** — архитектурное решение: валидация на границе service client
- **П. 3.9** — аномалия `created_by` и её исправление
