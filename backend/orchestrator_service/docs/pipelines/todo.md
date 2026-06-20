# План работ: обновление статусной модели

Все пункты выполнены ✅

## Файл 1: `overview.md`

### 1. Раздел 4 — Статусная модель (FSM) [строки ~84-94]
- [x] Pipeline 1: `uploaded → previewing → awaiting_decision → parsing → validation → ready_for_promotion / review_required → approved → registry`
  → ✅ заменено на `uploaded → previewing → ready_for_approve → approved → created`
- [x] Pipeline 2: `pending_index → indexing → indexed`
  → ✅ заменено на `pending_index → indexing → indexed / failed`

### 2. Раздел 8 — Ключевые архитектурные решения [строки ~238-258]
- [x] Строка с таймаутами: `awaiting_decision` и `review_required`
  → ✅ заменено на `ready_for_approve` (24ч → discarded) и `pending_index` (1ч → failed)

### 3. Раздел 9 — End-to-end (сквозной поток) [строки ~258-347]
- [x] Шаг 4: `PATCH /drafts/{draft_id}/decide` — ✅ добавлен `?action=approve|reject`
- [x] Шаг 5: Full-фаза — ✅ убраны `validated_v3`, `Registry: создание карточки`
- [x] Шаг 3: ✅ убраны `duplicates / decision_required` → `preview_ready / ошибка`
- [x] После шага 5: ✅ шаг 6 переработан: Registry (статус `created`) + Pipeline 2

### 4. Раздел 10 — Сводная статусная модель [строки ~347-430]
- [x] ✅ FSM-диаграмма заменена на новую (P1 + P2)
- [x] ✅ Таблица состояний заменена на новую (11 состояний вместо 16)
- [x] ✅ Удалены статусы `duplicate`, `new_version`, `archived`
- [x] ❓ Пайплайн 3 удалён из общей FSM (остаётся в своей документации)

## Файл 2: `pipeline2-indexation.md`

### 5. Вход (триггер)
- [x] ✅ `статусом registry` → `статусом created`
- [x] ✅ `статусе registry` → `статусе created`

### 6. Таймаут pending_index
- [x] ✅ `перехода в registry` → `перехода в created`

### 7. Sequence diagram, FSM, таблица состояний
- [x] ✅ Проверено — упоминаний `registry` как статуса нет, всё чисто.
