# Todo: удаление SQL-триггеров из описания, логика — в сервисы

**Задача:** Убрать реальные SQL-триггеры из документации БД. Их логику реализовать на уровне сервисов (приложения).

- [x] 1. `docs/database/ddl_migrations_17_06.md` — P2-9: убрать триггер `sync_chunk_document_id`
- [x] 2. `docs/database/ddl_migrations_17_06.md` — P2-8: убрать фразу "заменить триггером"
- [x] 3. `docs/database/ddl_migrations_17_06.md` — Порядок применения: убрать "заменить триггером"
- [x] 4. `docs/database/db_diagrams.md` — P2-9: убрать триггер синхронизации, переписать на valid_from/valid_until/indexing_txn_id
- [x] 5. `docs/database/db_diagrams.md` — Примечание 6: синхронизация через приложение вместо триггера
- [x] 6. `docs/6.dev_tasks_17_06.md` — DB-10: "Триггер" → "Логика в RAG Builder"
- [x] 7. `docs/specificity.md` — A20: обновить статус (решено: проставляет RAG Builder)
- [x] 8. `docs/api/registry_service_api.md` — примечание 4: убрать "триггером БД"
