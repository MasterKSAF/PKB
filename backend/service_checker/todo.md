# TODO: Разбор падения pipeline_test.py vs api_coverage_test.py

## Контекст
- `api_coverage_test.py` показывает 114/114 passed
- `pipeline_test.py` падает с ошибками БД (500) и валидации (422/401)
- Пользователь: "там идут ошибки с БД"

## Причины падения (установлено)

### 1. `api_coverage_test.py` — ложные positives (не "проходит корректно")
- В `_execute_endpoint` любой 4xx/5xx с JSON считается `success=True`
- Auth возвращает 401, Registry 307/422/500 — всё "✅ OK"
- `Context Variables: No context variables extracted` — prepare-шаги не создали данные
- Это НЕ означает, что сервисы работают. Это означает только "эндпоинт существует и отвечает JSON"

### 2. `document_processing` pipeline
- Шаг 5 (Converter): 422 — `task_id` передаётся как `int` (12345), сервис ожидает `string`
- Шаг 6 (Registry): 500 — `psycopg2.OperationalError: connection to server at "127.0.0.1", port 5432 failed: Connection refused`
- Шаг 7 (RAG Builder): 500 — та же БД-проблема
- Шаг 8 (RAG Search): 500 — `Database pool is not initialized`
- Проблема: сервисы в Docker настроены на `127.0.0.1:5432`, но внутри контейнера localhost — это сам контейнер

### 3. `registry_lifecycle` pipeline
- Шаг 1 (Auth): 401 — пользователя `petrova@example.com` нет в БД auth-сервиса
- Шаг 3 (Создать классификатор): 307 — путь без trailing slash, FastAPI делает redirect
- Шаг 5 (Получить классификатор): 422 — `{classifier_code}` не подставлен в путь
- Шаг 11 (Нормализация): 500 — БД-ошибка
- Шаг 12 (Обновить термин): 404 — `{term_id}` не подставлен

## План работ

1. **Анализ и документация**
   - [x] Запустить `api_coverage_test.py` с детальным выводом
   - [x] Запустить `pipeline_test.py` для всех pipeline
   - [x] Получить реальные тела ответов от сервисов
   - [x] Зафиксировать аномалии в `specificity.md`

2. **Исправления в `pipeline_test.py` / `pipelines`**
   - [x] `document_processing.py`: изменить `TEST_TASK_ID` на строку (`"12345"`)
   - [x] `document_processing.py`: добавить шаг аутентификации (Auth) перед Registry
   - [x] `registry_lifecycle.py`: добавить trailing slashes к путям Registry (кроме `/import`)
   - [x] `registry_lifecycle.py`: убрать trailing slashes у `/import` endpoints (иначе 307)
   - [x] `chat_inference.py`: auth-шаг использует те же credentials (проблема в БД, не в checker)

3. **Улучшения `api_coverage_test.py`**
   - [x] Добавить предупреждение, если prepare-шаги не извлекли контекст
   - [x] 500+ на не-health эндпоинтах теперь считается failed (не success)
   - [x] Добавить вывод реального тела ответа в отчёт для failed эндпоинтов (уже есть в pipeline)

4. **Тесты**
   - [x] Запустить `pipeline_test.py` после исправлений — converter теперь 200 (был 422)
   - [x] Запустить `api_coverage_test.py` после исправлений — теперь 5 failed (не 0)
   - [x] Убедиться, что unit-тесты проходят — 85/85 passed

5. **Актуализация `readme.md`**
   - [x] Обновить readme.md — document_processing 9 шагов, 5xx = fail

# ✅ Все задачи выполнены

## Итоговый статус сервисов

| Сервис | Статус | Примечание |
|--------|--------|-----------|
| Auth | ✅ 200 | admin@example.com / Admin1234! |
| Registry | ✅ 201 | БД работает, таблицы созданы |
| Converter | ✅ 200 | task_id как string |
| RAG Builder | ✅ 201 | UUID от конвертера |
| RAG Search | ❌ 500 | Без эмбеддингов (баг сервиса) |
| MinIO | ✅ 200 | S3 работает |
| Parser | ✅ 202 | парсинг работает |

## Результаты тестов

- **Unit-тесты:** 85/85 passed
- **Pipeline:** document_processing 7/9, registry_lifecycle 5/13, chat_inference 2/6
- **Coverage (честный):** 25/64 passed (раньше было 114/114 — ложные positives)

## Ключевые изменения

Подробно зафиксировано в `specificity.md` — аномалия №7
