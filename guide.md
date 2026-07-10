# Guide — архитектурные решения и стиль

## Сервер

**Адрес:** http://195.70.195.203
**Gateway:** http://195.70.195.203/api/v1



## Docker — обновление сервисов при разработке

**Правило:** фронтенд → build + up, бэкенд → restart (без build)

| Тип изменений | Команда |
|---|---|
| Фронтенд (TS/JSX/CSS) | `docker compose build frontend && docker compose up -d --no-deps frontend` |
| Python-сервисы (gateway, registry, query и др.) | `docker restart pkb-<service>` или `docker compose restart <service>` |
| Dockerfile / package.json / requirements.txt | `docker compose build <service> && docker compose up -d --no-deps <service>` |

У всех Python-сервисов исходники смонтированы через volumes + `--reload`,
поэтому пересборка не требуется — только рестарт контейнера.
Фронтенд — статика в nginx, нужна компиляция → build образа.

---

## Docker — CPU limits сервисов

CPU limits предотвращают ситуацию, когда 3 параллельных OCR + celery-worker + infinity перегружают CPU и kernel перестаёт обрабатывать прерывания (`hrtimer: interrupt took X ns`).

| Сервис | `cpus:` | Причина |
|--------|---------|---------|
| docling-service-cpu | `"2"` | Основной потребитель CPU (OCR + ML). `DOCLING_NUM_THREADS=4` при 2 vCPU — треды конкурируют, но не выжигают систему |
| celery-worker | `"2"` | 4 Celery-треда (`--concurrency=4 --pool=threads`) запускают subprocess'ы (tesseract, enrich). Лимит сдерживает взрыв |
| infinity | `"2"` | Reranker (BERT-like), уже имеет `mem_limit: 4g`. CPU предел страхует от скачков |
| orchestrator | `"1"` | FastAPI + QueueDrainPoller — лёгкий сервис, 1 ядра достаточно |

**Принцип:** лимиты считаются от 16 vCPU хоста — сумма `cpus` сервисов не должна превышать 50% физических ядер (остальное ОС + запас). При `cpus: "2"` на docling-serve, 4 документа обрабатываются в 2 волны — медленнее, но система остаётся стабильной.

---

## Правила диагностики серверных ошибок

При жалобе «сервер не работает / ошибка» — не гадать, а собирать диагностику системно:

1. **Gateway diagnostics** (публичный, не требует auth):
   - `GET /api/v1/system/diagnostics` — быстрая сводка + pipeline/БД/Celery
   - `GET /api/v1/system/diagnostics?verbose=true` — полная (dmesg, порты, диски, compose, volumes, git, ошибки, pipeline, БД, Redis)
   - `GET /api/v1/system/diagnostics/{service}` — по конкретному сервису (включая docling-serve, celery-worker)
   - `GET /api/v1/system/diagnostics/{service}?logs=200` — больше строк лога (параметр `logs`, не `log_lines`)
   - `GET /api/v1/system/diagnostics/system` — логи ядра
   - `GET /api/v1/system/logs/{service}?lines=500` — сырые docker-логи (без обёртки diagnostics; макс 500 строк)

   **Что показывает diagnostics всегда (без verbose):**
   - `[Pipeline: tasks]` — статистика задач: total, by_status, by_stage; активные задачи с пошаговой разбивкой (status, started_at, completed_at каждого шага); недавно завершённые
   - `[Pipeline: document queue]` — очередь документов оркестратора
   - `[Pipeline: DB]` — SQL-запросы напрямую в PostgreSQL: сводка по статусам; задачи, не обновлявшиеся >5 мин (потенциально зависшие) с указанием шага и времени; running/pending шаги всех задач
   - `[Registry: DB stats]` — количество документов/draft'ов/версий; последние ошибки
   - `[Celery]` — длина очередей через Redis (LLEN), зарезервированные и запланированные задачи
   - `[Registry: documents]` — количество документов в реестре через Registry API

   **Поддерживаемые сервисы для {service}:**
   gateway, orchestrator, parser, converter-validator, rag-builder, rag-search, registry, auth, query, celery-worker, frontend, postgres, redis, minio, infinity, docling-serve

2. **Health endpoints:**
   - `GET /api/v1/health` — gateway health
   - Прямые запросы к сервисам (если порты открыты): 8083 query, 8084 registry, 8091 rag-search, 7997 infinity

3. **Что смотреть в verbose diagnostics в первую очередь:**
   - `[System]` Memory/Swap — не забита ли память
   - `[Kernel]` — OOM kills (искать `Out of memory: Killed process`)
   - `[Memory pressure]` — не перегружена ли система
   - `[Ports]` — какие сервисы реально слушают порты

4. **Если docker логи недоступны** (SSH нет):
   - diagnostics показывает stderr docker — ошибка `error: no such object` значит контейнер не запущен или docker CLI не работает
   - dmesg из diagnostics — основной источник для OOM/kernel
   - SSH на сервер: `docker logs pkb-{service} --tail 50`

5. **Цепочка отказа:** начинать с downstream — если сервис Б не отвечает, смотреть его зависимости (сервис А, от которого он зависит). OOM одного сервиса валит всю цепочку.

## Правила поведения при диагностике

### П1. Не гадать — читать код

Любой непонятный ответ от сервиса — смотреть код того, кто этот ответ формирует. Если diagnostics пишет `(container not found)` — идти в `diagnostics.py`, смотреть как `run()` обрабатывает stderr. Не делать предположений «наверное docker не работает».

### П2. Симптом не равен причине

Ошибка в точке А не значит что проблема в А. «Поиск временно недоступен» в query_service — это следствие OOM infinity, а не проблема поиска. При диагностике — пройти всю цепочку: от пользователя до самого downstream сервиса.

### П4. Прежде чем сказать «не могу» — убедись что исчерпал все инструменты

- Docker CLI нет в образе → установить, а не говорить «нужен SSH»
- Gateway не отвечает на `/api/v1/rag/health` → посмотреть route transform, а не «rag-search недоступен»
- diagnostics молчит → починить `run()`, а не гадать

### П5. Gateway route transform — критическая точка

Gateway проксирует `/api/v1/rag/...` на rag_search. Но если transform не задан — путь идёт как есть (`/api/v1/rag/api/v1/health` вместо `/api/v1/health`). RAG search падает с 404. Всегда проверять transform при добавлении нового route.

### П6. Изменение конфига = изменение кода — тестировать

Поменял `--engine optimum` на `--engine torch` в docker-compose.yml — нужно проверить что infinity стартует. Если нет — откатить или подобрать другую модель. Конфиг развёртывания не менее критичен чем код.

### П7. Сопоставлять исходники с диагностикой и дорабатывать недостающее

Если diagnostics чего-то не показывает — не говорить «не видно», а добавлять. Недостаток данных diagnostics — это не тупик, а задача.

### П8. При изменении сервиса — пересобрать всех зависимых

Изменение кода одного сервиса может потребовать пересборки других, которые его вызывают.

| Меняешь | Нужно пересобрать | Причина |
|---------|-------------------|---------|
| `registry_service` | **orchestrator** (+ celery-worker) | Оркестратор ходит в Registry API через HTTP. Если формат ответа изменился — клиент в `registry_client.py` должен быть синхронизирован |
| `converter_validator_service` | **orchestrator** (+ celery-worker) | Аналогично — `converter_client.py` ожидает определённый формат |
| `orchestrator_service` | — | orchestrator — единственный потребитель своего API (через gateway). celery-worker использует тот же образ |

**Типичная ошибка:** правишь `registry_service/api/v1/routes.py` или `crud/document.py`, делаешь `docker compose build registry && docker compose up -d registry`, но pipeline продолжает падать. Причина — celery-worker использует старый код `registry_client.py`. Решение: `docker compose build orchestrator && docker compose rm -sf orchestrator celery-worker && docker compose up -d orchestrator celery-worker`.

### П9. Диагностика pipeline — последовательность шагов

При проблеме «pipeline завершился, но данных нет»:

1. **Docker logs celery-worker** — первичный источник: grep по `converter|registry|document|content|section|step|400|409|422|500`
2. **Логи registry** — grep по IP celery-worker (обычно 172.18.0.11): `docker logs pkb-registry 2>&1 | grep 172.18.0.11` — видно какие запросы пришли и с каким статусом
3. **SQL в PostgreSQL** — проверить наличие данных напрямую, минуя API:
   ```
   docker exec pkb-postgres psql -U pkb -d pkb_neuro -c "SELECT id, title, doc_code, status FROM registry.documents WHERE id = <id>;"
   docker exec pkb-postgres psql -U pkb -d pkb_neuro -c "SELECT COUNT(*) FROM registry.document_sections WHERE document_id = <id>;"
   ```
4. **Прямой запрос к сервису** — обойти gateway, стучаться напрямую к сервису:
   ```
   curl http://localhost:8084/api/v1/registry/documents/{id}/sections
   ```
   (порт 8084 registry, 8083 query, 8091 rag-search, 8090 rag-builder)
5. **Проверка формата ответа API** — если API вернул 200, но данные пустые — сравнить реальный JSON с тем, что ожидает клиент. Особенно наличие/отсутствие обёртки `data`

**Почему в таком порядке:** логи говорят что вызвано, код — что должно быть, SQL — что есть на самом деле, прямой запрос — что отдаёт API. Разрыв между ними указывает на конкретную проблему.

## Тестирование через data/tests/

### Назначение

Тесты в `data/tests/` — скрипты, которые стучатся в корневой docker-compose через Gateway (порт 8080).
Не используют `service_checker`. Предназначены для быстрой проверки загрузки документов, pipeline и поиска.

### Автоматическая подготовка окружения

Перед запуском каждый тест вызывает `ensure_services()` из `data/tests/config.py`.
Функция:
1. Проверяет что тест идёт на `localhost` (не внешний сервер)
2. Перезапускает контейнеры рабочих сервисов (НЕ postgres, redis, minio, infinity) — **без пересборки образов**
3. Очищает БД (`TRUNCATE registry.drafts, registry.documents, pipeline.tasks CASCADE`)
4. Очищает Minio (удаление файлов в /data/documents/ и /data/images/)

**Образы НЕ пересобираются.** Код синхронизируется через volume-монтирование:
контейнеры читают файлы напрямую из `backend/<service>/`. Перезапуск (`docker compose up -d`)
подхватывает изменения без rebuild. Если нужна пересборка образа — делай вручную:
```
docker compose build <service>
```

**Два режима:**
| Режим | Сервисы | Какие тесты используют |
|-------|---------|----------------------|
| `minimal` | gateway, auth, registry | `test_dup_check`, `test_bulk_upload`, `test_api_coverage`, `test_go` |
| `all` | gateway, auth, registry, parser, converter-validator, rag-builder, rag-search, query, orchestrator, celery-worker, frontend | `test_e2e`, `test_full_pipeline`, `test_load_pkps_pdf`, `test_quick`, `test_universal_pdf_loader` |

**Системные сервисы НЕ перезапускаются:** postgres, redis, minio, infinity, db-init, minio-init.

**Отключение авто-подготовки** (для быстрых итераций — данные не чистятся):
```
set TEST_SKIP_REBUILD=true && python data/tests/test_dup_check.py data/pdf/2-020101-004.pdf
```

**Внешний сервер** (авто-подготовка не запускается):
```
set TEST_API_URL=http://195.70.195.203/api/v1 && python data/tests/test_e2e.py
```

### Доступные тесты

| Файл | Что проверяет | Требует pipeline |
|------|---------------|------------------|
| `test_dup_check.py` | Детекция дублирующей загрузки PDF | Нет |
| `test_bulk_upload.py` | Загрузка всех PDF из data/pdf/ | Нет |
| `test_api_coverage.py` | Доступность всех GET-эндпоинтов | Нет |
| `test_go.py` | Upload + approve + poll + search | Да |
| `test_quick.py` | Upload + preview + approve + poll | Да |
| `test_e2e.py` | Полный E2E: upload → pipeline → search | Да |
| `test_full_pipeline.py` | Полный pipeline с верификацией search | Да |
| `test_load_pkps_pdf.py` | Загрузка ПКПС pdf → pipeline → search | Да |
| `test_universal_pdf_loader.py` | Загрузка любого PDF → pipeline → sections → search | Да |

## Chat FSM — статусы сообщений

Бэкенд (`query_service`) и фронтенд (`UI Final`) должны быть синхронизированы по набору статусов.

**Финальные статусы (бэкенд `_FINAL_STATUSES`):**

| Статус | Когда выставляется | Frontend-маппинг |
|--------|--------------------|------------------|
| `answered` | Успешный ответ с фрагментами | `mapGatewayStatus` → `'answered'` |
| `failed` | Ошибка поиска/LLM | `mapGatewayStatus` → `'failed'` |
| `not_found` | Нет фрагментов в БЗ | `mapGatewayStatus` → `'not_found'` |
| `out_of_scope` | Запрос вне области знаний | `mapGatewayStatus` → `'out_of_scope'` |
| `needs_clarification` | Недостаточно контекста | `mapGatewayStatus` → `'needs_clarification'` |
| `source_conflict` | Конфликт источников | `mapGatewayStatus` → `'source_conflict'` |

**Промежуточные статусы:** `pending` → `enriching` → `searching` → `generating` → `enriching_citations`

**Ключевые точки синхронизации:**
- Бэкенд: `_FINAL_STATUSES` в `backend/query_service/app/routes/chat.py` (строка 31)
- Фронтенд: `isFinalChatStatus` в `UI-UX/UI Final/frontend/src/utils/http.ts`
- Фронтенд: `mapGatewayStatus` в том же файле
- Фронтенд: `AnswerStatus` тип в `UI-UX/UI Final/frontend/src/utils/mockData.ts`
- Фронтенд: `statusLabel`/`statusTone` в `UI-UX/UI Final/frontend/src/components/Chat.tsx`

При добавлении нового статуса — править все 5 точек одновременно.
