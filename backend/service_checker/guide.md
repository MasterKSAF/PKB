# Архитектурные ориентиры

## Ленивая инициализация HTTP-клиента

**Проблема**: `httpx.AsyncClient()` загружает SSL-сертификаты при создании (~0.37s).  
`PipelineRunner` и `ApiCoverageTester` создавали клиент в `__init__`, из-за чего каждый unit-тест платил ~0.4s, даже если клиент сразу заменялся моком.

**Решение**: `httpx.AsyncClient` создаётся лениво — при первом реальном обращении к `self.client`.  
Реализовано через `@property` + приватный `_client`. Сеттер позволяет DI (подстановка мока в тестах).

**Паттерн**:
```python
self._client: Optional[httpx.AsyncClient] = None

@property
def client(self) -> httpx.AsyncClient:
    if self._client is None:
        self._client = httpx.AsyncClient(timeout=self.timeout)
    return self._client

@client.setter
def client(self, value: httpx.AsyncClient) -> None:
    self._client = value
```

**Где применяется**:
- `pipelines/base.py` — `PipelineRunner`
- `core/api_coverage_test.py` — `ApiCoverageTester`

---

## Проверка состояния сервисов в Docker

Любая проверка Docker (статус сервисов, coverage, pipeline-тесты) запускается **только** через:

```
cd docker && recheck.bat       # Обычный режим (rag-builder + rag-search)
cd docker && recheck_spd.bat   # SPD-режим (rag-builder-spk на 8090)
```

**Что делает**: чистит БД → перезапускает app → ждёт supervisor → запускает полный отчёт.

**Почему**: checker подразумевает, что внутри контейнера все сервисы под supervisor работают с чистыми данными. Нельзя запускать checker напрямую (`python _run_gateway_coverage.py`), потому что:
- supervisor может быть не готов
- данные могут быть неконсистентны
- prepare-шаги ожидают чистую БД

---

## Unit-тесты vs Docker

**Unit-тесты** (`python -m pytest tests/`) проверяют только Python-логику checker'а:
парсинг аргументов, формирование отчётов, pipeline runner, определение эндпоинтов.
Они **не проверяют Docker** — не запускают контейнеры, не ходят по HTTP.

**Docker проверяется** только интеграционно через `recheck.bat` / `recheck_spd.bat`:
валидация docker-compose, реальный запуск контейнеров, supervisorctl, checker.

Это разделение гарантирует, что юнит-тесты быстрые (~1.3с) и не зависят от Docker.

---

## Единый источник портов — MODE_PORTS

Порты всех сервисов хранятся в `services/__init__.py → MODE_PORTS`.
`PipelineRunner._get_service_port`, `ApiCoverageTester` и `_get_health_services`
берут порты оттуда.

Это позволяет подменить порт для любого сервиса глобально (например, при `--spd`
`MODE_PORTS["rag_search"] = 8090`), и все компоненты checker'а автоматически
подхватят новое значение.

**Важно**: `PipelineRunner.run_step()` использует `_get_service_port(step.service)`
как приоритет над `step.port`. Это значит, что хардкод `port=...` в pipeline step
definitions — только fallback. Реальный порт всегда из MODE_PORTS.

---

## Registry: URL без trailing slash

**Проблема**: Registry service редиректит 307 Temporary Redirect при запросе с trailing slash.
`POST /api/v1/registry/classifiers/` → 307 → `/api/v1/registry/classifiers`.
Redirect теряет body → сервис получает пустой запрос.

**Ориентир**: все endpoint-ы registry (`/classifiers`, `/documents`, `/terminology`,
`/categories`, `/drafts` и их подпути) указывать **без** `/` в конце.
Исключение — ни одного, даже параметризованные пути.

**Где закреплено**:
- `services/registry.py` — service definition (api_coverage)
- Все registry-пайплайны (registry_lifecycle, registry_quarantine, full_document_lifecycle, document_processing, multi_document_cross_search, orchestrator_document_versions, document_approval)

---

## Orchestrator: POST /drafts — HTTP 500

**Проблема**: Orchestrator возвращает HTTP 500 на `POST /api/v1/registry/drafts`.
Registry `/drafts` эндпоинты уже реализованы, но Orchestrator всё равно падает с 500.

**Статус (2026-06-23)**: причина не установлена, требуется диагностика Orchestrator.
Затронуты 9 пайплайнов с черновиками.

---

## Registry: internal API — PATCH /documents/{id}/status, POST /drafts, PATCH /drafts/{id}/metadata

**Проблема**: Некоторые Registry-эндпоинты спроектированы как **internal** — доступны только `orchestrator`.
- `PATCH /api/v1/registry/documents/{id}/status` — только Orchestrator (docs 3.6)
- `POST /api/v1/registry/drafts` — только Orchestrator (docs 4.1)
- `PATCH /api/v1/registry/drafts/{id}/metadata` — только Orchestrator (docs 4.6)

**Ориентир**:
- `PATCH /status`: checker ожидает `{200, 403}` — 403 означает "внешний клиент" (норма)
- `POST /drafts`: checker шлёт тело по docs (`file_key`, `document_key`, `status`, `created_by`). Извлекает `draft_id` в контекст.
- `PATCH /drafts/{id}/metadata`: checker ожидает `{200, 404}` — internal

**Где закреплено**:
- `services/registry.py` — expected_status для internal endpoints

---

## Изолированное тестирование API Coverage

**Проблема**: API Coverage тестирует каждый сервис изолированно — контекст очищается между сервисами.
`{task_id}`, `{draft_id}`, `{version_id}` из контекста недоступны downstream сервисам.

**Ориентир**:
- Для эндпоинтов, где ID не участвуют в логике и не сохраняются в БД, используются константы:
  - `task_id = 12345`, `draft_id = 1`, `version_id = "1"`
- Pipeline тесты (сквозные) проверяют связанность с реальными ID из контекста

**Где закреплено**:
- `services/converter_validator.py` — константы в body
- `services/parser.py` — константы в body
- `pipelines/document_processing.py` — реальные ID через PipelineContext

---

## Registry: Categories не реализованы — честный ❌ Fail

**Ориентир**: Если эндпоинт спроектирован в документации, но не реализован в сервисе —
checker показывает ❌ Fail. Подгонка под тесты (expected_status={404}) запрещена.

**Где закреплено**:
- `services/registry.py` — categories endpoints без expected_status
- `specificity.md` #55 — аномалия зафиксирована

---

## Процедура валидации после изменений

После любых изменений, затрагивающих Docker или SPD, необходимо прогнать **оба** режима:

```bash
# 1. Обычный режим (rag-builder + rag-search)
cd docker && recheck.bat

# 2. SPD-режим (rag-builder-spk на 8090)
cd docker && recheck_spd.bat
```

Каждый `recheck*` делает:
1. Чистит БД (drop + create) и Redis (flushall)
2. Перезапускает app-контейнер
3. Ждёт supervisorctl (все процессы RUNNING)
4. Проверяет supervisor .err логи (пусты — нет ошибок)
5. Запускает health check (контейнеры → HTTP → supervisorctl → .err)
6. Запускает coverage + pipeline + полный отчёт

Ошибки валидации:
- **Обычный recheck падает** → проблема в normal-режиме (rag-builder + rag-search)
- **SPD recheck падает** → проблема в SPD-режиме (port override, pipeline steps)
- **Оба падают** → проблема в общей инфраструктуре (БД, Docker, supervisord)
