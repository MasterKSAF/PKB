# Todo — Актуальные задачи по `docs/`

> Сформирован 17.06.2026 по итогам аудитов (06.06), обсуждений (25.05–16.06), спринт-планов и сверки файлов.
> Полный план: [`docs_plans/plans/4.docs_action_plan_17_06.md`](../docs_plans/plans/4.docs_action_plan_17_06.md)

**Легенда:** 🔴 блокирующе / 🟠 серьёзно / 🟡 важно / 🔵 средне / ⚪ косметика / ✅ сделано

---

## ✅ Выполнено ранее (до 17.06)

- [x] C1: `db_diagrams.md` — типы секций (type → text + список)
- [x] C2: `converter_validator_service_api.md` — удалён `document_id` из JSON-примера
- [x] C3: `orchestrator_service_api.md` — убран `version_id` из `POST /drafts`
- [x] C4: `orchestrator_service_api.md` + `common_api.md` — удалён `POST /documents/{doc_id}/approve`
- [x] C5: `query_service_api.md` + `rag_search_service_api.md` — добавлен `confidence` в `sources[]`
- [x] C6: `db_diagrams.md` — CHECK для `chat.messages.status`
- [x] C7: `overview.md` — маппинг статусной модели (DB/Task/UI)
- [x] C8: `common_api.md` — RBAC-матрица обновлена
- [x] Этап 8: Статусная модель упрощена до `created → pending_index → indexing → indexed / failed`
- [x] Статусы `duplicate`, `new_version`, `archived` удалены из FSM документа
- [x] FSM Pipeline 1: `uploaded → previewing → ready_for_approve → approved → created`
- [x] `registry.drafts` — таблица создана (не `pipeline.drafts`)
- [x] `pipeline.tasks` + `pipeline.task_steps` — в схеме БД
- [x] `auth.users` — таблица в схеме БД
- [x] `registry.terminology` — таблица в схеме БД
- [x] `current_version_id` в `registry.documents` — добавлен
- [x] `registry.categories` + `registry.document_categories` (M:N) — созданы
- [x] Все ID — `bigint (sequence)` (task_id, session_id, message_id, document_id, version_id, project_id, draft_id)
- [x] `bbox` — разделён: px в raw_ocr_v4, [0,1] в validated_v3
- [x] RAG Builder: `sections[].section_id` (не `[]`id`)
- [x] Схлопывание `/parser/preview` + `/parser/process` в единый `POST /{parser|ocr}/process` с `mode`

## P0 — Блокирующее

- [ ] 🔴 P0-1: Исправить формулу `title_hash_sha256` в `db_diagrams.md` (строки 301, 388) — привести к 6-польной формуле из glossary.md
- [ ] 🔴 P0-2: Привести `document_id` в примерах query_service_api.md к bigint
- [ ] 🔴 P0-3: Решить неатомарность `check-uniqueness` (LP-C3)
- [ ] 🔴 P0-4: Описать резолвер `document_references.is_resolved` (A37)
- [ ] 🔴 P0-5: Добавить service-to-service аутентификацию во все internal API
- [ ] 🔴 P0-6: Описать защиту `PATCH /registry/documents/{id}/status`

## P1 — Серьёзное (интеграция)

- [ ] 🟠 P1-1: Аудит RAG Search / Auth Service (B7a)
- [ ] 🟠 P1-2: Восстановить `search`, `checks`, `registry` в RBAC
- [ ] 🟠 P1-3: Подключить drafts через Gateway (не mock)
- [ ] 🟠 P1-4: Реализовать longpoll на сообщение чата
- [ ] 🟠 P1-5: Разделить demo/prod в Gateway
- [ ] 🟠 P1-6: POST /chat/sessions — принимать document_ids, options, project_id
- [ ] 🟠 P1-7: Подключить chat/history/export (stream, не локальный CSV)
- [ ] 🟠 P1-8: Использовать Registry API для классификаторов/терминологии в UI
- [ ] 🟠 P1-9: Добавить раздел «Артефакты» в админку
- [ ] 🟠 P1-10: Исправить кнопку «Повторить OCR» (reprocess по выбранному)
- [ ] 🟠 P1-11: Удалить/legacy DocumentRegistry.tsx
- [ ] 🟠 P1-12: Описать отдельную таблицу ролей GET /admin/roles
- [ ] 🟠 P1-13: Карточка документа: detail/status/history/errors
- [ ] 🟠 P1-14: Добавить таймаут pending (30 с) в Pipeline 3
- [ ] 🟠 P1-16: Удалить/описать partially_indexed
- [ ] 🟠 P1-17: Описать `indexed -> failed : Integrity check failed`
- [ ] 🟠 P1-18: Устранить противоречие в компенсации Pipeline 2
- [ ] 🟠 P1-19: Описать повторный запуск preview (idempotency/409)
- [ ] 🟠 P1-20: Добавить триггер `review_required -> validation`
- [ ] 🟠 P1-21: Описать `current_version_id` в registry.documents
- [ ] 🟠 P1-22: Связь `pipeline.drafts ↔ registry.drafts`

## P2 — DDL/схема (миграции)

- [ ] 🟡 P2-1: CHECK/ENUM на source_type, document_type, era, validity_status, jurisdiction, processing_status
- [ ] 🟡 P2-2: file_hash_sha256, title_hash_sha256 -> CHAR(64)
- [ ] 🟡 P2-3: UNIQUE-ограничения на бизнес-ключи
- [ ] 🟡 P2-4: ON DELETE/ON UPDATE для всех FK
- [ ] 🟡 P2-5: Soft-delete (deleted_at)
- [ ] 🟡 P2-6: Дополнительные индексы
- [ ] 🟡 P2-7: CHECK на положительность счётчиков
- [ ] 🟡 P2-8: CHECK на mks_oks_code/okstu_code в classifier_registry
- [ ] 🟡 P2-9: Триггер синхронизации document_chunks.document_id
- [ ] 🟡 P2-10: Унифицировать нейминг (timestamps, status, FK)
- [ ] 🟡 P2-11: Создать ddl_migrations.md со скриптами

## P3 — Безопасность

- [ ] 🟠 P3-1: Rate limiting (реализовать или убрать 429 из docs)
- [ ] 🟠 P3-2: mTLS для Gateway ↔ Auth
- [ ] 🟠 P3-3: IDOR — примечания о rate-limit и audit
- [ ] 🟠 P3-4: Чувствительные данные — запретить в URL
- [ ] 🟠 P3-5: PDF-security — поле warnings[] в Parser/OCR
- [ ] 🟡 P3-6: Lama Parser — риск для конфиденциальных документов

## P4 — RAG-методики

- [ ] 🟡 P4-1: Создать docs/plans/quality_report_sprint2.md
- [ ] 🟡 P4-2: Перенести RAG-методики в docs/methodology/
- [ ] 🟡 P4-3: Актуализировать модели (Qwen3-Embedding, int8)
- [ ] 🟡 P4-4: Зафиксировать 9 стратегий поиска (S1–S9)
- [ ] 🟡 P4-5: Описать таймауты и метрики производительности
- [ ] 🟡 P4-6: Зафиксировать итоговую конфигурацию
- [ ] 🟡 P4-7: Протокол проверки значимости
- [ ] 🟡 P4-8: Постобработка LLM — валидация цитирования
- [ ] 🔵 P4-9: Смена модели эмбеддингов (ALTER TABLE)
- [ ] 🔵 P4-10: Repromote/переиндексация

## P5 — Спецификации и глоссарий

- [x] ✅ P5-1: Покрыто P0-1 (дубликат удалён)
- [ ] ⚪ P5-2: «артефакт» -> «результат обработки» в глоссарии
- [ ] 🟡 P5-3: Добавить preview_not_supported в глоссарий
- [ ] 🟡 P5-4: Обновить parsing_specifications.md
- [ ] 🟡 P5-5: Обновить purgatory_scenario.md
- [ ] ⚪ P5-6: Добавить плашку «исторический» в pipeline1-formation_discussion.md
- [ ] 🟡 P5-7: Добавить seed с mks_oks_code: 47.020
- [ ] 🔵 P5-8: Добавить нормализатор doc_code в normalizer_specification.md
- [ ] 🟡 P5-9: Синхронизировать cas_storage_specification.md с решением 08.06
- [ ] 🔵 P5-10: Создать registry_resolver_spec.md

## P6 — README и навигация

- [ ] 🟡 P6-1: Сверить README с реальным деревом файлов
- [ ] 🟡 P6-2: Синхронизировать «Загрузку документа» с docs_ui.md
- [ ] 🟡 P6-3: Синхронизировать «Базу знаний» с docs_ui.md
- [ ] 🔵 P6-4: Добавить секцию «Open Questions»
- [ ] 🔵 P6-5: Создать CHANGELOG.md
- [ ] 🔵 P6-6: Перенести docs_ui*.md в docs/ui/

## P7 — Аудит и архив

- [ ] 🟡 P7-1: Обновлён (этот файл)
- [ ] 🔵 P7-2: Перенести аудиты в docs/audit/
- [ ] ⚪ P7-3: Перекодировать имена обсуждений в UTF-8
- [ ] ⚪ P7-4: Переименовать обсуждения в семантические
- [ ] ⚪ P7-5: Удалить дубль ui-final-... (28 КБ)
- [ ] 🔵 P7-6: Создать README.md с индексом встреч
- [ ] 🔵 P7-7: Добавить front-matter в обсуждения
- [ ] 🔵 P7-8: Добавить cross-references обсуждений ↔ specificity.md
- [ ] 🟡 P7-9: Запустить повторный аудит по check_rule.md
- [ ] 🔵 P7-10: Актуализировать Excel-статусы сервисов

## P8 — Сверка со СВОДНЫМ ПЛАНОМ (04.06)

- [ ] 🔵 P8-1: Добавить решение document_id = bigint (sequence) в specificity.md
- [ ] 🔵 P8-2: Добавить решение bbox (px vs [0,1]) в specificity.md
- [ ] 🟡 P8-3: Описать end-to-end FSM approve/reprocess (частично — decide описан в pipeline1-formation_detail.md:444)
- [ ] 🟡 P8-4: Описать Scheduler Pipeline 2
- [x] ✅ P8-5: Редакции — не в MVP (зафиксировано в решениях 16.06)
- [ ] 🔵 P8-6: Создать docs/deployment.md
- [x] ✅ P8-7: Нагрузочное тестирование — методика в rag_evaluation_methodology.md
- [ ] 🟡 P8-8: Перенести SigNoz в описание мониторинга
- [x] ✅ P8-9: Демо-стенд — частично в sprint2_11_06_17_06.md
- [ ] 🟡 P8-10: Дождаться примеров семейств от Семёна для конвертера
- [x] ✅ P8-11: RRP-алгоритм — частично в rag_experiments_methodology.md

## P9 — Зависимости сервисов

- [ ] 🔵 P9-1: Создать docs/architecture/service_dependencies.md
- [ ] 🟡 P9-2: Добавить email-validator в requirements.txt
- [ ] 🔵 P9-3: Описать mock-роутер Gateway

## P10 — Справочник ПКБ

- [ ] 🔵 P10-1: Восстановить кодировку справочника ПКБ
- [ ] 🔵 P10-2: Перенести таблицу в CSV
- [ ] 🔵 P10-3: Добавить ссылку в glossary.md
