# Спецификация резолвера графа связей (Registry Resolver)

> **Версия**: 1.0 (17.06.2026)
> **Источник**: `analyse_alternative_project.md §1.1`, `db_diagrams.md` (таблица `registry.document_references`), обсуждения 13.06, 16.06.
> **Статус**: 🟠 серьёзное (P0-4 блокирующее до полноценной работы графа ссылок).

## 1. Назначение

`Registry Resolver` — фоновый компонент сервиса `Registry`, который сопоставляет
`registry.document_references.target_doc_code` (нормализованный идентификатор целевого ГОСТ/ТУ)
с реальной карточкой документа в `registry.documents` и проставляет
`is_resolved = TRUE` и `resolved_document_id`.

Без резолвера поле `is_resolved` всегда остаётся `FALSE`, что делает невозможным
навигацию по графу ссылок между документами («Правила РС» → конкретный ГОСТ),
анализ преемственности редакций и проверку целостности ссылочного графа.

## 2. Модель данных

Таблица `registry.document_references` (выдержка из `db_diagrams.md`):

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | bigint | PK |
| `source_document_id` | bigint (FK → `registry.documents.id`) | Документ-источник |
| `target_doc_code` | text | Целевой ГОСТ/ТУ/ОСТ/RD (нормализованный, см. §6) |
| `reference_type` | varchar | `single`, `range` |
| `context` | text | Контекст упоминания в источнике |
| `current_status` | text | Статус целевого документа (`active`, `superseded`, `expired`, `unknown`) |
| `replaced_by` | text | Код заменившего документа (для `superseded`) |
| `replacement_date` | date | Дата замены |
| `is_resolved` | boolean | `TRUE`, если `resolved_document_id` проставлен |
| `resolved_document_id` | bigint (FK → `registry.documents.id`, nullable) | Целевой документ |
| `created_at` / `updated_at` | timestamptz | Служебные |

**Индекс** (для ускорения выборки нерезолвленных ссылок):

```sql
CREATE INDEX idx_refs_unresolved
  ON registry.document_references(target_doc_code)
  WHERE is_resolved = FALSE;
```

## 3. Триггеры запуска

Резолвер запускается в двух режимах:

### 3.1. По событию (event-driven)

При создании **новой** карточки в `registry.documents` (после успешной фиксации
`approved → created`) Registry публикует внутреннее событие `document.created`
и синхронно вызывает резолвер для всех нерезолвленных ссылок, у которых
`target_doc_code` совпадает с `doc_code` новой карточки.

Преимущества:
- Минимальная задержка для пользователя: ссылка в только что созданном документе
  может сразу указывать на ранее загруженный «связанный» документ.
- Снижение нагрузки на фоновый планировщик.

### 3.2. Фоново (cron)

Периодический запуск (раз в час, настраивается через `RESOLVER_CRON_INTERVAL`):
обрабатывает **оставшиеся** нерезолвленные ссылки. Гарантирует, что:
- Ссылки, добавленные до создания новой карточки, тоже будут резолвлены.
- Ссылки на документы, которые ещё не загружены, будут ожидать появления
  соответствующего `doc_code` в системе.

## 4. Алгоритм резолвинга

### 4.1. Базовая стратегия: прямое совпадение по `doc_code`

```sql
UPDATE registry.document_references AS ref
SET is_resolved = TRUE,
    resolved_document_id = d.id,
    updated_at = NOW()
FROM registry.documents AS d
WHERE d.doc_code = ref.target_doc_code
  AND ref.is_resolved = FALSE
  AND ref.resolved_document_id IS NULL
RETURNING ref.id, d.id AS resolved_document_id;
```

**Стратегия резолвинга (конфигурируется в `app_settings.registry.resolver_strategy`):**

| Стратегия | Описание | Когда применять |
|-----------|----------|-----------------|
| `exact` (default) | Точное совпадение нормализованного `doc_code` | Стандартные ГОСТ/ОСТ/ТУ |
| `exact_active` | Только документы со статусом `active` (без `superseded`/`expired`) | Нормативные ссылки в действующих документах |
| `latest_revision` | Среди совпадений выбирается документ с **максимальным** `adoption_date` | Если в системе несколько редакций одного ГОСТ |
| `latest_version` | Среди совпадений выбирается документ с **максимальным** `version_number` | Если редакции фиксируются через `document_versions` |

### 4.2. Обработка `replaced_by` (преемственность)

Если для целевого документа известен `replaced_by` (т.е. у `doc_code` есть преемник),
резолвер дополнительно пытается найти заменённый документ в БД и записать ссылку
**на актуальную редакцию**:

```sql
-- 1. Ищем прямой матч
SELECT id FROM registry.documents WHERE doc_code = $1;
-- 2. Если не нашли и у target_doc_code есть replaced_by
SELECT id FROM registry.documents WHERE doc_code = $replaced_by;
-- 3. Проставляем resolved_document_id на найденную замену,
--    current_status = 'superseded' в reference
```

## 5. Логика работы фоновой задачи

| Параметр | Значение по умолчанию | Описание |
|----------|------------------------|----------|
| `RESOLVER_CRON_INTERVAL` | `3600` (1 час) | Интервал фонового запуска |
| `RESOLVER_BATCH_SIZE` | `500` | Количество ссылок, обрабатываемых за одну итерацию (LIMIT) |
| `RESOLVER_MAX_RUNTIME_SEC` | `120` | Максимальная длительность одной итерации |
| `RESOLVER_STRATEGY` | `latest_revision` | Стратегия выбора из нескольких кандидатов (см. §4.1) |
| `RESOLVER_LOCK_KEY` | `registry_resolver_run` | Advisory lock для предотвращения параллельного запуска |

**Защита от параллельного запуска** (PostgreSQL advisory lock):

```sql
SELECT pg_try_advisory_lock(hashtext('registry_resolver_run'));
-- если FALSE — другой инстанс уже работает, выход
```

## 6. Нормализация `doc_code` (критическое условие)

Для успешного резолвинга `target_doc_code` должен **точно** совпадать
с `registry.documents.doc_code`. Нормализация выполняется на стороне
Converter-validator при извлечении ссылок (поле `cross_references[].target_code`)
и должна следовать тому же алгоритму, что и нормализация `doc_code` при
сохранении карточки документа.

**Канонический алгоритм** (см. `specifications/normalizer_specification.md`):
1. Приведение к верхнему регистру.
2. Удаление всех пробелов (внутри номера и вокруг разделителей).
3. Унификация разделителей: `/`, `\`, `—`, `–` → `-`.
4. Удаление префиксов-дубликатов: `ГОСТ ГОСТ` → `ГОСТ`.
5. Удаление суффиксов года, если в `doc_code` хранится только номер (опционально,
   настраивается `NORMALIZER_STRIP_YEAR`).

**Проверка:** `normalizer_specification.md` содержит набор unit-тестов
(Given/When/Then) для всех правил. Резолвер при старте может прогнать
sanity-check на известных парах (например, `ГОСТ 20868-81` ↔ `гост 20868-81`)
и логировать warning при расхождении.

## 7. Метрики и мониторинг

| Метрика | Тип | Описание |
|---------|-----|----------|
| `registry.resolver.resolved_total` | counter | Общее число резолвленных ссылок с момента старта |
| `registry.resolver.unresolved_total` | gauge | Текущее число нерезолвленных ссылок |
| `registry.resolver.iteration_duration_seconds` | histogram | Длительность одной итерации фоновой задачи |
| `registry.resolver.batch_size` | histogram | Размер обработанной партии |
| `registry.resolver.errors_total` | counter | Ошибки (deadlock, потеря соединения и т.п.) |

**Алерты** (см. P11-8):
- `unresolved_total > 1000` более 24 часов — возможная деградация нормализатора.
- `iteration_duration_seconds p95 > 30` — перегрузка БД или резкий рост числа ссылок.

## 8. Тестирование

### 8.1. Unit-тесты

- Алгоритмы нормализации `doc_code` (покрытие ≥ 95% случаев из `normalizer_specification.md`).
- Стратегии резолвинга (`exact`, `exact_active`, `latest_revision`, `latest_version`).
- Логика `replaced_by` (преемственность редакций).

### 8.2. Integration-тесты

- Сценарий: загрузить документ A со ссылкой на ГОСТ X (которого ещё нет в системе)
  → ссылка остаётся `is_resolved = FALSE`. Загрузить документ B с `doc_code = X`
  → резолвер по событию проставляет `is_resolved = TRUE` для ссылки из A.
- Сценарий фоновой задачи: 1000 нерезолвленных ссылок, запуск фоновой задачи
  → все 1000 резолвлены, `iteration_duration_seconds < 30`.

### 8.3. Acceptance-критерии

- Доля `is_resolved = TRUE` для ссылок, у которых `doc_code` существует в системе,
  ≥ 99% (допускается задержка до 1 часа для фоновой задачи).
- 0 ложноположительных резолвов (тест: doc_code `X-1981` не должен резолвиться
  в `X-2025` при стратегии `exact`).

## 9. Связанные документы

- `db_diagrams.md` — таблица `registry.document_references`, индекс `idx_refs_unresolved`.
- `specifications/normalizer_specification.md` — алгоритм нормализации `doc_code`.
- `api/registry_service_api.md` — эндпоинт `GET /registry/documents/{id}/references`
  (возвращает `is_resolved` + `resolved_document_id`).
- `analyse_alternative_project.md §1.1` — происхождение требования.
- `pipelines/overview.md` — взаимодействие с FSM.
- P0-4 (план 5.06) — текущая инициатива, статус 🟠.

## 10. План внедрения

| Этап | Что | Когда |
|------|-----|-------|
| 1 | Миграция: добавить индекс `idx_refs_unresolved`, advisory lock key | 17.06 |
| 2 | Реализация event-driven триггера в `Registry` | 18–19.06 |
| 3 | Реализация cron-задачи | 20–21.06 |
| 4 | Метрики и алерты | 22.06 |
| 5 | Нагрузочный тест (10k нерезолвленных) | 23.06 |
| 6 | Документирование в `api/registry_service_api.md` (endpoint `GET /registry/resolver/status`) | 24.06 |
