# План работ: оценка и исправление документации — ВЫПОЛНЕНО

## Задачи

### 1. Удалить/добавить ссылки из структуры README.md ✅
- [x] 1.1 Убрать `plans/` из структуры (директория не существует)
- [x] 1.2 Убрать `database/db_audit_report.md` из структуры (файл не существует)
- [x] 1.3 Добавить `audit/` в структуру (директория существует, но не отражена)

### 2. Исправить конфликт RBAC в common_api.md ✅
- [x] Строки 356 и 368 — `GET /tasks/{task_id}/status` приведён к `system_admin only`

### 3. Унификация формулы title_hash_sha256 (X2) ✅
- [x] Формула: `doc_code + title + era`
- [x] overview.md и db_diagrams.md синхронизированы

### 4. X1 — document_id назначается Registry ✅
- [x] overview.md исправлен, specificity.md — X1 закрыт

### 5. Закрыть вопросы из specificity.md ✅
- [x] X3 — `partially_indexed` удалён (нестатус)
- [x] X6 — `current_version_id` добавлен в `registry.documents`
- [x] X8 — `amendments` оставлены в JSONB (осознанное)
- [x] A17 — таблицы `auth.users`, `registry.terminology` добавлены в ER-диаграмму

### 6. Исправить README.md строка 151 — битый путь ✅
- [x] Удалена битая ссылка

### 7. Исправить README.md строка 198 — блок curl ✅
- [x] Закрывающие backticks добавлены
