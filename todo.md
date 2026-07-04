# План на сессию — выполнено

## 1. Кнопки "Создать чат" / "Последний чат" вместо сообщения-заглушки
- [x] Добавлен `activeThreadId` в uiStore + сброс при logout/setWorkMode/toggleWorkMode
- [x] ModeSwitcher переведён на store-версию `activeThreadId`
- [x] Добавлен `useEffect` для раскрытия проекта в дереве при установке `activeProjectId`
- [x] Реализованы `handleCreateChat` / `handleLastChat` в Chat.tsx
- [x] Добавлена проверка `projectsQuery.isLoading` перед обработкой
- [x] Добавлена сортировка проектов по `updatedAt` для выбора действительно последнего
- [x] Кнопки переключают вкладку на chat (`setActiveTab('chat')`)
- [x] Alert с заглушкой заменён на две кнопки

## 2. Дублирующиеся цитаты в чате
- [x] Дедупликация цитат в `mapGatewayChatResponse` (фильтр по `documentId + sectionId`)
- [x] Дедупликация цитат в `mapGatewaySessionMessages`
