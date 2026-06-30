# Баг: Исчезновение черновика после обработки / approval

## Статус: ИСПРАВЛЕНО

### Корневая причина
Оркестратор (`decide_draft`) при approve возвращает `status: "proceeding"`, а фронтенд ожидал `"approved"` и удалял черновик по наличию `document_id`. Документ при этом ещё не проиндексирован (Pipeline 2).

### Сделанные изменения

**Файл**: `UI-UX/UI Final/frontend/src/components/KnowledgeProcessing.tsx`

**Fix 1** (строки 1728–1752): В `handleDecision` при approve:
- Добавлен флаг `isProceedingAfterApprove` — true, когда ответ оркестратора `{ status: "proceeding" }`
- `shouldRemoveDraft` теперь учитывает этот флаг: не удаляет черновик при "proceeding" даже если есть `document_id`
- Вместо удаления — обновляет черновик со статусом `"validation"` (маппинг `"proceeding"` → `"validation"`)
- Note: "Документ создан, запущена индексация. Черновик исчезнет после завершения."
- 5-сек опрос `gatewayDraftsQuery` подхватит финальный `"approved"` и `isActiveDraftStatus` отфильтрует

**Fix 2** (строка 1036–1039): `publishedDocumentsQuery`
- Добавлен `refetchInterval: 10_000` при активной секции `registry`
- Реестр автоматически обновляется и подхватывает проиндексированные документы
