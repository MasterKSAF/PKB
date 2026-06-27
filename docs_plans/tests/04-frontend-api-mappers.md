# Frontend — API mappers (http.ts)

**Директория:** `UI-UX/UI Final/frontend/src/utils/__tests__/` (создать новую)

---

## 1. `__tests__/http-auth.test.ts` (~200 строк)

Функции аутентификации.

**Сценарии:**
- `authApi.login()` — успех: отправляет username/password, получает access_token + refresh_token
- `authApi.login()` — 401: вызов с неверными данными → исключение
- `authApi.me()` — валидный токен: возвращает profile c user_id, full_name, permissions
- `authApi.me()` — без токена: 401
- `authApi.refresh()` — валидный refresh: новый access_token
- `authApi.refresh()` — истёкший refresh: 401
- `authApi.logout()` — revoke refresh_token
- `getAccessToken()` — токен из localStorage
- `getAccessToken()` — нет токена → null
- `setGatewayTokens()` — сохраняет access + refresh + timestamp
- `clearGatewayTokens()` — удаляет все токены
- `syncGatewayCurrentUser()` — запрос /auth/me + сохранение в store
- `refreshGatewayAccessToken()` — обновление через /auth/refresh
- `refreshGatewayTokenOnce()` — предотвращает множественные одновременные refresh
- `ensureGatewayToken()` — свежий токен: возвращает как есть
- `ensureGatewayToken()` — истёк: вызывает refresh
- `ensureGatewayToken()` — нет токена: вызывает login

---

## 2. `__tests__/http-chat.test.ts` (~250 строк)

Chat API.

**Сценарии:**
- `chatApi.sessions()` — GET /chat/sessions → список сессий
- `chatApi.getSession(1)` — GET /chat/sessions/1 → сообщения сессии
- `chatApi.getSession(999)` — не найдена → null/404
- `chatApi.createSession(project_id=1)` — POST /chat/sessions → session_id
- `chatApi.createSession()` — с document_ids
- `chatApi.updateSession(1, {title: "New"})` — PATCH /chat/sessions/1
- `chatApi.updateSession(1, {title: "", document_ids: [1,2]})` — обновление полей
- `chatApi.deleteSession(1)` — DELETE /chat/sessions/1
- `chatApi.exportSession(1)` — GET /chat/sessions/1/export → CSV
- `chatApi.exportSession(1)` — GET /chat/sessions/1/export?format=json
- `chatApi.send(1, "text")` — POST /chat/send → long-poll ответ
- `chatApi.send(1, "text")` — 404 stale session → create новый + retry
- `chatApi.send(1, "")` — пустой текст → ошибка
- `mapGatewayChatResponse()` — answered: content + citations
- `mapGatewayChatResponse()` — answered: limitation поле
- `mapGatewayChatResponse()` — pending/failed: без content
- `mapGatewayChatResponse()` — сообщение с источниками (directSources + itemSources)
- `isFinalChatStatus("answered")` → true
- `isFinalChatStatus("failed")` → true
- `isFinalChatStatus("pending")` → false
- `isFinalChatStatus("generating")` → false
- `chatLongpollIncompleteMessage()` — формат сообщения для long-poll
- `waitForGatewayChatMessage()` — опрос до answered
- `waitForGatewayChatMessage()` — опрос до failed
- `mapGatewaySessionMessages()` — преобразование сообщений сессии
- `mapGatewaySessionsToProjects()` — группировка сессий по проектам
- `mapGatewayProject()` — преобразование проекта
- `mapGatewayProjectsResponse()` — список проектов

---

## 3. `__tests__/http-projects.test.ts` (~120 строк)

Projects API.

**Сценарии:**
- `projectsApi.list()` — GET /chat/projects + GET /chat/sessions → объединённый список
- `projectsApi.list()` — с пустым проектами: только сессии
- `projectsApi.list()` — с пустыми сессиями: только проекты
- `projectsApi.create({name: "Project"})` — POST /chat/projects → project_id
- `projectsApi.create({name: "", code: "P-001"})` — с code
- `projectsApi.update(1, {name: "New"})` — PATCH /chat/projects/1
- `projectsApi.delete(1)` — DELETE /chat/projects/1
- `mergeGatewayProjectsWithSessions()` — корректное слияние
- `mergeGatewayProjectsWithSessions()` — проект без session_id → chats=[]
- `normalizeGatewayProjectId()` — преобразование id
- `createGatewayProjectCode()` — генерация code из id

---

## 4. `__tests__/http-drafts.test.ts` (~200 строк)

Drafts API.

**Сценарии:**
- `draftsApi.create(file, metadata)` — POST /drafts multipart → 202 c draft_id + task_id
- `draftsApi.create()` — calculateFileSha256 в form
- `draftsApi.create()` — Idempotency-Key заголовок
- `draftsApi.list()` — GET /drafts → список
- `draftsApi.list({document_key:"xxx", status:"uploaded", page:1, page_size:10})` — фильтры
- `draftsApi.get(1)` — GET /drafts/1 → детали
- `draftsApi.getPreview(1)` — GET /drafts/1
- `draftsApi.startPreview(1)` — POST /drafts/1/preview → 202
- `draftsApi.waitPreview(1)` — GET /drafts/1/preview/status → completed
- `draftsApi.waitPreview(1, timeout=30)` — с таймаутом
- `draftsApi.updateMetadata(1, {title: "New"})` — PATCH /drafts/1/metadata
- `draftsApi.decide(1, "approve", {comment: "OK"})` — PATCH /drafts/1/decide
- `draftsApi.decide(1, "reject", {comment: "Fix it"})` — с metadata_overrides
- `draftsApi.delete(1)` — DELETE /drafts/1
- `mapGatewayDraftRecord()` — полное преобразование draft record
- `normalizeDraftStatus()` — все статусы
- `normalizePreviewMetadata()` — preview_metadata из API

---

## 5. `__tests__/http-documents.test.ts` (~250 строк)

Documents API.

**Сценарии:**
- `documentsApi.list()` — GET /documents → items + summary
- `documentsApi.get(1)` — GET /documents/1 → детали
- `documentsApi.status(1)` — GET /documents/1/status
- `documentsApi.history(1)` — GET /documents/1/history
- `documentsApi.errors(1)` — GET /documents/1/errors
- `documentsApi.parameters(1)` — GET /documents/1/parameters
- `documentsApi.pages(1)` — GET /documents/1/pages
- `documentsApi.pagePreview(1, 1)` — GET /documents/1/pages/1/preview
- `documentsApi.file(1)` — GET /documents/1/file → blob
- `documentsApi.queue()` — GET /documents/queue
- `documentsApi.knowledgeSections()` — GET /documents/knowledge-sections
- `documentsApi.upload()` — POST /documents → 410 (deprecated)
- `documentsApi.reprocess(1, {mode:"full"})` — POST /documents/1/reprocess
- `documentsApi.versions(1)` — GET /documents/1/versions
- `documentsApi.updateValidity(1, {valid_from:"...", valid_until:"..."})` — PATCH /documents/1
- `documentsApi.archive(1)` — DELETE /documents/1

---

## 6. `__tests__/http-registry.test.ts` (~300 строк)

Registry API (классификаторы + терминология).

**Сценарии классификаторы:**
- `classifiers.list()` — GET /registry/classifiers → paginated
- `classifiers.list({system: "MKS", code: "01", status: "active"})` — фильтры
- `classifiers.tree()` — GET /registry/classifiers/tree
- `classifiers.tree({system: "MKS", root_code: "01", max_depth: 3})` — параметры
- `classifiers.get(1)` — GET /registry/classifiers/1
- `classifiers.get(1, {system: "MKS"})` — с query param
- `classifiers.create({code: "01.020", full_name: "..."})` — POST
- `classifiers.update(1, {full_name: "New"})` — PUT
- `classifiers.patch(1, {full_name: "New"})` — PATCH
- `classifiers.delete(1)` — DELETE
- `classifiers.import(file)` — POST /registry/classifiers/import
- `classifiers.pending()` — GET /registry/classifiers/pending
- `classifiers.pending({system:"MKS", status:"pending"})` — фильтры
- `classifiers.acceptPending(1, {parent_code:"01", full_name:"New"})` — PATCH accept
- `classifiers.rejectPending(1, {admin_comment:"Wrong"})` — PATCH reject
- `classifiers.validate({mks_oks_code:"01", okstu_code:"02", udk_code:"03"})` — POST validate

**Сценарии терминология:**
- `terminology.list()` — GET /registry/terminology
- `terminology.list({raw_term:"bolt", term_type:"abbreviation"})` — фильтры
- `terminology.get(1)` — GET /registry/terminology/1
- `terminology.create({raw_term:"bolt", standard_term:"BOLT"})` — POST
- `terminology.update(1, {standard_term:"BOLT-2"})` — PUT
- `terminology.delete(1)` — DELETE
- `terminology.normalize({raw_term:"bolt"})` — GET/POST normalize
- `terminology.import(file)` — POST /registry/terminology/import

**Сценарии registry:**
- `registryApi.documents()` — GET /registry/documents
- `registryApi.documentSections(1)` — GET /registry/documents/1/sections
- `registryApi.knowledgeSections()` — GET /registry/knowledge-sections
- `registryApi.stats()` — GET /registry/stats
- `registryApi.enums()` — GET /registry/enums

---

## 7. `__tests__/http-mappers-chat.test.ts` (~150 строк)

Мэпперы чата.

**Сценарии:**
- `mapGatewayChatResponse()` — полный ответ с цитатами, источниками, лимитациями
- `mapGatewayChatResponse()` — ответ с двойными источниками (directSources + itemSources)
- `mapGatewayChatResponse()` — сообщение в статусе "pending"
- `mapGatewayChatResponse()` — сообщение в статусе "failed"
- `mapGatewayChatResponse()` — ответ с limitation "out_of_scope"
- `mapGatewaySessionMessages()` — список сообщений из сессии
- `mapGatewaySessionsResponse()` — преобразование сессий
- `mapGatewaySessionsToProjects()` — группировка
- `mapGatewayProject()` — один проект
- `mapGatewayProjectsResponse()` — список проектов

---

## 8. `__tests__/http-mappers-search.test.ts` (~100 строк)

Мэпперы поиска.

**Сценарии:**
- `mapGatewaySearchResponse()` — результаты с полями id, documentId, name, type, version, source, relevance, fragment, page, section, sectionId, group, classifierCode, pagePreviewUrl, documentUrl
- `mapGatewaySearchResponse()` — пустые результаты
- `mapGatewaySearchResponse()` — null поля (page, fragment)
- `mapGatewayKnowledgeSections()` — дерево с rootNodes, children, documents_count
- `mapGatewayKnowledgeSections()` — пустое дерево
- `countClassifierChildren()` — рекурсивный подсчёт
- `flattenClassifierNodes()` — преобразование в плоский список

---

## 9. `__tests__/http-mappers-documents.test.ts` (~180 строк)

Мэпперы документов.

**Сценарии:**
- `mapGatewayDocumentsResponse()` — полный список документов со всеми статусами (ocr, index, validity)
- `mapGatewayDocumentsResponse()` — null значения полей
- `mapGatewayDocumentsResponse()` — пустой список
- `mapGatewayDocumentDetailResponse()` — полная детализация документа
- `mapGatewayDocumentDetailResponse()` — без successor/predecessor
- `mapGatewayHistoryResponse()` — история с сообщениями
- `mapGatewayHistoryResponse()` — история без сообщений
- `mapGatewayDocumentStatus()` — completed статус
- `mapGatewayDocumentStatus()` — parsing/validation/failed
- `mapGatewayDocumentErrors()` — список ошибок
- `mapGatewayDocumentParameters()` — параметры с extraction_confidence
- `mapGatewayDocumentPages()` — страницы с title/lines
- `mapGatewayQueueResponse()` — очередь с progress по статусам
- `mapGatewayQueueResponse()` — пустая очередь

---

## 10. `__tests__/http-mappers-drafts.test.ts` (~150 строк)

Мэпперы черновиков.

**Сценарии:**
- `mapGatewayDraftRecord()` — все поля draft record
- `mapGatewayDraftRecordToUi()` — преобразование Gateway → UI draft
- `draftPatchFromGateway()` — патч обновления
- `mapGatewayPreviewMetadata()` — preview metadata
- `mapGatewayDuplicates()` — список дубликатов с reason/similarity
- `mapGatewayNotifications()` — уведомления с code/severity/category/message
- `normalizeDraftStatusFromGateway()` — все статусы (uploaded, previewing, ready_for_approve, review_required, validation, approved, discarded, failed)
- `pickMetadataSource()` — выбор manual/extracted
- `buildMetadataOverridesFromForm()` — сборка overrides из формы

---

## 11. `__tests__/http-mappers-metrics.test.ts` (~60 строк)

Мэпперы метрик.

**Сценарии:**
- `mapGatewayMetricsResponse()` — контрольные метрики (ocrQuality, retrievalQuality, answersWithSources, manualReviewQueue, searchLatency)
- `mapGatewayMetricsResponse()` — нулевые значения
- `mapGatewayAnswerMetrics()` — ответы (ratedAnswers, usefulRate, flaggedForReview, unresolvedAfterReview, commonSignals)
- `mapGatewayMonitorLogs()` — логи с time/text/level

---

## 12. `__tests__/http-mappers-admin.test.ts` (~120 строк)

Мэпперы администрирования.

**Сценарии:**
- `mapGatewayUsersResponse()` — список пользователей с role/permissions/access/status
- `mapGatewayUsersResponse()` — пользователь без некоторых полей
- `mapGatewayProfileToAdminUser()` — профиль → admin user
- `mapGatewayRolesResponse()` — список ролей
- `mapGatewayRole()` — преобразование роли
- `mapGatewayPermissions()` — permission flags
- `mapGatewayUserStatus()` — статус пользователя
- `mapGatewayAuditResponse()` — события аудита с action/resource/document/stage

---

## 13. `__tests__/http-mappers-registry.test.ts` (~80 строк)

Мэпперы registry.

**Сценарии:**
- `mapRegistryListResponse()` — paginated ответ с data + meta
- `mapRegistryClassifierNode()` — узел классификатора с system/code/full_name/status/children/documents_count
- `mapRegistryClassifierNode()` — null children
- `mapRegistryPendingNode()` — pending узел с id/system/code/found_in_document/suggested_parent
- `mapRegistryTerminologyNode()` — терминология с raw_term/standard_term/synonyms/scope
- `unwrapRegistryObject()` — извлечение data из обёртки

---

## 14. `__tests__/http-helpers.test.ts` (~150 строк)

Вспомогательные функции.

**Сценарии:**
- `calculateFileSha256()` — вычисление SHA-256 для файла
- `deriveDocumentKey()` — генерация document_key
- `normalizeDraftStatus()` — все варианты статусов
- `normalizePreviewMetadata()` — preview data
- `isDemoMode()` — определение demo режима
- `toUiTimestamp()` — форматирование ISO → UI
- `todayIsoDate()` — текущая дата в ISO
- `isNumericDraftId()` — числовой/нечисловой
- `requireNumericDraftId()` — исключение для нечислового
- `needsClarification()` — широкие/неопределённые запросы
- `shouldShowNoKnowledgeResult()` — маркеры no knowledge
- `shouldShowOutOfScopeResult()` — маркеры out of scope
- `mapGatewayStatus()` — статус документа
- `mapGatewayDocumentOcrStatus()` — OCR статус
- `mapGatewayDocumentIndexStatus()` — индекс статус
- `mapGatewaySource()` — источник с id/documentId/section/page/text/version/confidence/urls

---

## 15. `__tests__/http-error.test.ts` (~60 строк)

Сообщения об ошибках.

**Сценарии:**
- `backendUnavailableMessage()` — структура сообщения: id, role="system", content, status="failed"
- `notFoundMessage()` — content="Документ не найден", status="failed"
- `outOfScopeMessage()` — content="Вопрос вне области знаний", status="failed", limitation="out_of_scope"
- `demoChatMessage()` — имитация ответа в demo режиме
- `demoSearchResults()` — имитация результатов в demo режиме

---

## 16. `__tests__/http-interceptors.test.ts` (~100 строк)

Interceptor для `gatewayRequest()`.

**Сценарии:**
- Успешный запрос: возвращает response
- Response 401 → автоматический refresh → retry → успех
- Response 401 → refresh → 401 → logout
- Сетевая ошибка (Network Error) → исключение
- Request timeout → исключение
- SKIP_AUTH_HEADER — пропуск auth interceptor

---

## 17. `__tests__/http-helpers-extra.test.ts` (~80 строк)

Дополнительные вспомогательные функции.

**Сценарии:**
- `appendFormValue(form, key, value)` — добавление значения в FormData
- `appendFormValue(form, key, File)` — добавление файла в FormData
- `toGatewayStringId(id)` — преобразование id в строку
- `getRefreshToken()` — чтение refresh_token из localStorage
- `getRefreshToken()` — нет токена → null
- `clearGatewaySession()` — очистка session + chatMessages в store
- `clearGatewaySession()` — без store → просто очистка storage

---

## 18. `__tests__/http-mappers-tasks.test.ts` (~100 строк)

Мэпперы задач (task stages, statuses).

**Сценарии:**
- `mapGatewayTaskStage("formation")` → "Формирование"
- `mapGatewayTaskStage("indexation")` → "Индексация"
- `mapGatewayTaskStage("unknown")` → исходное значение
- `mapGatewayTaskStatusLabel("pending")` → "Ожидание"
- `mapGatewayTaskStatusLabel("running")` → "Выполняется"
- `mapGatewayTaskStatusLabel("completed")` → "Завершено"
- `mapGatewayTaskStatusLabel("failed")` → "Ошибка"
- `mapGatewayServiceLabel("parser")` → "Парсер"
- `mapGatewayServiceLabel("converter-validator")` → "Конвертер-Валидатор"
- `mapGatewayServiceLabel("gateway")` → "Gateway"
- `formatAuditEvent()` — форматирование события аудита с IP
- `formatTaskEvent()` — форматирование события задачи
- `formatTaskStepEvent()` — форматирование шага задачи
- `mapGatewayTaskRetryStatus()` — статусы retry
- `mapGatewayTaskStatusResponse()` — полный ответ статуса задачи
