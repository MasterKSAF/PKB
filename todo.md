# Реструктуризация docs/ и docs_plans/

## Анализ проблем
- ~~Корневой README.md не отражает реальную структуру (нет docs_plans/, есть phantom-ссылки)~~
- ~~Дублирование: `docs_plans/features/rag_evaluation_methodology.md` = `docs_plans/methodology/rag_evaluation_methodology.md` (версии различаются)~~
- ~~`docs/` содержит служебные файлы (todo.md, 6.dev_tasks_17_06.md, opencode.json), не относящиеся к документированию системы~~
- ~~`docs/opencode.json` — конфигурация, не место в документации~~
- ~~В корневом README.md ссылки на несуществующие пути (`docs/plans/`, `docs/rules/`, `docs_discussions/`)~~

## План

### 1. Устранить дублирование методологий
- [x] 1.1. Сверить `docs_plans/features/rag_evaluation_methodology.md` vs `docs_plans/methodology/rag_evaluation_methodology.md` — версии разные
- [x] 1.2. Удалить `docs_plans/features/rag_evaluation_methodology.md` (устаревшая версия)
- [x] 1.3. Удалить `docs_plans/features/rag_experiments_methodology.md` (устаревшая версия)
- [x] 1.4. Обновить `docs_plans/features/readme.md` — исправить ссылки на методологии

### 2. Переместить служебные файлы из docs/
- [x] 2.1. `docs/todo.md` → корень проекта (служебный файл агента)
- [x] 2.2. `docs/6.dev_tasks_17_06.md` → `docs_plans/plans/` (план задач по сервисам)
- [x] 2.3. `docs/opencode.json` → корень проекта (конфигурация, не в git)

### 3. Обновить корневой README.md
- [x] 3.1. Исправить структуру проекта — отразить реальные папки: docs/, docs_plans/, убрать несуществующие
- [x] 3.2. Исправить ссылки в «Быстрый старт» на актуальные пути

### 4. Проверить перекрёстные ссылки
- [x] 4.1. Исправлены ссылки в 10 файлах (docs/README.md, rag_builder_service_api.md, rag_search_service_api.md, glossary.md, specificity.md, audit_06_06_2026.md, audit_logic_schema_report.md, sprint1.md, sprint2.md, 5.docs_action_plan_17_06.md)

### 5. Финальный обзор
- [x] 5.1. Сверка с todo.md — все пункты выполнены
- [x] 5.2. Перепросмотр правок — случайных затираний нет, все замены целевые
- [ ] 5.3. ~~Оценка целостности~~ (перенесено в финальный ответ)
- [ ] 5.4. ~~Закоммитить~~ (ожидает подтверждения пользователя)

### 6. Переклассификация в 6.dev_tasks_17_06.md (задачи разработчикам)
- [x] 6.1. **CM-6** — убрать `+ service_checker` (отдельный сервис, не Common API)
- [x] 6.2. **QS-10** — удалить (RBAC + Idempotency-Key → Gateway)
- [x] 6.3. **RG-12** — удалить (RBAC-матрица → Gateway)
- [x] 6.4. **Gateway** — добавить GW-17 (RBAC), GW-18 (Idempotency-Key /chat), GW-19 (IDOR audit)
- [x] 6.5. **Service Checker** — новый раздел 6 (SC-1, SC-2), перенумеровать разделы 6→7, 7→8, …, 12→13
- [x] 6.6. Обновить заголовки пайплайнов (11.1→12.1, 11.2→12.2, 11.3→12.3)
- [x] 6.7. Добавить Service Checker в матрицу ответственных
