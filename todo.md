# Fix: timeout 6500ms для проверки черновика ✅

## Причина
Глобальный таймаут axios (6500ms) в `UI-UX/UI Final/frontend/src/utils/http.ts` обрывал longpoll-запрос
`GET /drafts/{id}/preview/status?longpoll=15` раньше, чем сервер успевал ответить.

Серверный longpoll (orchestrator) ожидает до 15с завершения preview pipeline, 
но axios на клиенте прерывал запрос через 6.5с → timeout → ошибка.

## Что сделано
- [x] 1. Проанализировать проблему (таймаут 6500 в axios, longpoll 15с на сервере)
- [x] 2. Увеличить глобальный таймаут `apiClient` с 6500ms → 30000ms (30с)
- [x] 3. Создать `pipelineClient` с таймаутом 120000ms (2 мин) для pipeline-операций
- [x] 4. Переключить `startPreview` и `waitPreview` на `pipelineClient`
- [x] 5. Проверить целостность (импорты, тесты, другие использования `apiClient`)
