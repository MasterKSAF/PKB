# Рефакторинг: вынос описаний сервисов в отдельные файлы + подготовка данных

## Задача
На основании описания API реализовать опрос API с заполненными данными и получением готового ответа, учитывая предварительную подготовку.
- Для registry: сначала вносить документ перед загрузкой, вносить классификаторы перед проверкой и т.д.
- Распределить работу с сервисами по отдельным файлам (т.к. данных будет больше)

## Что сделано ✅

### 1. Создан пакет `service_checker/services/`
Каждый сервис — отдельный файл с полным описанием эндпоинтов и prepare-шагами.

```
services/
├── __init__.py              # Реестр SERVICE_REGISTRY + MODE_PORTS
├── base.py                  # ServiceDef, EndpointDef, константы
├── auth.py                  # Auth Service (16 endpoints + 2 prepare)
├── registry.py              # Registry Service (32 endpoints + 3 prepare)
├── orchestrator.py          # Orchestrator Service (23 endpoints + 1 prepare)
├── query.py                 # Query Service (18 endpoints + 2 prepare)
├── parser.py                # Parser Service (5 endpoints + 1 prepare)
├── ocr.py                   # OCR Service (5 endpoints + 1 prepare)
├── converter_validator.py   # Converter-Validator (4 endpoints)
├── rag_builder.py           # RAG Builder (4 endpoints + 1 prepare)
├── rag_search.py            # RAG Search (2 endpoints)
├── tei.py                   # TEI Embeddings (2 endpoints)
└── gateway.py               # Gateway (агрегирует auth+orchestrator+query+registry)
```

### 2. Data-класс ServiceDef
Добавлен в `base.py`:
- `service_key`, `display_name`, `port`
- `needs_auth`, `depends_on`, `base_data`
- `endpoints` — основные эндпоинты
- `prepare_endpoints` — эндпоинты подготовки данных

### 3. Prepare-эндпоинты
Для каждого сервиса добавлены prepare-шаги:
- **auth**: POST /auth/token → access_token, GET /auth/me
- **registry**: POST /classifiers → classifier_code, POST /documents → doc_id, POST /terminology → term_id
- **query**: POST /chat/sessions → session_id, POST /messages → message_id
- **orchestrator**: POST /documents → task_id
- **parser**: POST /parser/process → task_id
- **ocr**: POST /ocr/process → task_id
- **rag_builder**: POST /rag/build
- **gateway**: наследует prepare от auth + orchestrator + query + registry

### 4. Рефакторинг `api_coverage_test.py`
- Заменён `build_endpoints()` на `SERVICE_REGISTRY` из `services/`
- Добавлен `_execute_endpoint()` — выделенная логика выполнения одного эндпоинта
- Prepare-эндпоинты выполняются перед основными, заполняют контекст
- Добавлен флаг `--skip-prepare` для пропуска prepare-шагов
- Сохранена совместимость формата отчёта
- Тесты обновлены (`tester.endpoints` → `tester._test_endpoints`)

### 5. Проверка
- ✅ **83/84 тестов пройдено** (1 интеграционный — требует Docker)
- ✅ `python -c "from services.base import *"` — импорт работает
- ✅ `python -c "from services import SERVICE_REGISTRY"` — все сервисы загружаются
- ✅ `python api_coverage_test.py --ping-only` — ping работает
- ✅ `python api_coverage_test.py --skip-prepare` — пропуск prepare
