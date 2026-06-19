# Guide — архитектурные решения и стиль

## Нейминг: `notifications` вместо `warnings` и `issues`

**Дата:** 18.06.2026
**Решение:** P3-5 (`quality.warnings[]`) и P12-3 (`quality.issues[]`) схлопнуты в единый массив `quality.notifications[]`.

**Обоснование:**
- Оба массива адресованы оператору (человеку за UI) — сервисы лишь передают данные, потребитель один.
- Нет технической причины разделять security-предупреждения и замечания по качеству: и те и другие — уведомления оператору.
- Единый массив упрощает контракт и UI (один рендер, одна фильтрация).
- Система новая, истории миграций нет — таблица БД с самого начала называется `pipeline.draft_notifications`.

**Структура:**
```json
{
  "code": "EMBEDDED_JS",
  "severity": "info | warning | error | critical",
  "category": "security | quality",
  "message": "human readable",
  "location": {"page": 1, "block": 5},
  "suggested_action": "reprocess | manual_edit | review | ignore | null"
}
```

**БД:** `pipeline.draft_notifications` (единая таблица, `category` разводит типы).

**P3-5 поглощён P12-3:** отдельный `warnings[]` не создаётся, security-предупреждения пишутся в `notifications[]` с `category: "security"`.

---

## Чеклист синхронизации при правках

При любом изменении статусной модели, enum-значений, полей БД или формата ответов API — обязательно проверить все точки, где эти значения перечислены.

**Конвенция регистра enum-значений:**
- `source_type`, `era`, `jurisdiction` — **UPPERCASE** (аббревиатуры и коды: `GOST`, `RMRS`, `USSR`, `RU`). Канонический регистр задан в `/registry/enums`.
- `document_type`, `validity_status` — строчные (`normative`, `technical`, `active`, `superseded`). Это слова, а не коды.
- Исключение — `normalizer_specification.md`: нормализатор приводит `source_type` к нижнему регистру для вычисления бизнес-ключа (осознанное решение для единообразия хеша).

DB CHECK-ограничения, DDL-миграции и спецификации должны использовать тот же регистр, что и API.

### При изменении FSM / добавлении статуса черновика

- [ ] `orchestrator_service_api.md` — поле `status` в `GET /drafts` (список enum)
- [ ] `orchestrator_service_api.md` — параметр фильтра `?status=`
- [ ] `orchestrator_service_api.md` — `PATCH /decide`: условие доступности действия
- [ ] `pipeline1-formation.md` — основная FSM-таблица (состояния)
- [ ] `pipeline1-formation.md` — упрощённая Draft FSM-таблица
- [ ] `pipeline1-formation.md` — FSM-диаграмма (mermaid)
- [ ] `gateway_service_api.md` — таблица ошибок: коды `DRAFT_ALREADY_DECIDED`
- [ ] `gateway_service_api.md` — RBAC и описание в route table
- [ ] `db_diagrams.md` — примечание о статусах черновика (если есть)
- [ ] `specificity.md` — зафиксировать изменение как решённое (при закрытии аномалии)

### При изменении enum-значения (source_type, era и т.п.)

- [ ] `registry_service_api.md` — `/registry/enums` (актуальный список, канонический регистр — UPPERCASE)
- [ ] `db_diagrams.md` — примечание enum в разделе `registry.documents`
- [ ] `db_diagrams.md` — CHECK-ограничение (регистр должен совпадать с API)
- [ ] `ddl_migrations_17_06.md` — DDL-Migration (список значений)
- [ ] `converter_validator_service_api.md` — `POST /converter/preview/metadata` (поле `source_type`)
- [ ] `converter_specification.md` — шаг 5 (классификация), если enum упомянут
- [ ] `glossary.md` — определение термина (если enum перечислен)
- [ ] `orchestrator_service_api.md` — `POST /drafts` (поле `source_type` обязательно при загрузке)
- [ ] Все JSON-примеры — содержат ли новое значение (если уместно)

### При добавлении поля в API-ответ/запрос

- [ ] Gateway route table — отражено ли изменение в описании эндпоинта
- [ ] Gateway sequence diagram — нужен ли новый шаг / нота
- [ ] Orchestrator API — описание поля и его тип
- [ ] Registry API (если applicable) — internal-эндпоинт
- [ ] Registry API модель 5.4 (registry_document) — добавлено ли поле в таблицу модели?
- [ ] `db_diagrams.md` — ER-диаграмма и примечание (если поле меняет БД)
- [ ] JSON-примеры — обновлены
- [ ] Если поле меняет lifecycle — проверен FSM и его документация

### При изменении модели данных (БД)

- [ ] `registry_service_api.md` 5.4 (registry_document) — все ли поля из ER-диаграммы `db_diagrams.md` отражены в модели?
- [ ] `db_diagrams.md` CHECK-ограничения — совпадают ли с enum в `/registry/enums` и DDL-миграциях?
- [ ] Регистр значений: DB CHECK должен совпадать с API (UPPERCASE). Исключение — нормализатор (lowercase для хеша)

### При изменении точек входа Gateway

- [ ] `gateway_service_api.md` — таблица маршрутизации (префикс, сервис, порт)
- [ ] `gateway_service_api.md` — секция read-only контракта (если admin-эндпоинт)
- [ ] `gateway_service_api.md` — секция middleware / заголовков (если новый заголовок)
- [ ] `gateway_service_api.md` — таблица специфичных ошибок

---

## Стиль оформления документации

- Таблицы API: столбцы `Поле | Тип | Описание`. Тип — краткий (string, int, object, array).
- Ссылки на P#-задачи: `**P#**` в тексте.
- Ссылки на файлы: полный относительный путь от `docs/`.
- DDL-миграции описываются в табличном/списочном виде, без SQL-кода. CHECK-ограничения, FK, индексы — списком или таблицей. Для DBA эквивалентный SQL восстанавливается из описания однозначно (см. `docs/database/ddl_migrations_17_06.md`).
