# UI Final / Gateway: актуальные backend-code blockers

Дата проверки: 19.06.2026  
Ветка: `develop`  
Проверенный Gateway: `f538286d`  
Актуализировано после fast-forward: `d2ff355c`  
Источник истины для UI: документация `backend/gateway_service/docs/*` и `docs/api/*` на `develop`.

## Что уже закрыто в свежем Gateway

1. `POST /drafts` работает через прямую файловую загрузку и возвращает `202`.
2. `POST /drafts/{id}/preview` и `GET /drafts/{id}/preview/status` работают.
3. `PATCH /drafts/{id}/decide` с `action: "approve"` работает.
4. `metadata_overrides` уже принимается при `approve` и применяется к создаваемому документу.
5. `GET /drafts` работает без обязательного `document_key`.
6. После `approve` документ появляется в Gateway/Orchestrator `/documents` и `/documents/{document_id}`.

## Что остается стопером

| # | Контракт в документации | Факт в Gateway `d2ff355c` | Влияние на UI | Что нужно от backend |
| --- | --- | --- | --- | --- |
| 1 | `PATCH /drafts/{id}/metadata` сохраняет ручные правки метаданных до решения оператора. | Endpoint отсутствует: фактический ответ `404 Not Found`. | Кнопка "Сохранить изменения" не может подтвердить сохранение в Gateway; UI не подменяет "Текущее значение" локально. | Реализовать endpoint или официально убрать его из документации и подтвердить, что ручные метаданные передаются только через `decide.metadata_overrides`. |
| 2 | `PATCH /drafts/{id}/decide` принимает `action: "confirm"` для `review_required`. | Handler принимает только `approve/reject`; `confirm` возвращает `400 VALIDATION_ERROR`. | UI может отрисовать кнопку "Подтвердить проверку", но сценарий `review_required -> validation` проверить нельзя. | Добавить `confirm` в обработчик и FSM: `review_required -> validation`, далее polling `GET /drafts/{id}`. |
| 3 | `GET /drafts/{id}` возвращает полную карточку: `preview_metadata`, `raw_data`, `metadata_overrides`, `title_hash_sha256`, `title_key`, `valid_from`, `valid_until`. | Фактический ответ содержит только краткий набор: ids/status/hash/document flags/notifications. | UI не может после refresh детали надежно восстановить все текущие значения, JSON и бизнес-ключ из одного detail endpoint. | Расширить detail response до документированного контракта. |
| 4 | `review_required` появляется при warnings/critical `notifications[]`, после чего оператор делает `confirm/reject`. | На текущем mock-сценарии preview переводит черновик в `ready_for_approve`; воспроизводимого `review_required`-сценария нет. | Нельзя полноценно протестировать UI уведомлений, confirm и повторную validation. | Добавить seed/test scenario для `review_required` с `notifications[]` или параметр, позволяющий создать такой черновик. |
| 5 | `/documents/{id}/file` возвращает рабочую ссылку на файл документа. | Endpoint возвращает `file_url`, но прямой `GET /files/{id}/full.pdf` и `/api/v1/files/{id}/full.pdf` дают `404`. | Кнопка "Скачать файл" может только показать ошибку; скачать исходный документ через UI нельзя. | Сделать `file_url` рабочим: абсолютная signed URL или Gateway endpoint, доступный с тем же Bearer token. |
| 6 | `/documents/{id}/pages` + `/documents/{id}/pages/{page}/preview` дают данные для preview документа. | `/pages` возвращает `has_text_layer: true`, но не возвращает текст страницы; `/pages/{page}/preview` возвращает `preview_url`, который фактически дает `404`. | UI не может реализовать полноценный preview "как в чате": страница, поиск по тексту, раскрытие документа. | Вернуть текст страницы и/или рабочую preview-картинку/PDF URL; зафиксировать, какой endpoint является каноническим для просмотра. |
| 7 | `PATCH /registry/documents/{doc_id}` принимает `valid_from` / `valid_until`, при этом после approve документация Gateway говорит работать с `/documents/{document_id}`. | Новый документ после approve есть в `/documents/{id}`, но `PATCH /registry/documents/{id}` для него возвращает `404 Not Found`; `PATCH /documents/{id}` в Gateway не описан/не реализован. | UI не может сохранить дату действия принятого документа из вкладки "Реестр документов". | Синхронизировать контракт: либо сделать `PATCH /documents/{id}` для `valid_from/valid_until`, либо гарантировать, что тот же `document_id` доступен в `/registry/documents/{id}`. |

## Не стопер, но важная фиксация для UI

После `approve` новый документ виден через `/api/v1/documents`, но не через `/api/v1/registry/documents/{document_id}`. Поэтому зона "Реестр" внутри "Обработки базы знаний" должна читать принятые документы из Gateway/Orchestrator `/documents`. Registry mirror `/registry/documents` не считать источником истины для только что принятых черновиков.

## Временное поведение UI

1. UI отправляет `metadata_overrides` при `approve/confirm`.
2. Если `PATCH /metadata` вернет `404/405/501`, UI показывает ошибку Gateway и не переносит "Новое значение" в "Текущее значение".
3. Если `confirm` вернет `400`, UI оставляет черновик в текущем состоянии и показывает, что backend-код еще не поддерживает этот документированный сценарий.
4. Если download/preview URL возвращает `404`, UI показывает понятную ошибку и не открывает пустую вкладку.
5. Если сохранение срока действия документа возвращает `404`, UI показывает ошибку Gateway и не подменяет дату локально.
6. После реализации пунктов выше UX менять не нужно, достаточно повторить smoke: `upload -> preview -> metadata -> approve/confirm -> registry validity -> registry preview/download`.
