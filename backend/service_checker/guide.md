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
