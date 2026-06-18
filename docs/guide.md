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

## Стиль оформления документации

- Таблицы API: столбцы `Поле | Тип | Описание`. Тип — краткий (string, int, object, array).
- Ссылки на P#-задачи: `**P#**` в тексте.
- Ссылки на файлы: полный относительный путь от `docs/`.
- DDL-миграции описываются в табличном/списочном виде, без SQL-кода. CHECK-ограничения, FK, индексы — списком или таблицей. Для DBA эквивалентный SQL восстанавливается из описания однозначно (см. `docs/database/ddl_migrations_17_06.md`).
