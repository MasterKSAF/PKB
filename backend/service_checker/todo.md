# TODO: Валидация данных через openapi.json и сверка с документацией

## Изученная архитектура

### Текущее состояние
- **`services/*.py`** — вручную прописанные `response_schema` (Dict[str, type]), неполные, упрощённые
- **`docs/api/*.md`** — подробная документация с примерами JSON и таблицами полей (14 файлов)
- **`core/api_coverage_test.py::_validate_response()`** — проверяет ответ только по ручной схеме
- **Real-сервисы (FastAPI)** — имеют `/openapi.json` (кроме gateway-mock и TEI)

### Задача пользователя
1. Сверять openapi.json реальных сервисов с документацией `docs/api/*.md`
2. Для этого нужно из md-документации генерировать схему в формате, сопоставимом с OpenAPI

---

## План реализации

### Блок 1: Парсер markdown-документации → структура эндпоинтов (core/md_parser.py)
- [x] Создать парсер `docs/api/*.md`
  - Извлекает по каждому эндпоинту: method, path, group, описание
  - Парсит примеры JSON-ответов (```json блоки) и строит JSON Schema
  - Парсит таблицы полей (имя, тип, обязательность, описание)
  - Строит древовидную схему ответа из примеров + таблиц
- [x] Покрыть тестами на 14 md-файлах (40 тестов)
- [x] Встроенная конвертация в OpenAPI 3.0.3 (MdApiParser.to_openapi)

### Блок 2: Загрузчик OpenAPI-схем от сервисов (core/openapi_loader.py)
- [x] Загружает `/openapi.json` с сервиса по URL
- [x] Разрешает `$ref` (локальные ссылки)
- [x] Извлекает schema для каждого эндпоинта по method + path
- [x] Строит плоскую карту полей для сравнения
- [x] Match эндпоинтов с path parameters
- [x] Исключения: gateway-mock, TEI (нет /openapi.json)

### Блок 3: Генератор схемы из md (встроен в md_parser.py как to_openapi)
- [x] Преобразует распарсенную md-документацию в OpenAPI 3.0.3
- [x] Формат: paths → {method} → parameters, requestBody, responses

### Блок 4: Компаратор схем (core/schema_comparator.py)
- [x] Сравнивает OpenAPI-схему сервиса со сгенерированной из md
- [x] Выявляет расхождения: missing_in_md, missing_in_oapi, type_mismatches, required_mismatches
- [x] Сравнивает query-параметры
- [x] format_diff() — читаемый отчёт
- [x] summarize_diff() — сводная статистика

### Блок 5: Интеграция в coverage test (api_coverage_test.py)
- [x] Флаг `--schema-check` — загружает OpenAPI-схемы и валидирует ответы
- [x] Флаг `--strict` — fail при любом расхождении с OpenAPI
- [x] `_validate_against_openapi()` — сверяет ответ с OpenAPI-схемой
- [x] `_flatten_response()` — преобразует JSON-ответ в плоскую карту полей
- [x] `load_openapi_schemas()` — загружает схемы для всех сервисов
- [x] Предупреждения о расхождениях в warnings эндпоинта

### Блок 6: Ограничения и исключения
- [x] Gateway (mock) и TEI — нет `/openapi.json`, остаётся ручная `response_schema`
- [x] Не валидировать prepare-шаги (они создают данные, а не возвращают)
- [ ] Converter и Parser health на `/health` — их OpenAPI может отличаться от ожиданий
- [ ] RAG Builder / RAG Search могут иметь неполные схемы

---

## Результат
- ✅ Парсер md-документации — 14 файлов, ~160 эндпоинтов, 40 тестов
- ✅ Загрузчик OpenAPI-схем с `$ref` resolution
- ✅ Компаратор схем (md vs openapi)
- ✅ Интеграция в coverage test (--schema-check, --strict)
- ✅ Все тесты: 210/210
- ❓ Остаётся: полный цикл md→OpenAPI→сравнение в отдельном CLI

---

## Текущее: Обновление warnings после прямой проверки API

### Блок 1: Parser Service
- [x] Исправить health endpoint: `GET /health` → `GET /api/v1/health` (сейчас падает 404)
- [x] Убрать все 3 устаревших warnings

### Блок 2: RAG Builder
- [x] Убрать warning про JWT (RAG Builder не проверяет токен)
- [x] Проверено: health на /api/v1/health — уже корректный в checker

### Блок 3: Converter-Validator
- [x] Уточнить warning про task_id/version_id — сервис принимает и int, и str
- [x] Уточнить warning про document_id/validation_id — возвращает val-xxxx (string), не UUID

### Блок 4: Проверка
- [x] Запустить coverage тест — проверить что Parser health проходит
- [x] Запустить full report — проверить что warnings обновились

### Итог:
- **Parser**: health исправлен (5/5 ✅), 3 warnings убраны
- **RAG Builder**: warning про JWT убран (сервис не проверяет токен)
- **Converter**: warning уточнены (int/str, val-xxxx)
- **Full report**: 10/10 ✅, "Нет замечаний"
