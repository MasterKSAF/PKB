# PKB Neuroassistant — Service Checker

## Назначение

**`service_checker` — диагностический инструмент для проверки работоспособности микросервисов PKB Neuroassistant, работающих в Docker.** Он не является production-сервисом, а используется для локальной разработки, отладки и интеграционного тестирования.

🔹 **Ключевая идея:** «проверка сервисов» означает **запуск всех микросервисов** и **анализ результатов их работы**. Это не статический анализ кода, а полноценный прогон системы в Docker-окружении с вызовом реальных API и генерацией сводного отчёта.

Что происходит при проверке:

| Этап | Действие |
|------|----------|
| **Docker Compose up** | Запуск инфраструктуры: PostgreSQL, Redis, MinIO, TEI, 10 Python-сервисов под supervisord |
| **Health Check** | Проверка `/health` каждого сервиса — жив ли, отвечает ли |
| **API Coverage** | Вызов **каждого эндпоинта** из API-документации (~150 шт.) — проверка HTTP-статуса и JSON-схемы |
| **Pipeline Testing** | Сквозные сценарии: загрузка → парсинг → индексация → поиск, чат-сессия, CRUD классификаторов |
| **Сбор логов** | Чтение supervisor-логов каждого сервиса, поиск ошибок |
| **Генерация отчёта** | Сводная таблица по всем сервисам (Markdown / HTML) |

> 🔹 **Важно:** service_checker НЕ вмешивается в работу других сервисов. Его задача — только запустить их, проверить состояние, выполнить тестовые API-вызовы и сформировать отчёт. Любые изменения конфигурации, данных или кода сервисов ЗАПРЕЩЕНЫ.

---

## Состав модулей

### 1. `service_checker.py` — Запуск / Health Check / Эмуляция UI

Главный CLI-инструмент. Умеет:

- **Запускать mock- и real-сервисы** — стартует uvicorn-процессы для сервисов из `SERVICE_DEFS`
- **Health check** — проверяет /health каждого сервиса (GET), выводит сводку
- **Эмуляция UI** — выполняет сценарии, имитирующие работу фронтенда (auth, classifiers, terminology, documents, upload, search, chat, monitor, system_health)
- **Docker-режим** — управление Docker Compose (up/down/build/restart/reset/logs/health/coverage)
- **Генерация отчёта** (Markdown / HTML) — логи, health check, API-вызовы, ошибки

> 🔹 **Особенность:** два режима запуска сервисов — **локальный** (через subprocess.Popen на хосте) и **Docker** (через docker compose). Локальный режим использует моки из gateway_service. Docker — реальные сервисы под supervisord.

**Ключевые компоненты:**

| Компонент | Назначение |
|-----------|------------|
| `ServiceProcess` | Запущенный процесс сервиса (pid, port, health_url) |
| `HealthResult` | Результат health check (ok, degraded, error, unreachable) |
| `ApiCallLog` | Лог одного API-вызова (метод, URL, статус, тело, время) |
| `ServiceLog` | Собранные логи конкретного сервиса |
| `Report` | Отчёт с сводкой, таблицей сервисов, health, эмуляцией, логами |
| `WebEmulator` | Эмуляция 9 сценариев UI (см. ниже) |

**Режимы запуска моков:**
- `individual` (по умолч.) — каждый сервис на своём порту (auth:8082, orchestrator:8000, query:8083, registry:8084)
- `gateway` — всё через единый Gateway Mock (порт 8081)
- `none` — без моков

> 🔹 **Особенность:** `registry_real` конфликтует по порту (8084) с mock registry, поэтому при `--with-real` он автоматически пропускается.

**Определённые сервисы** (`SERVICE_DEFS`):

| Ключ | Тип | Порт | Имя |
|------|-----|------|-----|
| gateway | mock | 8080 | Gateway (Mock All-in-One) |
| auth | mock | 8082 | Auth Service |
| orchestrator | mock | 8081 | Orchestrator Service |
| query | mock | 8083 | Query Service |
| registry | mock | 8084 | Registry Service |
| integration | real | 8085 | Integration Service |
| registry_real | real | 8084 | Registry Service (real) |
| parser | real | 8087 | Parser Service |
| rag_builder | real | 8090 | RAG Builder Service |
| rag_search | real | 8091 | RAG Search Service |

**Сценарии эмуляции UI** (`WebEmulator.run_all_scenarios`):

1. `system_health` — GET /api/v1/system/health (без токена)
2. `auth` — POST /auth/token → GET /auth/me
3. `classifiers` — GET /api/v1/classifiers
4. `terminology` — GET /api/v1/terminology
5. `documents` — GET /api/v1/documents → GET /documents/{id}
6. `upload` — POST /api/v1/documents (multipart+text)
7. `monitor` — GET /api/v1/monitor/health
8. `search` — POST /api/v1/text/search
9. `chat` — POST /chat/sessions → POST /sessions/{id}/messages

> 🔹 **Особенность:** эмуляция делает те же вызовы, что и фронтенд — сценарии построены по реальному пользовательскому пути (auth → классификаторы → терминология → документы → поиск → чат). При падении аутентификации дальнейшие сценарии продолжаются с заглушками.

**Команды CLI:**

```
python service_checker.py all       # запуск + health + эмуляция + отчёт
python service_checker.py start     # запустить сервисы
python service_checker.py health    # health check
python service_checker.py emulate   # эмуляция UI
python service_checker.py docker    # управление Docker (up/down/build/coverage/health/logs)
python service_checker.py report    # отчёт из сохранённых логов
```

---

### 2. `api_coverage_test.py` — API Coverage Test

Проверяет вызов **каждого эндпоинта из документации** по каждому сервису. Работает только в Docker (real-режим).

> 🔹 **Особенность:** эндпоинты строятся строго на основе файлов `docs/api/*.md`. Порядок внутри цепочек: CREATE → GET → PUT → PATCH → DELETE, чтобы эндпоинты, зависящие от ID из предыдущих вызовов, выполнялись после создания.

**Ключевые компоненты:**

| Компонент | Назначение |
|-----------|------------|
| `EndpointDef` | Определение эндпоинта (метод, путь, тело, схема ответа) |
| `EndpointResult` | Результат вызова одного эндпоинта |
| `ServiceResult` | Результаты по сервису (passed, failed, skipped, ping_ok) |
| `ApiCoverageTester` | Движок: ping → resolve → request → validate → extract context → report |
| `build_endpoints()` | Описывает **все эндпоинты** сервисов на основе docs/api/*.md |

**Логика определения success/fail** (см. `test_service`):

- **2xx/3xx** — success
- **4xx/5xx с валидным JSON** — success (эндпоинт существует, сервис ответил)
- **4xx/5xx без JSON** — fail
- **Оверрайд `all_404`** — если ≥2 не-health эндпоинтов вернули 404 → `ping_ok=False`, success откатывается у всех результатов (включая health)

> 🔹 **Особенность:** 404 с валидным JSON считается успехом — эндпоинт существует и вернул осмысленный ответ (ресурс не найден). Это отличает реально работающий сервис от заглушки на порту.
> 🔹 **Особенность:** all_404 оверрайд — защита от «призрачных» сервисов. Если на порту запущено что-то другое (например, Parser вместо OCR), механизм all_404 детектирует это: ≥2 не-health эндпоинтов вернули 404 → ping_ok=False, success откатывается у ВСЕХ результатов, включая health.

**Проверяемые сервисы** (порты из `MODE_PORTS`):

| Сервис | Порт | Кол-во эндпоинтов |
|--------|------|-------------------|
| auth | 8082 | 16 (health, auth, admin, internal) |
| registry | 8084 | 28 (classifiers, terminology, documents, common) |
| orchestrator | 8081 | 30 (health, monitor, tasks, documents, search, drafts) |
| query | 8083 | 20 (health, chat, history, text) |
| parser | 8087 | 5 |
| ocr | 8088 | 5 (см. аномалию — сервис не существует) |
| converter_validator | 8086 | 4 |
| rag_builder | 8090 | 4 |
| rag_search | 8091 | 2 |
| gateway | 8080 | 120+ (агрегирует auth+orchestrator+query+registry) |

**Контекстные переменные:** между вызовами сохраняются ID (`doc_id`, `session_id`, `user_id`, `classifier_code`, `term_id`, `message_id`, `task_id`, `refresh_token`, `access_token`) для подстановки в шаблоны путей (`{doc_id}`, `{draft_id}`).

**Prepare-шаги:** перед основными эндпоинтами выполняются prepare-эндпоинты, которые создают необходимые данные (JWT-токен, ID объектов). Prepare могут обращаться к другим сервисам через `override_port` — альтернативный порт, отличный от порта тестируемого сервиса.

> 🔹 **Особенность:** контекстные переменные обеспечивают связанность цепочек эндпоинтов. Например, `POST /classifiers` возвращает `classifier_code`, который автоматически подставляется в `GET /classifiers/{classifier_code}`, `PUT /classifiers/{classifier_code}`, `DELETE /classifiers/{classifier_code}`. Без этого пришлось бы хардкодить ID.
> 🔹 **Особенность:** валидация схемы ответа (`response_schema`) — проверяет не только наличие поля, но и его тип (точечная нотация: `data.id` → str). Если схема не совпала — эндпоинт помечается как failed, даже при HTTP 200.

**Генерируемые отчёты:**
- `check_result/api_coverage_{timestamp}.md` — сводка + детали по каждому эндпоинту + контекст + легенда + карта зависимостей
- `check_result/errors_{timestamp}.md` — логи ошибок supervisord

---

### 3. `pipeline_test.py` — Pipeline Testing (Сквозные сценарии)

Проверяет **сквозные бизнес-пайплайны** обработки документов с реальным PDF-файлом.
В отличие от API Coverage Test (проверка каждого эндпоинта изолированно), этот режим
эмулирует реальную работу системы: загрузка → парсинг → конвертация → регистрация → индексация → поиск.

> 🔹 **Особенность:** второй режим тестирования — **сценарный (pipeline)**. Вместо изолированных вызовов эндпоинтов проверяется полный цикл обработки реального PDF-документа с валидацией содержимого JSON на каждом шаге.

**Принцип работы:**

1. Берётся реальный PDF-файл из каталога `service_checker/pdf/`
2. Файл загружается в MinIO (S3-совместимое хранилище)
3. Запускается последовательность шагов пайплайна, где выход одного сервиса подаётся на вход следующему
4. На каждом шаге проверяется не только HTTP-статус, но и **структура и содержимое JSON-ответа**
5. Результаты сводятся в единую таблицу: одна строка — один пайплайн

**Определённые пайплайны:**

| Пайплайн | Описание | Сервисы | Шагов |
|----------|----------|---------|:-----:|
| `document_processing` | Полный цикл обработки документа | MinIO → Parser → Converter → Registry → RAG Builder → RAG Search | 8 |
| `chat_inference` | Чат-сессия с поиском по проиндексированным документам | Auth → Query (Chat) → Query (Text Search) → RAG Search | 6 |
| `registry_lifecycle` | CRUD + импорт классификаторов и терминов | Auth → Registry | 13 |

---

#### Пайплайн: `document_processing`

Полный конвейер обработки реального PDF-документа:

```
PDF-файл
  │
  ▼
┌── 1. MinIO ─────────────────────────────────────────────┐
│  Загрузка PDF в S3-хранилище (PUT /minio/documents/)    │
│  ✅ Проверка: файл сохранён, ключ доступа получен       │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 2. Parser Service ────────────────────────────────────┐
│  POST /api/v1/parser/process  — запуск парсинга         │
│  GET  /api/v1/parser/process/{task_id}/status  — longpoll│
│  GET  /api/v1/parser/process/{task_id}/result  — JSON   │
│  ✅ Проверка: result содержит pages[], blocks[], text    │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 3. Converter-Validator Service ───────────────────────┐
│  POST /api/v1/converter/convert — конвертация JSON      │
│  ✅ Проверка: структура соответствует target-схеме      │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 4. Registry Service ──────────────────────────────────┐
│  POST /api/v1/registry/documents — сохранение документа │
│  ✅ Проверка: doc_id создан, metadata совпадает         │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 5. RAG Builder Service ───────────────────────────────┐
│  POST /api/v1/rag/build — построение чанков и индексация│
│  GET  /api/v1/rag/build/{doc_id}/status  — longpoll     │
│  ✅ Проверка: чанки созданы, индекс построен            │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 6. RAG Search Service ────────────────────────────────┐
│  POST /api/v1/rag/search — поиск по проиндексированному │
│  ✅ Проверка: результаты содержат фрагменты из PDF     │
└──────────────────────────────────────────────────────────┘
```

> 🔹 **Особенность:** пайплайн `document_processing` — сквозной тест «от файла до ответа». Если на любом шаге JSON не соответствует ожидаемой структуре или данные потеряны, пайплайн помечается как failed.

---

#### Пайплайн: `chat_inference`

Проверяет, что после индексации документа можно выполнить текстовый поиск, задать вопрос и получить осмысленный ответ.
В этом пайплайне участвуют сервисы: **Auth → Query (Chat) → Query (Text Search) → RAG Search**.

```
┌── 1. Auth ──────────────────────────────────────────────┐
│  POST /auth/token → GET /auth/me                        │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 2. Query Service (Chat) ──────────────────────────────┐
│  POST /chat/sessions — создание сессии                   │
│  POST /chat/sessions/{id}/messages — отправка сообщения  │
│  ✅ Проверка: ответ содержит text, sources[], документы  │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 3. Query Service (Text Search) ───────────────────────┐
│  POST /api/v1/text/search — поиск по тексту              │
│  ✅ Проверка: результаты содержат фрагменты из PDF      │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 4. RAG Search ────────────────────────────────────────┐
│  POST /api/v1/rag/search — гибридный поиск по индексу   │
│  ✅ Проверка: результаты релевантны, score > 0.5        │
└──────────────────────────────────────────────────────────┘
```

> 🔹 **Особенность:** пайплайн `chat_inference` эмулирует реальный диалог пользователя: аутентификация → создание сессии → текстовый поиск → вопрос по документу → получение ответа с источниками через RAG Search.

---

#### Пайплайн: `registry_lifecycle`

Проверяет полный жизненный цикл классификаторов и терминов:

```
┌── 1. Auth ──────────────────────────────────────────────┐
│  POST /auth/token → GET /auth/me                        │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 2. Registry: Classifiers ─────────────────────────────┐
│  POST   /classifiers  (создать)                         │
│  GET    /classifiers/{code}  (получить)                 │
│  PUT    /classifiers/{code}  (обновить)                 │
│  PATCH  /classifiers/{code}  (частичное обновление)     │
│  DELETE /classifiers/{code}  (удалить)                  │
│  POST   /classifiers/import  (импорт)                   │
│  ✅ Проверка: все CRUD-операции, данные сохраняются     │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌── 3. Registry: Terminology ─────────────────────────────┐
│  POST   /terminology  (создать)                         │
│  GET    /terminology/{id}  (получить)                   │
│  GET    /terminology/normalize  (нормализация)          │
│  PUT    /terminology/{id}  (обновить)                   │
│  DELETE /terminology/{id}  (удалить)                    │
│  POST   /terminology/import  (импорт)                   │
│  ✅ Проверка: термины созданы, нормализация работает    │
└──────────────────────────────────────────────────────────┘
```

---

#### Формат отчёта

Результаты pipeline-тестов выводятся в **горизонтальной таблице** — одна колонка на каждый пайплайн:

| Показатель | `document_processing` | `chat_inference` | `registry_lifecycle` |
|-----------|:---------------------:|:----------------:|:--------------------:|
| **Ping** | ✅ | ✅ | ✅ |
| **API calls** | 8/8 | 6/6 | 12/12 |
| **Pipeline** | ✅ Пройден | ✅ Пройден | ❌ CRUD classifiers |
| **Status** | ✅ | ✅ | ❌ |

> 🔹 **Особенность:** таблица транспонирована относительно классического отчёта: строки — метрики, столбцы — пайплайны. Показывает прохождение каждого сценария «по вертикали».

**Генерируемые отчёты:**
- `check_result/pipeline_{timestamp}.md` — детальная таблица пайплайнов + логи каждого шага

---

#### Итоговая сводная таблица

Результаты **обоих режимов тестирования** сводятся в единую таблицу — одна строка на сервис.
Столбцы показывают, в каких пайплайнах участвует сервис и успешно ли они пройдены.

| Service | Port | Ping | ✅ Passed | Documents | Query | Status |
|---------|:----:|:----:|:---------:|:---------:|:-----:|:------:|
| Auth Service | 8082 | ✅ | 16/16 | — | ✅ | ✅ |
| Orchestrator | 8000 | ✅ | 27/27 | — | — | ✅ |
| Gateway | 8081 | ✅ | 80/80 | — | — | ✅ |
| Query Service | 8083 | ✅ | 20/20 | — | ✅ | ✅ |
| Registry Service | 8084 | ✅ | 28/28 | ✅ | — | ✅ |
| Parser Service | 8087 | ✅ | 5/5 | ✅ | — | ✅ |
| Converter-Validator | 8086 | ✅ | 4/4 | ✅ | — | ✅ |
| RAG Builder | 8090 | ✅ | 4/4 | ✅ | — | ✅ |
| RAG Search | 8091 | ✅ | 2/2 | ✅ | ✅ | ✅ |

> 🔹 **Особенность:** итоговая таблица объединяет API Coverage (✅ Passed) и Pipeline Testing (Documents, Query) в одном представлении. 

**Детализация колонок:**

- **Service / Port** — имя и порт сервиса из `SERVICE_DEFS` / `MODE_PORTS`
- **Ping** — ✅ сервис отвечает на health check, ❌ недоступен
- **✅ Passed** — успешные эндпоинты / общее количество (из API Coverage Test)
- **Documents** — ✅ пайплайн обработки документов пройден для этого сервиса, ❌ сбой, — сервис не участвует
- **Query** — ✅ пайплайн чата/поиска пройден, ❌ сбой, — сервис не участвует
- **Status** — ✅ если Ping + покрытие + все пайплайны в зелёной зоне, иначе ❌

**Генерируемый отчёт:**
- `check_result/full_report_{timestamp}.md` — итоговая таблица + детали API Coverage + детали Pipeline Testing

---

#### Детализация пайплайнов

Для каждого пайплайна выводится таблица шагов с результатами — аналогично детализации эндпоинтов в API Coverage.

##### Pipeline: `document_processing`

| # | Step | Service | Status | Code | Проверка |
|---|------|---------|:------:|:----:|----------|
| 1 | Загрузка PDF в MinIO | MinIO | ✅ | 200 | file_key получен |
| 2 | Запуск парсинга | Parser | ✅ | 202 | task_id получен |
| 3 | Статус парсинга (longpoll) | Parser | ✅ | 200 | status=completed |
| 4 | Результат парсинга | Parser | ✅ | 200 | pages[], blocks[], text |
| 5 | Конвертация JSON | Converter | ✅ | 200 | target-схема совпадает |
| 6 | Сохранение документа | Registry | ✅ | 201 | doc_id создан |
| 7 | Построение чанков + индексация | RAG Builder | ✅ | 200 | chunks created |
| 8 | Поиск по индексу | RAG Search | ✅ | 200 | фрагменты из PDF |

**Итог:** ✅ Пройден | Ping: ✅ | API calls: 8/8

##### Pipeline: `chat_inference`

| # | Step | Service | Status | Code | Проверка |
|---|------|---------|:------:|:----:|----------|
| 1 | Аутентификация | Auth | ✅ | 200 | access_token получен |
| 2 | Профиль пользователя | Auth | ✅ | 200 | email, role |
| 3 | Создание чат-сессии | Query | ✅ | 201 | session_id получен |
| 4 | Отправка сообщения | Query | ✅ | 200 | ответ с text, sources[] |
| 5 | Текстовый поиск | Query | ✅ | 200 | фрагменты из PDF |
| 6 | Гибридный поиск | RAG Search | ✅ | 200 | score > 0.5 |

**Итог:** ✅ Пройден | Ping: ✅ | API calls: 6/6

##### Pipeline: `registry_lifecycle`

| # | Step | Service | Status | Code | Проверка |
|---|------|---------|:------:|:----:|----------|
| 1 | Аутентификация | Auth | ✅ | 200 | access_token получен |
| 2 | Создать классификатор | Registry | ✅ | 201 | classifier_code получен |
| 3 | Список классификаторов | Registry | ✅ | 200 | data[] |
| 4 | Получить классификатор | Registry | ✅ | 200 | data.code совпадает |
| 5 | Обновить классификатор | Registry | ✅ | 200 | full_name обновлён |
| 6 | Частичное обновление | Registry | ✅ | 200 | status=inactive |
| 7 | Удалить классификатор | Registry | ✅ | 200 | |
| 8 | Импорт классификаторов | Registry | ✅ | 200 | |
| 9 | Создать термин | Registry | ✅ | 201 | term_id получен |
| 10 | Нормализация термина | Registry | ✅ | 200 | normalized_value |
| 11 | Обновить термин | Registry | ✅ | 200 | definition обновлён |
| 12 | Удалить термин | Registry | ✅ | 200 | |

**Итог:** ❌ CRUD classifiers | Ping: ✅ | API calls: 12/12

### 4. `setup.py` — One-command setup

Автоматизирует подготовку модели TEI и запуск Docker Compose одной командой.

```
python setup.py                 # Полный цикл
python setup.py --model         # Только модель
python setup.py --up            # Только Docker
python setup.py --down          # Остановка
python setup.py --ps            # Статус
```

### 5. `setup_db.py` — Инициализация БД

Скрипт для создания и настройки единой PostgreSQL-базы `pkb_neuroassistant` (схемы, расширения, таблицы, пользователи).

**Функции:**

- Создание/пересоздание БД (`--drop-first`)
- Установка расширений: `uuid-ossp`, `pgcrypto`, `ltree`, `pg_trgm`, `vector` (pgvector — опционально)
- Создание схем `registry` и `rag`
- Загрузка схемы Registry из `backend/registry_service/install/0. full_schema.sql`
- Создание RAG-таблиц: `rag.document_chunks` (с HNSW-индексом и GIN-индексом полнотекстового поиска)
- Создание пользователей: `pkb_user` (registry, integration), `rag_user` (rag_builder, rag_search)
- Генерация `.env`-файлов для сервисов (Registry, Integration, RAG Builder, RAG Search, Orchestrator)
- Поиск `psql` в PATH и стандартных путях Windows

> 🔹 **Особенность:** единая БД для всех сервисов — `pkb_neuroassistant`. Каждый сервис получает своего пользователя (`pkb_user`, `rag_user`) с правами только на нужные схемы, а не один суперпользователь.
> 🔹 **Особенность:** pgvector опционален — RAG-таблицы создаются только если расширение `vector` установлено в ОС. Иначе RAG-сервисы работать не будут, но остальная система запустится.
> 🔹 **Особенность:** поддержка Windows — скрипт ищет psql не только в PATH, но и в типичных местах (`C:\Program Files\PostgreSQL\{15,16,17}\bin\psql.exe`), а SQL-файл пишется с UTF-8 BOM для корректного чтения psql на Windows.

**Использование:**
```
python setup_db.py                    # интерактивный ввод пароля
python setup_db.py --password pass    # пароль в аргументе
python setup_db.py --dry-run          # только показать SQL
python setup_db.py --drop-first       # пересоздать с нуля
python setup_db.py --only-env         # только .env файлы
```

---

### 6. Docker-конфигурация (директория `docker/`)

| Файл | Назначение |
|------|------------|
| `docker-compose.yml` | 5 контейнеров: **postgres** (pgvector/pg16), **redis** (7-alpine), **minio** (S3), **tei** (Hugging Face TEI), **app** (11 Python-сервисов под supervisord) |
| `supervisord.conf` | Управление 11 процессами: auth, gateway, orchestrator, query, registry, integration, converter-validator, parser, ocr, rag-builder, rag-search |
| `Dockerfile.base` | Базовый образ |
| `Dockerfile.full` | Полный образ |
| `entrypoint.sh` | Точка входа: создание директорий, PYTHONPATH, автоустановка зависимостей, запуск supervisord |
| `requirements.txt` | Python-зависимости |
| `prepare_tei_model.py` | Скачивание и подготовка локальной ONNX-модели для TEI |

**Ключевая архитектурная особенность:** все Python-сервисы работают **в одном контейнере** под supervisord. `autorestart=false` для всех программ — сервисы не должны перезапускаться при краше.

> 🔹 **Особенность:** три уровня health check в Docker: (1) `docker compose ps` — жив ли контейнер, (2) HTTP-пинг каждого Python-сервиса по его порту, (3) `supervisorctl status` — все ли процессы RUNNING.
> 🔹 **Особенность:** перед coverage test **очищаются supervisord-логи** (`truncate -s 0`), чтобы в отчёт попали только логи текущего запуска, а не накопленные за дни.
> 🔹 **Особенность:** сбор логов с авто-классификацией — скрипт читает каждый файл из `/var/log/supervisor`, ищет паттерны ошибок (`Traceback`, `Error`, `ERROR`, `FATAL`) и раскладывает на Info/Error-секции с навигацией (TOC).
> 🔹 **Особенность:** entrypoint.sh имеет self-fix CRLF — если скрипт был склонирован на Windows (CRLF), он сам себя чинит и перезапускается.
> 🔹 **Особенность:** зависимости устанавливаются при каждом старте контейнера (`pip install -r requirements.txt`), чтобы не ждать пересборки образа при изменении зависимостей.

---

### 7. `observability_check.py` — Проверка инструментации (SC-1)

Модуль для проверки observability-инструментации сервисов. Работает в двух режимах:

1. **Динамическая проверка** — через API сервиса: health endpoint, заголовки ответа, структура логов
2. **Статический анализ** — поиск OTEL-инициализации в исходном коде

**Проверяемые аспекты:**

| Аспект | Что проверяется | Метод |
|--------|-----------------|-------|
| OTEL SDK | Инициализация OpenTelemetry, OTLPSpanExporter, TracerProvider | Статический анализ (`re` по .py файлам) |
| OTLP-экспорт | Наличие signoz-otel-collector в конфигурации | Статический анализ |
| Span-атрибуты | instrument_app, BatchSpanProcessor | Статический анализ |
| Корреляционные заголовки | X-Request-ID, X-Trace-ID, X-User-ID, X-Draft-ID, X-Document-ID, X-Version-ID в ответе /health | HTTP-запрос |
| Структурированное логирование | JSON-поля severity, timestamp, service, trace_id, span_id | HTTP + статический анализ |
| Health endpoint | Наличие /api/v1/health (собственный, не /system/health) | HTTP-запрос |
| X-User-ID | Проверка заголовка X-User-ID в ответе (GW-9) | HTTP-запрос |
| X-Trace-ID | Проверка заголовка X-Trace-ID в ответе (OTEL correlation) | HTTP-запрос |
| Коды ошибок | INDEX_TRIGGER_TIMEOUT (408), DECISION_TIMEOUT (408), PREVIEW_TRIGGER_TIMEOUT (408), LLM_GENERATION_TIMEOUT (408), PREVIEW_NOT_SUPPORTED (422), EMPTY_QUERY (400), INVALID_PARAMETER (422) | HTTP-запрос |

**Использование:**

```bash
# Проверить все сервисы
python -m service_checker check

# Проверить конкретный сервис
python -m service_checker check auth

# CI-режим: exit-code 0/1/2
python -m service_checker check auth --post-deploy

# Статический анализ исходного кода
python -m service_checker check auth_service --source-dir /path/to/auth_service
```

**Exit codes (SC-2):**
- `0` — всё хорошо
- `1` — ошибки (сервис не отвечает, нет OTEL)
- `2` — предупреждения (только в `--post-deploy`; нет correlation-заголовков, нет структурированных логов)

---

### 8. Тесты (`tests/`)

6 файлов, 71 тест:

| Файл | Тесты | Что проверяют |
|------|-------|---------------|
| `test_success_determination.py` | 6 | Логика success/fail: 200 → success, 404 с JSON → success, 404 без JSON → fail, 500 с JSON → success, 500 без JSON → fail |
| `test_override_logic.py` | 4 | all_404 оверрайд: с JSON, без JSON, откат health-результатов, mixed-режим |
| `test_report_generation.py` | 3 | Статус-колонка ❌ при ping_ok=False, иконки ✅/❌ в отчёте и в консоли |
| `test_no_restarts.py` | 1 (integration) | /auth/refresh не должен крашить Auth Service |
| `test_observability_check.py` | 11 | Модель ObservabilityCheckResult, формат отчёта, константы KNOWN_ERROR_CODES (7 кодов), CORRELATION_HEADERS |
| `test_pipeline_base.py` | 29 | Базовые классы Pipeline Testing: PipelineContext, PipelineStep, PipelineResult, PipelineDef, PipelineRunner, StepStatus, функции проверки |
| `test_pipeline_steps.py` | 28 | Шаги пайплайнов: document_processing (7), chat_inference (7→8 шагов с enrichment_skipped), registry_lifecycle (7), реестр пайплайнов (3) |

> 🔹 **Особенность:** тесты покрывают только логику service_checker (success/fail, all_404, отчёт). Интеграционный тест  требует Docker. Юнит-тесты сервисов (auth_service и др.) находятся в самих сервисах, не в checker.

---

## Архитектурные решения (из `specificity.md`)

1. **404 с валидным JSON = success** — эндпоинт существует, ресурс не найден
2. **all_404 оверрайд** — если ≥2 не-health эндпоинтов вернули 404, сервис помечается мёртвым (`ping_ok=False`, success откатывается)
3. **4xx/5xx без JSON = fail**
4. **Статус-колонка отчёта** — ❌ если `ping_ok=False`
5. **autorestart=false** — никакие сервисы не должны перезапускаться при краше
6. **TEI (Text Embeddings Inference)** — локальный сервер эмбеддингов, ONNX int8 модель `TrendHD/rubert-tiny2-int8` (312 dim), порт 18092, bind mount `./tei_model:/data`

> 🔹 **Особенность:** отчёт генерируется в двух форматах — Markdown (для чтения в репозитории) и HTML (самодостаточная страница со стилями).
> 🔹 **Особенность:** карта зависимостей в отчёте — автоматически строится обратный граф зависимостей: если сервис не отвечает, показывается кто от него зависит и кто из них всё ещё жив (каскадные проблемы).
> 🔹 **Особенность:** Analyse Service временно исключён из coverage (нет контейнера), но его эндпоинты описаны в закомментированном блоке в `build_endpoints()` — достаточно раскомментировать при появлении контейнера.

---

## Аномалии (из `specificity.md`)

- **OCR Service не существует** — в supervisord на порт 8088 запущен Parser Service (частично исправлено в checker)
- **Auth Service падал на /auth/refresh** — баг в `auth_service` (исправлено, добавлена проверка `expires_at is None`)

> 🔹 **Особенность:** аномалии фиксируются в `specificity.md` и не исправляются автоматически — checker только адаптирует свою логику под них (например, all_404 оверрайд для OCR). Исправление самих сервисов — задача владельцев сервисов.

---

## Зависимости

- Python 3.9+
- `httpx` — асинхронные HTTP-запросы
- `pytest` + `pytest-asyncio` — тесты
- Docker + Docker Compose — для real-режима
- PostgreSQL + psql — для инициализации БД

> 🔹 **Особенность:** единственная внешняя Python-зависимость runtime — `httpx`. Никаких тяжёлых фреймворков. Отчёт генерируется без Markdown-библиотек (собственный конвертер md→html на регулярках).

---

## Запуск

```bash
# Полный setup с нуля: модель TEI + Docker Compose
python setup.py

# Все unit-тесты
python -m pytest tests/ -v

# API Coverage Test (требует Docker)
python api_coverage_test.py run-all

# Pipeline Testing (требует Docker с реальными сервисами)
python pipeline_test.py run-all
python pipeline_test.py run document_processing

# Запуск всех сервисов локально + health + эмуляция + отчёт
python service_checker.py all

# Docker: запустить + coverage + логи
python service_checker.py docker --action coverage
```
