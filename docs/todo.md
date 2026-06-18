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

## ✅ Аутентификация service-to-service: переход на сетевую изоляцию — 18.06

- [x] **1. common_api.md** — раздел переписан на сетевую изоляцию Docker-сети
- [x] **2. service API (10 файлов)** — разделы обновлены
- [x] **3. auth_service_api.md** — обновлён раздел + заметка у POST /internal/auth/validate
- [x] **4. registry_service_api.md** — убрана ссылка на сертификаты из PATCH /status
- [x] **5. deployment.md** — удалён раздел конфигурации сертификатов
- [x] **6. README.md** — обновлён чейнджлог
- [x] **7. 5.docs_action_plan_17_06.md** — обновлены P0-5, P3-2
- [x] **8. audit_06_06_2026.md** — обновлены таблицы уязвимостей и рекомендаций
- [x] **9. specificity.md** — обновлено S10
- [x] **10. todo.md** — обновлён (этот файл)
- [x] **11. service_dependencies.md** — обновлены связанные документы
- [x] ✅ Финальная проверка: все упоминания удалены

---

## P0 — Блокирующее

- [x] ✅ P0-1: Формула `title_hash_sha256` в `db_diagrams.md` уже соответствует 6-польной из glossary.md (18.06)
- [x] ✅ P0-2: `document_id` в примерах query_service_api.md уже bigint (18.06)
- [x] ✅ P0-3: Неатомарность `check-uniqueness` — решена через `INSERT ... ON CONFLICT`. Описано в `registry_service_api.md` (18.06)
- [x] ✅ P0-4: Описать резолвер `document_references.is_resolved` — создан `registry_resolver_spec.md`
- [x] ✅ P0-5: Добавить service-to-service аутентификацию во все internal API — разделы добавлены
- [x] ✅ P0-6: Описать защиту PATCH /registry/documents/{id}/status — сетевая изоляция описана

- [x] ✅ P1-22: Упоминания `pipeline.drafts` остались только в исторических записях (audit specificity) — корректно (18.06)

## P2 — DDL/схема (миграции)

- [x] ✅ P2-1: CHECK/ENUM — добавлены (18.06)
- [x] ✅ P2-2: CHAR(64) — уже было (18.06)
- [x] ✅ P2-3: UNIQUE — `title_hash_sha256` добавлен (18.06)
- [x] ✅ P2-4: ON DELETE/ON UPDATE — CASCADE/SET NULL проставлены (18.06)
- [x] ✅ P2-5: Soft-delete — `deleted_at` уже был (18.06)
- [x] ✅ P2-6: Индексы — добавлены (18.06)
- [x] ✅ P2-7: CHECK на положительность — добавлены (18.06)
- [x] ✅ P2-8: CHECK на коды классификаторов — добавлены (18.06)
- [x] ✅ P2-9: Триггер синхронизации — описан (18.06)
- [x] ✅ P2-10: Нейминг — конвенция зафиксирована (18.06)


## P3 — Безопасность

- [x] ✅ P3-3: IDOR — rate-limit и audit описаны в `common_api.md` §«Защита от IDOR» (18.06)
- [x] ✅ P3-5: Поглощён P12-3 — security-предупреждения в `quality.notifications[]` с `category: security` (18.06)
- [x] ✅ P3-6: Lama Parser — риск для конфиденциальных документов — описан в `parsing_specifications.md` §6
- [x] ✅ P12-3 / P3-5: `quality.warnings[]` + `quality.issues[]` схлопнуты в единый `quality.notifications[]` с `category: security | quality`. БД-таблица `pipeline.draft_notifications`. (18.06)

## P4 — RAG-методики

- [x] ✅ P4-3: Актуализировать модели (Qwen3-Embedding, int8) — сделано через P13-1 (18.06)
- [x] ✅ P4-6: Зафиксировать итоговую конфигурацию — сделано через P13-1 (18.06)
- [x] ✅ P4-8: Постобработка LLM — валидация цитирования. **Решение**: LLM обязана включать `[source:N]` после каждого абзаца, отсутствие → регенерация. Описано в `pipeline3-search.md` (18.06)

## P5 — Спецификации и глоссарий

- [x] ✅ P5-1: Покрыто P0-1 (дубликат удалён)
- [x] ✅ P5-2: термин «артефакт» в глоссарии заменён (подтверждено D62) (18.06)
- [x] ✅ P5-3: Добавить preview_not_supported в глоссарий — присутствует
- [ ] 🟡 P5-4: Обновить parsing_specifications.md
- [ ] 🟡 P5-5: Обновить `purgatory_scenario.md` — синхронизировать сценарии с актуальной статусной моделью и API
- [x] ✅ P5-7: Добавить seed с mks_oks_code: 47.020 — примеры в normalizer_specification.md
- [ ] 🔵 P5-8: Добавить нормализатор doc_code в normalizer_specification.md
- [x] ✅ P5-9: Синхронизировать cas_storage_specification.md с решением 08.06
- [x] ✅ P5-10: Создать registry_resolver_spec.md — файл создан

## P6 — README и навигация

- [x] ✅ P6-1: README сверено с реальным деревом файлов (+ `architecture/`, `guide.md`, `pipelines/todo.md`, вычищены дубликаты) (18.06)
- [ ] 🔵 P6-4: Добавить секцию «Open Questions»

## P8 — Сверка со СВОДНЫМ ПЛАНОМ (04.06)

- [x] ✅ P8-1: Добавить решение document_id = bigint (sequence) в specificity.md — присутствует
- [x] ✅ P8-2: Добавить решение bbox (px vs [0,1]) в specificity.md — присутствует
- [x] ✅ P8-3: Описать end-to-end FSM approve/reprocess — описана в overview.md:353-395
- [x] ✅ P8-4: Описать Scheduler Pipeline 2 — описан в pipeline2-indexation.md (триггер 15 мин, advisory lock, таймаут 1ч)
- [x] ✅ P8-5: Редакции — не в MVP (зафиксировано в решениях 16.06)
- [x] ✅ P8-6: Создать docs/deployment.md — файл создан (`docs/specifications/deployment.md`)
- [x] ✅ P8-7: Нагрузочное тестирование — методика в rag_evaluation_methodology.md
- [x] ✅ P8-8: Перенести SigNoz в описание мониторинга — создан `docs/architecture/monitoring.md`
- [x] ✅ P8-9: Демо-стенд — частично в sprint2_11_06_17_06.md

- [x] ✅ P8-11: RRP-алгоритм — частично в rag_experiments_methodology.md

## P9 — Зависимости сервисов

- [x] ✅ P9-1: Создать docs/architecture/service_dependencies.md — файл создан

- [x] ✅ P9-3: mock-роутер Gateway описан в `service_dependencies.md` §3 (18.06)

## P10 — Справочник ПКБ

- [x] ✅ P10-1: Восстановить кодировку справочника ПКБ — UTF-8 версия создана, legacy сохранён
- [x] ✅ P10-2: Перенести таблицу в CSV — pkb_domains_classifier.csv создан
- [x] ✅ P10-3: Добавить ссылку в glossary.md — раздел «Справочник ПКБ» присутствует
