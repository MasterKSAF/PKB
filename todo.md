# TODO: Нечисловой draft_id в запросах к Gateway

## Проблема
`draftTasksQuery` отправляет запрос с `gatewayDraftId` = `"draft-{timestamp}-{random}"` (не число).
Gateway возвращает 400, т.к. ожидает числовой ID.

## Причина
`gatewayDraftId` может получить нечисловое значение от сервера (Registry) или через цепочку fallback'ов.
`enabled` проверяет только truthy, но не числовой формат.

## План

### 1. http.ts — защита методов draftsApi
- [x] `tasksApi.forDraft` — уже есть guard
- [x] `draftsApi.get` — добавлен guard: если не число → throw
- [x] `draftsApi.getPreview` — добавлен guard
- [x] `draftsApi.startPreview` — добавлен guard
- [x] `draftsApi.waitPreview` — добавлен guard
- [x] `draftsApi.updateMetadata` — добавлен guard
- [x] `draftsApi.decide` — добавлен guard
- [x] `draftsApi.delete` — добавлен guard

### 2. KnowledgeProcessing.tsx — защита query
- [x] `draftTasksQuery.enabled` — проверяется числовой gatewayDraftId через `/^\d+$/`
- [x] `refreshGatewayDraftDetails` — добавлена проверка gatewayDraftId на число перед вызовом API

### 4. mapGatewayDraftRecord — запрет подмены draft_id на data.id
- [x] `draft_id: data.draft_id ?? data.id` → `draft_id: data.draft_id`
  Веб не имеет права создавать/подставлять свой id за сервер.
  Если сервер не вернул `draft_id` → пусть будет undefined, а не строковый `id`.
