# Guide — архитектурные решения и стиль

## Правила диагностики серверных ошибок

При жалобе «сервер не работает / ошибка» — не гадать, а собирать диагностику системно:

1. **Gateway diagnostics** (публичный, не требует auth):
   - `GET /api/v1/system/diagnostics` — быстрая сводка
   - `GET /api/v1/system/diagnostics?verbose=true` — полная (dmesg, порты, диски, compose, volumes, git, ошибки)
   - `GET /api/v1/system/diagnostics/{service}` — по конкретному сервису
   - `GET /api/v1/system/diagnostics/{service}?log_lines=100` — больше строк лога (по умолчанию 20)
   - `GET /api/v1/system/diagnostics/system` — логи ядра

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

### П3. Изменяя `run()` — проверь всех, кто его вызывает

Общая функция (`run()`) используется везде. Изменение её поведения (начал возвращать stderr) влияет на всех — `_git()` сломался, потому что `if not branch:` перестал работать (stderr не пуст). Каждое изменение общей функции — проверить всех потребителей.

### П4. Прежде чем сказать «не могу» — убедись что исчерпал все инструменты

- Docker CLI нет в образе → установить, а не говорить «нужен SSH»
- Gateway не отвечает на `/api/v1/rag/health` → посмотреть route transform, а не «rag-search недоступен»
- diagnostics молчит → починить `run()`, а не гадать

### П5. Gateway route transform — критическая точка

Gateway проксирует `/api/v1/rag/...` на rag_search. Но если transform не задан — путь идёт как есть (`/api/v1/rag/api/v1/health` вместо `/api/v1/health`). RAG search падает с 404. Всегда проверять transform при добавлении нового route.

### П6. Изменение конфига = изменение кода — тестировать

Поменял `--engine optimum` на `--engine torch` в docker-compose.yml — нужно проверить что infinity стартует. Если нет — откатить или подобрать другую модель. Конфиг развёртывания не менее критичен чем код.

### П7. Сопоставлять исходники с диагностикой и дорабатывать недостающее

Если diagnostics чего-то не показывает — не говорить «не видно», а добавлять.

Схема:
1. Вижу симптом в diagnostics → иду в код diagnostics (`diagnostics.py`)
2. Смотрю что он реально делает (читает stdout, stderr игнорирует)
3. Понимаю какая информация нужна (stderr docker, transform пути)
4. Дорабатываю diagnostics или сервис чтобы эту информацию получить
5. Проверяю что изменения не сломали существующее (тесты)

**Примеры из этой диагностики:**
- `run()` не возвращал stderr → починил, diagnostics стал показывать реальные ошибки docker
- Gateway не трансформировал `/api/v1/rag/` → добавил transform, теперь rag-search health проверяется
- Docker CLI не было в образе → установил, diagnostics получил docker логи

Недостаток данных diagnostics — это не тупик, а задача.

## Тестирование через data/tests/

### Назначение

Тесты в `data/tests/` — скрипты, которые стучатся в корневой docker-compose через Gateway (порт 8080).
Не используют `service_checker`. Предназначены для быстрой проверки загрузки документов, pipeline и поиска.

### Автоматическая подготовка окружения

Перед запуском каждый тест вызывает `ensure_services()` из `data/tests/config.py`.
Функция:
1. Проверяет что тест идёт на `localhost` (не внешний сервер)
2. Перезапускает контейнеры только рабочих сервисов (НЕ postgres, redis, minio, infinity)
3. Очищает БД (`TRUNCATE registry.drafts, registry.documents, pipeline.tasks CASCADE`)
4. Очищает Minio (удаление файлов в /data/documents/ и /data/images/)

**Два режима:**
| Режим | Сервисы | Какие тесты используют |
|-------|---------|----------------------|
| `minimal` | gateway, auth, registry | `test_dup_check`, `test_bulk_upload`, `test_api_coverage`, `test_go` |
| `all` | gateway, auth, registry, parser, converter-validator, rag-builder, rag-search, query, orchestrator, celery-worker, frontend | `test_e2e`, `test_full_pipeline`, `test_load_pkps_pdf`, `test_quick`, `test_universal_pdf_loader` |

**Системные сервисы НЕ перезапускаются:** postgres, redis, minio, infinity, db-init, minio-init.
Образы НЕ пересобираются (используются существующие).

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
