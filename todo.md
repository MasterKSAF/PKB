# Todo — ошибка 404 при загрузке документа

## Диагноз

**Симптом:** `GET /api/v1/drafts/draft-1782457434298-yfnxtlf943/tasks` → 404

**Корень (UI — race condition):**
1. `createLocalDraft()` → `createIdempotencyKey()` → `draft-{timestamp}-{random}` — локальный нечисловой ID
2. Сразу выставляется `selectedDraftId = id`
3. React ре-рендерит → `draftTasksQuery` видит `selectedGatewayDraftId = gatewayDraftId || id = '' || 'draft-xxx'` → запрос летит с нечисловым ID до того, как `uploadDraftFile` успел проставить `gatewayDraftId` от сервера

## Выполнено

### ✅ Gateway — валидация draft_id
`backend/gateway_service/gateway/routers.py`:
- Добавлена проверка `_INVALID_DRAFT_PATH_RE` в `gateway_catch_all`
- Если путь матчит `/api/v1/drafts/{нечисловой_id}/...` → возвращается 400 `INVALID_DRAFT_ID` вместо 404 `NOT_FOUND`
- Роуты (`client.py`) остались с `\d+` — без изменений

### ✅ Gateway — безопасность приведения к int
`backend/gateway_service/gateway/main.py`:
- В `CorrelationHeadersMiddleware` добавлен try/except вокруг `int(match.group(1))` для draft_id

### ✅ Service Checker — добавлены пропущенные эндпоинты
`backend/service_checker/services/gateway.py`: +22 эндпоинта (draft tasks, preview/status, metadata, task status/steps, документы через Gateway transform, очередь/статус/ошибки документов)

## Осталось (UI — передано разработчику)

### Задача. UI — убрать запрос тасков для локального draft_id
- [ ] `KnowledgeProcessing.tsx` — в `draftTasksQuery.enabled` добавить `Boolean(selectedDraft?.gatewayDraftId)` — запрос только когда сервер проставил числовой ID
- [ ] `KnowledgeProcessing.tsx` — `selectedGatewayDraftId` не должен fallback на локальный `id`
