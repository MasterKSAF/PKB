# TODO: Обновление документации согласно Спринту 1 (04.06 – 10.06)

> **Основание**: `docs/plans/sprint1_04_06_10_06.md` (задача 1.5), `docs/plans/СВОДНЫЙ_ПЛАН_РЕАЛИЗАЦИИ.md`, `docs/plans/итоги общей встречи 03.06.26.md`, `docs_discussions/plans/3.04_06_26.md`, `docs/specificity.md`.
> **Цель**: привести всю документацию (`docs/api/*`, `docs/schema/*`, `docs/database/*`, `docs/pipelines/*`, `docs/glossary.md`, `docs/plans/*`) в соответствие с архитектурными решениями Спринта 1.
> **Дедлайн**: 10.06.2026 (к чек-листу приёмки).
> **Статус**: ✅ **ЗАВЕРШЕНО** 05.06.2026 — все этапы выполнены.

---

## Этап 0. Аудит текущего состояния документации

- [x] **0.1.** Проверить, что уже исправлено по `docs_discussions/plans/3.04_06_26.md` (план bigint+bbox) — сверить по факту в файлах
- [x] **0.2.** Выявить оставшиеся расхождения между документацией и планом (`specificity.md` A1–A10)
- [x] **0.3.** Зафиксировать новые требования из `sprint1_04_06_10_06.md`, которые ещё не отражены в документации

---

## Этап 1. Синхронизация схем БД (`docs/database/db_diagrams.md`)

- [x] **1.1.** Проверить все FK в ER-диаграмме на bigint — ✅ уже bigint; нумерация разделов исправлена (дубль «8» → «9»)
- [x] **1.2.** Таблица `chat.projects` — ✅ присутствует
- [x] **1.3.** Поле `project_id` в `chat.sessions` — ✅ присутствует
- [x] **1.4.** Примечание п.8 (теперь п.9) — ✅ `document_id` и `task_id` описаны как bigint
- [x] **1.5.** `document_type` в `registry.documents` — ✅ присутствует

---

## Этап 2. Актуализация API-спецификаций (`docs/api/*`)

- [x] **2.1–2.3.** `common_api.md` — ✅ bigint ID, bbox [0,1], RBAC проверены
- [x] **2.4–2.6.** `orchestrator_service_api.md` — ✅ примеры проверены, approve/reprocess — TBD до 10.06
- [x] **2.7–2.9.** `registry_service_api.md` — ✅ bigint в примерах, `document_type`, UUID в моделях БД заменены на bigint
- [x] **2.10–2.11.** `rag_builder_service_api.md`, `rag_search_service_api.md` — ✅ bigint document_id
- [x] **2.12–2.13.** `query_service_api.md` — ✅ session_id/message_id bigint, project_id добавлен
- [x] **2.14–2.16.** `converter_validator_service_api.md`, `parser_service_api.md`, `ocr_service_api.md` — ✅ bigint task_id, bbox px исправлен
- [x] **2.17.** TODO аудита: `sort_by`/`order`, `top_k ∈ [1,100]`, `source_type` vs `document_type` — ✅ верифицированы

---

## Этап 3. Актуализация JSON-схем (`docs/schema/*`)

- [x] **3.1.** `schema_parser_result.json` — ✅ task_id=420000, bbox пиксели (корректны для сырого OCR)
- [x] **3.2.** `schema_converter_result.json` — ✅ task_id=420000, bbox нормированный
- [x] **3.3.** `schema_registry_for_rag.json` — ✅ все document_id="a1b2c3d4-..." → 420000 (16 вхождений)
- [x] **3.4.** `schema_parser_preview.json` — ✅ task_id=420000
- [x] **3.5.** `diagrams.md` — ✅ raw_ocr_v2 → raw_ocr_v4

---

## Этап 4. Актуализация пайплайнов (`docs/pipelines/*`)

- [x] **4.1.** `pipeline1-formation.md` — ✅ маппинг проверен
- [x] **4.2.** `pipeline1-formation.md` — ✅ черновики уже описаны, ссылка на `drafts_storage_plan.md`
- [x] **4.3.** `pipeline1-formation_detail.md` — ✅ UUID → bigint в описании field mapping
- [x] **4.4–4.6.** Остальные пайплайны — ✅ document_id, session_id bigint

---

## Этап 5. Актуализация глоссария (`docs/glossary.md`)

- [x] **5.1.** Идентификаторы — ✅ все BIGINT
- [x] **5.2.** Добавлены `comparison_id` и `batch_id` (TBD)
- [x] **5.3.** Добавлен термин «Проект (project)»
- [x] **5.4.** bbox — ✅ описан для обоих форматов (px / [0,1])
- [x] **5.5.** Черновик — ✅ уже был, дополнен

---

## Этап 6. Актуализация навигации (`docs/README.md` и `README.md` в корне)

- [x] **6.1.** «Последние изменения» — ✅ исправлены битые ссылки, добавлена запись о синхронизации
- [x] **6.2.** Структура — ✅ `docs_discussions/` убран из дерева, добавлена ссылка-примечание
- [x] **6.3.** Mermaid-диаграмма — ✅ без изменений (bigint не влияет на архитектуру)
- [x] **6.4.** Описания сервисов — ✅ QueryService (project_id), Orchestrator (drafts)
- [x] **6.5.** Корневой README — ✅ ссылки актуальны

---

## Этап 7. Открытые вопросы → документация

- [x] **7.1.** `comparison_id`/`batch_id` — ✅ добавлены в glossary.md (TBD до 10.06)
- [x] **7.2.** `approve`/`reprocess` — ⏳ ожидается решение до 10.06 (помечено TBD)
- [x] **7.3.** `raw_ocr_v4` — ✅ унифицировано, sprint plan вопрос 4.3 закрыт
- [x] **7.4.** RBAC — ⏳ ожидается согласование до 10.06
- [x] **7.5.** Пользовательские категории — ✅ архитектура зафиксирована, реализация → Спринт 2

---

## Этап 8. Актуализация `specificity.md`

- [x] **8.1.** A1 — ✅ db_diagrams закрыто
- [x] **8.2.** A2 — ✅ bbox описание исправлено (px в OCR/Parser, [0,1] в Converter)
- [x] **8.3.** A3 — ✅ raw_ocr_v4 унифицировано
- [x] **8.4.** A4 — ✅ comparison_id/batch_id добавлены в glossary
- [x] **8.5.** A7 — ✅ Проект добавлен
- [x] **8.6.** A12, A13, A14 — ✅ добавлены и закрыты

---

## Этап 9. Финальная проверка и чек-лист приёмки

- [x] **9.1.** Чек-лист спринта §5:
  - [x] Документация синхронизирована с кодом (нет расхождений типов ID и bbox)
  - [ ] Определены `comparison_id` / `batch_id` или принято решение об их удалении — ⏳ до 10.06
  - [ ] Схема `approve`/`reprocess` описана и согласована — ⏳ до 10.06
- [x] **9.2.** Перекрёстная проверка: ✅ 0 UUID в JSON-примерах, 0 bbox px (кроме OCR/Parser)
- [x] **9.3.** Перекрёстная проверка: ✅ raw_ocr_v2 заменён, task_id строковый исправлен
- [x] **9.4.** Целостность ссылок: ✅ битые ссылки исправлены (A14)
- [x] **9.5.** `docs/README.md` «Последние изменения» обновлён
- [x] **9.6.** `todo.md` сверен — выполнено
- [x] **9.7.** `specificity.md` обновлён

---

## Итого: что выполнено, что осталось

### ✅ Выполнено (05.06.2026)

| Файл | Изменения |
|------|-----------|
| `docs/database/db_diagrams.md` | Дубль нумерации исправлен (8→9) |
| `docs/api/ocr_service_api.md` | `version_id` → bigint, `bbox` единицы: мм→px, запятая восстановлена |
| `docs/api/parser_service_api.md` | `version_id` → bigint, `bbox` единицы: мм→px, запятая восстановлена |
| `docs/api/registry_service_api.md` | `bbox` в footnotes → [0,1]; `successor_doc_id`/`predecessor_doc_id` → bigint; `document.id` → bigint; все uuid в моделях БД → bigint |
| `docs/schema/schema_converter_result.json` | `task_id` → 420000 (число) |
| `docs/schema/schema_parser_preview.json` | `task_id` → 420000 (число) |
| `docs/schema/schema_registry_for_rag.json` | Все `document_id`="a1b2c3d4-..." → 420000 (16 вхождений) |
| `docs/schema/diagrams.md` | `raw_ocr_v2` → `raw_ocr_v4` |
| `docs/pipelines/pipeline1-formation_detail.md` | "UUID" → "bigint ID" в маппинге |
| `docs/glossary.md` | Добавлены `comparison_id`, `batch_id` (TBD); термин «Проект»; восстановлен `message_id` |
| `docs/README.md` | `docs_discussions/` убран из дерева; исправлены битые ссылки; добавлена запись о синхронизации |
| `docs/plans/sprint1_04_06_10_06.md` | Вопрос 4.3 (raw_ocr_v2/v4) закрыт |
| `docs/specificity.md` | A1–A14 актуализированы, история решений дополнена |
| `todo.md` | Этот файл — актуализирован |

### ⏳ Ожидается решение до 10.06

- `comparison_id` / `batch_id` — определение или решение об удалении
- Схема `approve` / `reprocess` (end-to-end FSM)
- RBAC: финальная модель прав
