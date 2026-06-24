# План адаптации UI Final к новой документации Gateway/Registry

Дата: 19.06.2026  
Ветка для анализа: `origin/develop`  
Локальная рабочая ветка: `develop`  
Контекст: новая документация Gateway/Registry/Orchestrator/Converter и резюме встречи 19.06.2026.
Обновлено после повторной проверки GitHub: backend-документация закрыла основные стоперы, часть контрактов еще не реализована в коде Orchestrator/Gateway, но это не блокирует UI-адаптацию.

## 1. Цель

Привести интерфейс UI Final к новой модели обработки документов через Gateway:

1. Сделать сценарий загрузки и обработки документов честным по стадиям: файл принят системой -> создан черновик -> pipeline извлек метаданные -> оператор проверил -> документ принят/отклонен -> документ попал в реестр.
2. Разделить перегруженную вкладку "Обработка базы знаний" на понятные рабочие зоны.
3. Отобразить новые поля и состояния из документации: `title_key`, `title_hash_sha256`, `notifications`, `critical_count`, `has_notifications`, `valid_from`, `valid_until`, `document_id`, `version_id`, `is_new_document`, `raw_data`.
4. Делать UI под целевой контракт из актуальной документации, даже если часть backend-кода еще догоняет документацию.
5. Отдельно пометить функции, которые UI может отрисовать и подготовить, но должен временно защищать от неуспешного ответа backend.

## 2. Входные материалы

Использованы:

1. Свежий `origin/develop` после `git fetch origin --prune`.
2. Новые коммиты документации и backend-папок:
   - `cb926c0c` - актуальный `origin/develop` после merge docs.
   - `1c7cf5e4` - унификация `uploaded_by/uploaded_at` в `created_by/created_at`.
   - `d7fc4a33` - реструктуризация `docs/` и `docs_plans/`.
   - `2c60cfa5` - закрытие 9 documentation stoppers от 19.06.
   - `93dfea41` - устранение 7 противоречий в документации.
   - `2ae27512` - merge docs into develop.
   - `e166f949` - Windows path style and nul artifact.
   - `c1ea2f5c` - добавлен `title_key`.
   - `5144ab25` - удалена service-to-service auth, добавлены consistency checks.
   - `d66f8542` - consistency fixes after 19.06 review.
3. Документация:
   - `docs/api/gateway_service_api.md`
   - `docs/api/orchestrator_service_api.md`
   - `docs/api/registry_service_api.md`
   - `docs/api/converter_validator_service_api.md`
   - `docs/api/parser_service_api.md`
   - `docs/api/ocr_service_api.md`
   - `docs/pipelines/pipeline1-formation.md`
   - `docs/pipelines/overview.md`
   - `docs/specifications/normalizer_specification.md`
   - `docs/specifications/converter_specification.md`
4. Резюме встречи:
   - `C:\Users\Misha\Downloads\meeting_2026-06-19_summary.md`
5. Текущее состояние UI:
   - `UI-UX/UI Final/frontend/src/components/KnowledgeProcessing.tsx`
   - текущие локальные правки в этом файле не должны быть затерты.
6. Проверка backend-кода на `origin/develop`:
   - `backend/orchestrator_service/app/schemas/drafts.py`
   - `backend/orchestrator_service/app/api/v1/endpoints/drafts.py`
   - `backend/orchestrator_service/app/api/v1/endpoints/tasks.py`
   - `backend/gateway_service/gateway/routers.py`
   - `backend/gateway_service/gateway/client.py`

## 2.1. Текущий статус после проверки GitHub

По документации основные стоперы закрыты. Целевой контракт для UI теперь понятен:

1. `review_required` подтверждается через `PATCH /drafts/{id}/decide` с `action: "confirm"`.
2. Ручные правки метаданных передаются как `metadata_overrides` или сохраняются через `PATCH /drafts/{id}/metadata`.
3. `issues[]` заменено на единое поле `notifications[]`.
4. Статус `validation` добавлен в draft FSM.
5. `valid_from` и `valid_until` описаны для черновика и реестра.
6. `RMRS` добавлен в `source_type`.
7. `/api/v1/tasks/*` описан как read-only мониторинг для admin-ролей.

При этом код backend пока не полностью соответствует новой документации:

1. В `DecideRequest` в коде Orchestrator пока нет `confirm` и `metadata_overrides`.
2. В обработчике `PATCH /drafts/{id}/decide` в коде пока есть только `approve` и `reject`.
3. Отдельный `PATCH /drafts/{id}/metadata` в коде пока не найден.

Вывод для UI: правки можно вносить по новой документации. Но действия `confirm` и сохранение metadata overrides должны быть реализованы с защитой: корректная обработка `400/404/409/501`, понятное сообщение пользователю и повторная проверка после обновления backend.

## 3. Новое важное в документации

### 3.1. `title_key`

В документации появился новый ключ `title_key`.

Формула:

```text
title_key = era | source_type | mks_oks_code | okstu_code | doc_code | normalized_title
title_hash_sha256 = SHA-256(title_key)
```

Что это значит для UI:

1. UI должен показывать не только `title_hash_sha256`, но и человекочитаемый `title_key`.
2. `title_key` нужен в карточке черновика, в JSON-данных, в блоке дедупликации и в карточке документа реестра.
3. При конфликте уникальности UI должен объяснять оператору, какие поля сформировали бизнес-ключ.
4. При ручной правке полей, влияющих на бизнес-ключ, UI должен явно показывать, что итоговый `title_key/title_hash_sha256` пересчитываются backend-ом, а не фронтом.

### 3.2. Уведомления оператора

Добавлены поля:

```text
notifications[]
has_notifications
critical_count
```

Источник:

1. Parser/OCR возвращают `quality.notifications[]`.
2. Orchestrator сохраняет их в `pipeline.draft_notifications`.
3. UI получает их через `GET /drafts/{draft_id}` в поле `notifications`.

Что это значит для UI:

1. В списке черновиков нужен компактный индикатор уведомлений.
2. В рабочей области черновика нужен отдельный блок "Замечания обработки".
3. Severity нужно отображать визуально: `info`, `warning`, `error`, `critical`.
4. Черновик со статусом `review_required` нельзя показывать как обычный готовый к approve без объяснения причин.

### 3.3. Статусы черновиков

В документации встречаются статусы:

```text
uploaded
previewing
ready_for_approve
review_required
validation
approved
discarded
processing
created
indexing
indexed
failed
```

Нужно разделить:

1. Статусы черновика: загрузка, preview, проверка оператором, принято/отклонено.
2. Статусы документа после принятия: created, indexing, indexed, failed.
3. Агрегированные UI-статусы для пользователя: в обработке, требуется решение, принято, ошибка.

### 3.4. Проверка уникальности

Документация описывает `POST /registry/documents/check-uniqueness`.

Что это значит для UI:

1. UI не должен сам считать уникальность.
2. UI должен показывать результат, который вернул Gateway/Orchestrator/Registry.
3. В preview черновика нужно место для кандидатов-дубликатов.
4. При approve backend повторно проверяет уникальность, поэтому UI должен быть готов к конфликту уже после нажатия "Принять в базу знаний".

### 3.5. Даты действия документа

В Registry API появились:

```text
valid_from
valid_until
valid_at
validity_status
```

Что это значит для UI:

1. В метаданных черновика нужен блок "Срок действия".
2. В реестре документов нужен фильтр "действует на дату".
3. Для бессрочных документов нужно показывать `9999-12-31` как "бессрочно", а не как обычную дату.

### 3.6. `source_type = RMRS`

В Converter/Orchestrator примерах появился `RMRS`, но в части таблиц Registry/Orchestrator enum еще указан без `RMRS`.

Что это значит для UI:

1. В UI нужно добавить `RMRS` в список типов источника.
2. Нужно уточнить у backend, какой enum является каноническим.

### 3.7. Service-to-service auth

Из документации убрали service-to-service auth / `X-Internal-Token`.

Что это значит для UI:

1. На UI это почти не влияет.
2. UI работает только через Gateway и пользовательский JWT.
3. Ошибки внутренних сервисов должны приходить в UI через Gateway в едином формате ошибок.

## 4. Целевая структура вкладки "Обработка базы знаний"

По итогам встречи и новой документации вкладку нужно разделить на 4 вложенные рабочие зоны по логике вкладки "Чат": нажимаем основную вкладку "Обработка базы знаний", под ней в навигации появляются вложенные пункты, а справа открывается выбранная рабочая зона.

### 4.1. Загрузка / очередь

Назначение: принять файлы от пользователя и создать черновики.

Что должно быть:

1. Кнопка выбора одного или нескольких файлов.
2. Список выбранных файлов до отправки.
3. Возможность удалить файл из списка до создания черновика.
4. Кнопка "Создать черновики".
5. После отправки файлы переходят в очередь/список черновиков со статусом `uploaded` или `previewing`.
6. На этом этапе не показываем форму ручных метаданных как основную рабочую форму, потому что метаданные еще не извлечены pipeline-ом.

Что важно:

1. Кнопка "Создать черновик" означает "передать файл в backend и создать draft".
2. Она не означает "финально сформировать документ".
3. Preview и метаданные появляются позже, после обработки.

### 4.2. Черновики / метаданные

Назначение: работать с уже созданными черновиками.

Что должно быть:

1. Компактный список черновиков.
2. Состояния:
   - загружен;
   - идет preview;
   - готов к проверке;
   - нужна проверка;
   - принят;
   - отклонен;
   - ошибка.
3. Индикаторы `has_notifications` и `critical_count`.
4. Рабочая область выбранного черновика.
5. Первый блок рабочей области - "Сверка и правка метаданных".
6. Ниже - readonly-блоки:
   - Raw JSON;
   - данные Gateway;
   - классификация;
   - результат проверки уникальности;
   - уведомления обработки;
   - история состояний.
7. Предпросмотр документа открывается как в чате: справа, с возможностью развернуть на весь экран.
8. Большую отдельную кнопку "Развернуть предпросмотр" не использовать, достаточно иконки в области preview.

### 4.3. Реестр документов

Назначение: смотреть уже принятые документы, версии и карточку документа.

Что должно быть:

1. Список документов из Registry/Gateway.
2. Поиск и фильтры:
   - название;
   - код документа;
   - тип источника;
   - дата действия;
   - раздел/категория, если backend отдает эти связи.
3. Карточка документа:
   - `document_id`;
   - `version_id`;
   - `title`;
   - `doc_code`;
   - `source_type`;
   - `title_key`;
   - `title_hash_sha256`;
   - `valid_from`;
   - `valid_until`;
   - `validity_status`;
   - `preview_snapshot`;
   - версии.
4. Предпросмотр документа с тем же UX, что в чате.

### 4.4. Журнал обработки / мониторинг

Назначение: показывать технический ход обработки для администратора.

Что должно быть:

1. Список задач/шагов pipeline.
2. Фильтры:
   - статус;
   - draft id;
   - document id;
   - дата;
   - сервис;
   - severity.
3. Ошибки и предупреждения.
4. Связь с черновиком и документом.
5. Read-only режим для диагностики.

Важно: если Gateway не отдает `pipeline.tasks` / `pipeline.task_steps` наружу, этот блок нельзя сделать полноценно без backend-контракта.

## 5. План внесения правок

### Шаг 0. Зафиксировать безопасную базу

1. Проверить `git status`.
2. Не делать `pull`, пока есть локальные правки в `KnowledgeProcessing.tsx`.
3. Сначала решить, как сохранить текущие локальные изменения:
   - commit;
   - stash;
   - или аккуратный merge после просмотра diff.
4. Отдельно удалить/игнорировать локальные логи Gateway, если они не нужны в репозитории:
   - `backend/gateway_service/gateway-8081.log`
   - `backend/gateway_service/gateway-8081.err.log`
5. После синхронизации с `origin/develop` запустить:

```bash
npm run lint
npm run build
```

### Шаг 1. Обновить UI-типы и API-модели

В `http.ts` / API-слое добавить или проверить поля:

```text
title_key
title_hash_sha256
notifications
has_notifications
critical_count
document_id
version_id
is_new_document
raw_data
preview_metadata
valid_from
valid_until
validity_status
file_hash_sha256
duplicate_of
duplicate_candidates
```

Добавить статусы:

```text
uploaded
previewing
ready_for_approve
review_required
validation
approved
discarded
processing
created
indexing
indexed
failed
```

Добавить `RMRS` в `source_type`.

### Шаг 2. Разделить UI-состояния по стадиям

Сейчас в одной вкладке смешиваются:

1. выбор файла;
2. создание черновика;
3. просмотр черновика;
4. правка метаданных;
5. принятие решения;
6. очередь;
7. журнал.

Нужно разделить состояние на:

1. `selectedFiles` - файлы до отправки;
2. `drafts` - черновики из Gateway;
3. `selectedDraft` - выбранный черновик;
4. `draftDetails` - полный ответ `GET /drafts/{id}`;
5. `metadataOverrides` - ручные значения оператора;
6. `previewState` - состояние preview;
7. `decisionState` - approve/reject;
8. `processingLogState` - журнал и задачи.

### Шаг 3. Переделать "Создать черновик"

Логика кнопки:

1. Пользователь выбирает один или несколько файлов.
2. UI показывает компактный список выбранных файлов.
3. Пользователь может удалить лишний файл до отправки.
4. Нажимает "Создать черновики".
5. UI отправляет файлы через Gateway.
6. Backend создает drafts и запускает обработку.
7. UI очищает список выбранных файлов.
8. UI обновляет список черновиков.
9. UI не делает вид, что метаданные уже готовы.

Нужно убрать из этой стадии:

1. ручную форму метаданных;
2. кнопку ручного preview;
3. лишние подсказки;
4. статусы, не пришедшие от Gateway.

### Шаг 4. Список черновиков

Список должен быть компактным, однострочным:

```text
1. ГОСТ 20868-81                 ready_for_approve     warning
2. Циркулярное письмо RMRS       review_required       critical: 1
```

Что сделать:

1. Оставить плотный список.
2. Активный черновик выделять ненавязчиво.
3. Неактивные черновики слегка приглушать.
4. Сортировку сделать компактной.
5. Счетчик черновиков держать в шапке блока.
6. Показывать индикатор уведомлений, а не длинные текстовые флаги.
7. По клику на черновик загружать `GET /drafts/{id}`.

### Шаг 5. Рабочая область черновика

Первым блоком должна идти "Сверка и правка метаданных".

Таблица:

```text
Поле | Текущее значение | Новое значение | Статус
```

Правила:

1. "Текущее значение" берется из Gateway.
2. "Новое значение" вводит оператор.
3. Новое значение не должно попадать в "Текущее значение" до успешного сохранения.
4. После успешного сохранения UI должен заново получить черновик из Gateway.
5. Только после этого обновлять "Текущее значение".
6. Если Gateway не возвращает сохраненное изменение, UI должен показать ошибку или предупреждение, а не подменять данные локально.

Валидация на UI:

1. `year`: 1900-2099.
2. `mks_oks_code`: числа и точки, 1-15 символов.
3. `okstu_code`: если backend не дал справочник, временно числовой ввод с ограничением.
4. `source_type`: только enum, включая `RMRS`, если backend подтверждает.
5. `valid_from` и `valid_until`: даты, `valid_from <= valid_until`.
6. `title`: обязательное, минимальная длина.
7. `doc_code`: обязательное, если backend требует.

### Шаг 6. Raw JSON и debug-блоки

Добавить в рабочую область черновика сворачиваемые блоки:

1. Raw JSON.
2. Данные Gateway.
3. Классификация.
4. Проверка уникальности.
5. Уведомления обработки.
6. История состояний.

Первый вариант - только readonly.

Причина: новая документация не описывает безопасный контракт ручного редактирования `raw_data`.

### Шаг 7. Предпросмотр документа

Предпросмотр должен работать так же, как в чате:

1. Открытие справа в рабочей области.
2. Разворот на полный экран через иконку.
3. Поиск по документу, если доступен текстовый слой или API preview.
4. Скачивание, если Gateway отдает file/download endpoint.
5. Не делать отдельную большую кнопку "Развернуть предпросмотр".

### Шаг 8. Approve / reject / delete

Кнопки должны быть активны только по статусам.

Целевая модель по актуальной документации:

```text
uploaded/previewing       -> approve/reject disabled
ready_for_approve         -> approve/reject enabled
review_required           -> reject enabled, confirm enabled
validation                -> actions disabled, polling GET /drafts/{id}
approved/discarded        -> actions disabled
failed                    -> possible retry/reprocess if API exists
```

Что сделать:

1. Переименовать "Отклонить" в "Отклонить черновик".
2. Переименовать "Удалить" в "Удалить черновик", если это именно DELETE draft.
3. "Принять в базу знаний" показывать для `ready_for_approve`.
4. "Подтвердить проверку" показывать для `review_required`; отправлять `PATCH /drafts/{id}/decide` с `action: "confirm"` и `metadata_overrides`.
5. При approve/reject/confirm показывать результат Gateway.
6. Если текущий backend еще не принимает `confirm`, показывать понятное сообщение и не менять локально статус черновика.
7. После действия обновлять список черновиков и карточку.
8. Черновик, ушедший в `approved` или `discarded`, не должен оставаться в списке активных черновиков без явного фильтра "Показать завершенные".

### Шаг 9. Реестр документов

После approve документ должен переходить в Registry-зону.

Что сделать:

1. Использовать `document_id` из ответа Gateway.
2. Загружать карточку документа через Gateway/Registry endpoint.
3. Показывать `title_key`, `title_hash_sha256`, `valid_from`, `valid_until`, `version_id`.
4. Разделить "черновики" и "документы реестра".
5. Не смешивать версии документов со списком черновиков.

### Шаг 10. Журнал обработки

Что сделать:

1. Отдельный блок/таб "Журнал обработки".
2. Отображать только те данные, которые Gateway реально отдает.
3. Если Gateway отдает `/tasks/*` только admin-ролям, скрывать блок по permissions.
4. Если Gateway не отдает task steps, оставить заглушку с понятной ошибкой: "Gateway не вернул журнал обработки".

### Шаг 11. Обработка ошибок

Что сделать:

1. Убрать silent fallback на mock в продуктивном Gateway-режиме.
2. Ошибки Gateway показывать явно.
3. Для `400 VALIDATION_ERROR` показывать ошибки по полям.
4. Для `409 DRAFT_ALREADY_DECIDED` обновлять черновик и объяснять, что решение уже принято.
5. Для `409 DRAFT_ALREADY_PREVIEWED` не предлагать повторно запускать preview, если reprocess API не подтвержден.
6. Для `401/403` показывать проблему прав, а не "система офлайн".

### Шаг 12. Проверка

После каждого слоя:

```bash
npm run lint
npm run build
```

Smoke на Gateway:

1. Login в Gateway-режиме.
2. Выбор нескольких файлов.
3. Удаление одного файла до отправки.
4. Создание черновиков.
5. Появление черновиков в списке.
6. Обновление статусов `uploaded -> previewing -> ready_for_approve/review_required`.
7. Выбор черновика.
8. Отображение `preview_metadata`.
9. Отображение `title_key/title_hash_sha256`.
10. Отображение `notifications`.
11. Сохранение ручных metadata overrides.
12. Проверка, что "Текущее значение" обновляется только после успешного ответа Gateway.
13. Approve.
14. Появление `document_id`.
15. Переход документа в Registry.
16. Reject.
17. Проверка, что завершенные черновики не мешают активному списку.
18. Проверка прав admin/engineer/knowledge_admin.

## 6. Статус backend-контракта после проверки GitHub

### 6.1. Закрыто в документации

По актуальной документации `origin/develop` стоперы, которые мешали проектировать UI, закрыты:

1. `review_required` больше не требует отдельного `operator-confirm`; целевой endpoint - `PATCH /drafts/{id}/decide` с `action: "confirm"`.
2. `metadata_overrides` описан как часть `PATCH /drafts/{id}/decide`, также описан отдельный `PATCH /drafts/{id}/metadata` для сохранения ручных правок до решения.
3. `issues[]` заменено на единый публичный массив `notifications[]`.
4. Статус `validation` добавлен в draft FSM и enum статусов.
5. `valid_from` / `valid_until` описаны для черновиков и документов: в API `valid_until: null` означает бессрочный документ.
6. `source_type` унифицирован, `RMRS` включен в enum.
7. `/api/v1/tasks/*` описан как read-only контур мониторинга для admin-ролей.
8. `title_key` закреплен как человекочитаемая строка бизнес-ключа, из которой считается `title_hash_sha256`.

### 6.2. Не закрыто в backend-коде

Проверка кода `origin/develop` показала, что часть новой документации еще не догнала реализацию:

1. `backend/orchestrator_service/app/schemas/drafts.py`: `DecideRequest` пока содержит только `action` и `comment`; в описании указаны только `approve` / `reject`.
2. `backend/orchestrator_service/app/schemas/drafts.py`: в `DecideRequest` пока нет поля `metadata_overrides`.
3. `backend/orchestrator_service/app/api/v1/endpoints/drafts.py`: `PATCH /drafts/{id}/decide` обрабатывает только `approve` и `reject`; `confirm` сейчас попадет в `400 BAD_REQUEST`.
4. Отдельный `PATCH /drafts/{id}/metadata` в backend-коде пока не найден.
5. В старом зеркале `backend/gateway_service/docs/*` часть описаний может отставать от корневых `docs/api/*`; для UI целевым источником считать корневую документацию.

### 6.3. Вывод для UI

Эти расхождения по коду не должны останавливать UI-адаптацию. UI нужно делать под целевой контракт документации, но спорные действия оборачивать в защитную логику:

1. Кнопки и формы можно отрисовать сразу.
2. Payload для `confirm`, `metadata_overrides`, `PATCH /metadata` нужно подготовить по документации.
3. Если текущий backend вернет `400`, `404`, `409`, `422` или `501`, UI должен показать честное сообщение: "Контракт описан в документации, но endpoint еще не реализован в текущем Gateway/Orchestrator".
4. После обновления backend UI не должен требовать переписывания сценария, только убрать временные guards при необходимости.

## 7. Что делаем в UI сейчас

1. Добавляем поля UI-моделей: `title_key`, `title_hash_sha256`, `notifications`, `critical_count`, `has_notifications`, `valid_from`, `valid_until`, `document_id`, `version_id`, `is_new_document`, `raw_data`, `preview_metadata`, `metadata_overrides`.
2. Добавляем `RMRS` в `source_type`.
3. Переделываем UX "Создать черновик": это отправка файла в Gateway и создание draft, а не ручное заполнение метаданных.
4. Делаем множественную загрузку файлов, список выбранных файлов и удаление файла до отправки.
5. Делаем компактный список черновиков с active-state, статусом и индикатором уведомлений.
6. Делаем рабочую область черновика: сначала сверка/правка метаданных, ниже JSON/debug-блоки.
7. Показываем Raw JSON readonly.
8. Показываем `title_key/title_hash_sha256` и объясняем бизнес-ключ.
9. Показываем `notifications[]` с severity.
10. Настраиваем кнопки по статусам `uploaded`, `previewing`, `ready_for_approve`, `review_required`, `validation`, `approved`, `discarded`.
11. Добавляем блок реестра документов отдельно от черновиков.
12. Добавляем журнал обработки через `/tasks/*` как read-only для admin-ролей, если Gateway возвращает данные.

## 8. Что делаем с защитой до обновления backend-кода

1. `action: "confirm"`: UI готовит сценарий `review_required -> validation`, но при ошибке текущего backend показывает понятное сообщение и не ломает состояние черновика.
2. `metadata_overrides` в `PATCH /decide`: UI формирует payload, но после ответа всегда перечитывает `GET /drafts/{id}`; локально не подменяет "Текущее значение" без подтверждения backend.
3. `PATCH /drafts/{id}/metadata`: UI может иметь кнопку "Сохранить изменения", но если endpoint отсутствует, показывает, что сохранение будет доступно после обновления backend.
4. `valid_from/valid_until`: UI показывает поля и валидирует их, но считает источником истины только ответ Gateway.
5. `/tasks/*`: UI показывает журнал только если endpoint реально ответил; иначе выводит read-only ошибку доступа/отсутствия данных.
6. Raw JSON остается readonly. Редактирование JSON не включаем, пока backend явно не опишет PATCH raw-data.

## 9. Backend-долги, которые не блокируют UI

1. Реализовать `confirm` в `PATCH /drafts/{id}/decide`.
2. Добавить `metadata_overrides` в `DecideRequest`.
3. Реализовать или подтвердить `PATCH /drafts/{id}/metadata`.
4. Вернуть из `GET /drafts/{id}` сохраненные overrides, `valid_from`, `valid_until`, `title_key`, `notifications`.
5. Синхронизировать зеркальные docs в `backend/gateway_service/docs/*` с корневыми `docs/api/*`.
6. Подтвердить фактический response для duplicate conflict при `approve/confirm`.
7. Подтвердить RBAC/permissions для `/tasks/*`, `delete draft`, `approve`, `reject`, `confirm`, `metadata`.

## 10. Критерии готовности UI

Правки UI можно считать закрытыми, когда:

1. UI собирается без ошибок.
2. В Gateway-режиме нет silent fallback на demo/mock там, где ожидается реальный API.
3. Файл можно выбрать и создать draft.
4. Несколько файлов можно выбрать, удалить лишний файл до отправки и создать несколько draft.
5. Draft появляется в списке черновиков.
6. Draft открывается в рабочей области.
7. Метаданные, `title_key`, hash, уведомления и raw JSON отображаются из Gateway.
8. Ручная правка метаданных не подменяет "Текущее значение" до успешного ответа Gateway.
9. При отсутствии backend-реализации `PATCH /metadata` или `confirm` UI показывает понятную ошибку, а не падает.
10. Approve/reject/confirm доступны только в разрешенных статусах.
11. Принятый документ появляется в Registry/документах, когда backend возвращает `document_id`.
12. Журнал обработки показывает реальные данные или честную read-only ошибку отсутствующего API/прав.
13. Роли и permissions управляют доступностью кнопок.

## 11. Рекомендуемый порядок реализации

1. Синхронизировать локальный `develop` с `origin/develop`, не потеряв текущие UI-правки.
2. Обновить API-типы и маппинг статусов.
3. Переделать "Создать черновик" и список выбранных файлов.
4. Переделать компактный список черновиков.
5. Добавить загрузку полной карточки черновика.
6. Добавить рабочую область с метаданными, `title_key`, JSON, notifications и readonly debug-блоками.
7. Реализовать сохранение metadata overrides по целевому контракту с fallback на понятную ошибку, если backend endpoint еще не готов.
8. Настроить approve/reject/confirm по статусам.
9. Добавить Registry-зону.
10. Добавить журнал обработки в read-only режиме.
11. Провести smoke-тест на текущем Gateway и отдельно отметить, какие функции упираются только в недореализованный backend-код.
12. После обновления backend повторить smoke-тест без изменения UX-сценария.

## 12. Статус текущего UI-прохода

Уже внесено в UI:

1. Обновлены API-типы и маппинг черновиков под `title_key`, `metadata_overrides`, `notifications`, `valid_from`, `valid_until`, `review_required`, `validation`, `RMRS`.
2. Добавлен вызов `PATCH /drafts/{id}/metadata` в API-слой для сохранения ручных метаданных по целевому контракту документации.
3. Сценарий `PATCH /drafts/{id}/decide` расширен под `confirm` и передачу `metadata_overrides`.
4. В рабочей области черновика добавлены поля срока действия документа и отображение `title_key`.
5. Добавлен блок уведомлений обработки с severity и компактный индикатор уведомлений в списке черновиков.
6. Кнопки решения разведены по статусам: `approve` только для `ready_for_approve`, `confirm` для `review_required`, `reject` для `ready_for_approve/review_required`.
7. Ручные метаданные не подменяют "Текущее значение" локально: после сохранения UI перечитывает черновик из Gateway.
8. При недоступном backend endpoint UI показывает ошибку Gateway и не переводит черновик в ложный успешный статус.
9. Добавлен фоновый refresh списка черновиков в активной вкладке обработки базы знаний.
10. Добавлен polling выбранного черновика в статусах `previewing` и `validation` через `GET /drafts/{id}`.
11. Маппинг `GET /drafts` расширен под разные форматы ответа Gateway: массив, `items`, `drafts`, `data`.
12. Журнал обработки подключен к `/drafts/{id}/tasks` и `/tasks/{task_id}/status` для выбранного черновика; audit используется как fallback.
13. Для краткого `GET /drafts/{id}` добавлен fallback на `GET /drafts/{id}/preview`, чтобы не терять preview-метаданные в рабочей области.

Остается проверить на живом Gateway:

1. Реальный ответ `GET /drafts/{id}` после сохранения `metadata_overrides`.
2. Фактическую поддержку `PATCH /drafts/{id}/metadata`.
3. Фактическую поддержку `PATCH /drafts/{id}/decide` с `action: "confirm"`.
4. Возврат `notifications[]`, `title_key`, `valid_from`, `valid_until` в полном ответе черновика.
5. Переход черновика из активного списка после `approve/reject`.

Backend-code debt, который не мешает продолжать UI:

1. Если `PATCH /drafts/{id}/metadata` еще не реализован в Gateway/Orchestrator, backend должен добавить endpoint или подтвердить другой путь сохранения.
2. Если `confirm` еще не реализован в `PATCH /drafts/{id}/decide`, backend должен расширить enum `action` и обработчик FSM.
3. Если `metadata_overrides` еще не принимается в `DecideRequest`, backend должен добавить поле в схему и прокинуть его в обработчик.

## 13. Повторная проверка свежего Gateway

Дата: 19.06.2026  
Проверенный commit: `f538286d`  
Метод проверки: локальный fast-forward `develop`, статический просмотр `backend/gateway_service`, ASGI-smoke через `fastapi.testclient.TestClient`.

Фактически подтверждено:

1. Свежий Gateway добавил `docker-compose.yml`, rate limiting, IDOR protection, request/correlation headers, logging/OTel, новые mock-структуры и тесты.
2. `POST /api/v1/drafts` с прямой файловой загрузкой возвращает `202`.
3. `POST /api/v1/drafts/{id}/preview` возвращает `202`.
4. `GET /api/v1/drafts/{id}/preview/status` переводит черновик в `ready_for_approve`.
5. `PATCH /api/v1/drafts/{id}/decide` с `action: "approve"` возвращает `200`.
6. `metadata_overrides` при `approve` уже принимается mock Gateway и применяется к создаваемому документу.
7. `/drafts/{id}/tasks`, `/tasks/{task_id}/status`, `/tasks/{task_id}/steps` возвращают `200` и пригодны для журнала обработки.

Осталось не закрыто в коде Gateway `f538286d`:

1. `PATCH /api/v1/drafts/{id}/metadata` описан в документации, но фактически возвращает `404 Not Found`.
2. `PATCH /api/v1/drafts/{id}/decide` с `action: "confirm"` описан в документации, но фактически возвращает `400 VALIDATION_ERROR`; handler принимает только `approve/reject`.
3. `GET /api/v1/drafts/{id}` пока возвращает краткий detail без `preview_metadata`, `raw_data`, `metadata_overrides`, `title_key`, `valid_from`, `valid_until`.
4. В mock-сценарии пока нет воспроизводимого перехода в `review_required` с `notifications[]`, поэтому нельзя полностью проверить UI-сценарий `review_required -> confirm -> validation`.

Что это меняет для UI:

1. UI должен продолжать отправлять ручные правки в `decide.metadata_overrides`, потому что этот путь уже работает для `approve`.
2. Кнопка "Сохранить изменения" остается с защитной обработкой ошибки, пока backend не реализует `PATCH /metadata` или не уберет его из документации.
3. "Подтвердить проверку" оставляем под целевой контракт документации, но UI не должен менять статус локально при `400`.
4. Для полной карточки черновика UI использует fallback из списка/preview, пока `GET /drafts/{id}` не начнет возвращать документированный полный набор полей.
5. Для статусов `previewing` и `validation` UI уже готов к backend-driven переходам: перечитывает выбранный черновик и обновляет список без ручной кнопки.
6. Журнал обработки теперь готов показывать реальные pipeline steps для выбранного draft, если Gateway возвращает task endpoints.
7. Пока detail endpoint не возвращает полный документированный набор полей, UI добирает preview-метаданные через отдельный preview endpoint.

## 14. Актуализация после обновления `origin/develop`

Дата проверки: 19.06.2026  
Проверенный удаленный commit: `d2ff355c`  
Метод проверки: `git fetch origin --prune`, просмотр `git log HEAD..origin/develop`, `git diff HEAD..origin/develop -- docs/api backend/gateway_service backend/orchestrator_service backend/query_service`.

Что изменилось на GitHub после предыдущей проверки:

1. `origin/develop` обновился с `f538286d` до `d2ff355c`.
2. Существенные изменения пришли в `backend/query_service`: проекты чата, feedback validation, streaming export, health live/ready, pending watchdog, idempotency для `POST /chat`, text search filters.
3. В проверенном diff нет изменений в `docs/api/gateway_service_api.md`, `docs/api/registry_service_api.md`, draft API Gateway и mock Gateway, которые меняли бы сценарий "Обработка базы знаний".
4. Для обработки базы знаний ранее выявленные backend-code ограничения остаются актуальными до отдельного обновления Gateway/Orchestrator: `PATCH /drafts/{id}/metadata`, `confirm`, короткий `GET /drafts/{id}`.

Что дополнительно сделано в UI после этой проверки:

1. В `uiStore` добавлено состояние вложенной рабочей зоны `activeKnowledgeProcessingSection`.
2. В левой навигации под вкладкой "Обработка базы знаний" добавлены 4 вложенные вкладки по паттерну "Чата":
   - "Загрузка" - выбор файлов, создание черновиков, очередь обработки;
   - "Черновики" - список черновиков, действия, сверка метаданных, JSON/Gateway/debug-блоки, preview;
   - "Реестр" - принятые документы;
   - "Журналы" - журнал обработки и pipeline-monitoring.
3. Экран `KnowledgeProcessing` больше не показывает все зоны одновременно: выбранная вложенная вкладка управляет содержимым рабочей области.
4. Кнопки работы с выбранным черновиком вынесены из загрузки в зону "Черновики".
5. `npm run lint` и `npm run build` прошли успешно после правки.
6. В браузере проверено раскрытие "Обработка базы знаний" и переключение вложенных вкладок: "Загрузка", "Черновики", "Реестр", "Журналы".

Что осталось сделать после актуализации:

1. Проверить сценарий обработки на живом Gateway: `upload -> drafts -> preview/status -> metadata -> approve/reject`.
2. Проверить, что принятый документ после `approve` реально уходит из активных черновиков и появляется в реестре.
3. Проверить влияние новых изменений `query_service` на чатовую навигацию:
   - создание проекта с обязательным `code`;
   - список проектов в формате `{ items, meta }`;
   - `POST /chat` с `Idempotency-Key`;
   - streaming export вместо JSON-ответа с `url`;
   - feedback validation `rating/rating_status`.
4. Дождаться backend-реализации или подтверждения по оставшимся draft-контрактам:
   - `PATCH /drafts/{id}/metadata`;
   - `PATCH /drafts/{id}/decide` с `action: "confirm"`;
   - полный `GET /drafts/{id}` с `preview_metadata`, `raw_data`, `metadata_overrides`, `title_key`, `valid_from`, `valid_until`;
   - воспроизводимый mock-сценарий `review_required + notifications`.

Выполнено после актуализации:

1. Локальный `develop` безопасно обновлен fast-forward до `origin/develop@d2ff355c`; пересечений с текущими UI-правками не было.
2. После обновления выполнен `npm run lint` - без ошибок.
3. После обновления выполнен `npm run build` - без ошибок, осталось только стандартное предупреждение Vite о крупном chunk.
4. Проверены базовые HTTP-ответы: UI на `127.0.0.1:3300` отвечает `200`, Gateway health на `127.0.0.1:8081/api/v1/health` отвечает `ok`.

Smoke Gateway после актуализации:

1. `POST /auth/token` с `admin@example.com / admin123` - успешно.
2. `POST /drafts` с файлом больше 1 КБ - успешно, создан `draft_id=207`.
3. `POST /drafts/{id}/preview` - успешно, статус `previewing`.
4. `GET /drafts/{id}/preview/status` - успешно, статус `ready_for_approve`.
5. `PATCH /drafts/{id}/metadata` - по-прежнему `404`; backend endpoint еще не реализован или не прокинут.
6. `PATCH /drafts/{id}/decide` с `action: "approve"` и `metadata_overrides` - успешно, draft получил `status=approved`, `document_id=209`, `version_id=209`.
7. Новый документ после approve виден через `/api/v1/documents` и `/api/v1/documents/{document_id}`.
8. Новый документ не виден через `/api/v1/registry/documents/{document_id}`; для UI зоны "Реестр" в обработке базы знаний источником должен оставаться Gateway/Orchestrator `/documents`, а не Registry mirror `/registry/documents`.

## 15. Остаток работ по memo встречи 19.06

Этот раздел фиксирует, что именно еще не закрыто по memo `UI-UX/meetings/2026-06-19/meeting-memo-2026-06-19.md`.

### 15.1. Что уже соответствует memo

1. Вкладка "Обработка базы знаний" разделена на 4 вложенные рабочие зоны:
   - "Загрузка";
   - "Черновики";
   - "Реестр";
   - "Журналы".
2. "Создать черновик/черновики" работает как стадия отправки файла в Gateway, а не как финальное создание документа.
3. Множественная загрузка файлов, список выбранных файлов и удаление файла до отправки реализованы.
4. Список черновиков компактный, выбранный черновик выделяется, остальные приглушаются.
5. В списке черновиков есть статус и компактный индикатор уведомлений.
6. Рабочая область черновика начинается с блока "Сверка и правка метаданных".
7. Ниже метаданных есть readonly-блоки Raw JSON, данные Gateway, классификация, уведомления, дубликаты, статус обработки.
8. Ручные метаданные не подменяют "Текущее значение" до успешного ответа Gateway.
9. `approve/reject/confirm/delete` разведены по статусам и защищены от ложного локального успеха.
10. Журнал обработки подключен к `/drafts/{id}/tasks` и `/tasks/{task_id}/status`, audit остается fallback.

### 15.2. Главный незакрытый слой: "Реестр документов"

Текущий статус: зона "Реестр" создана и подключена через существующий `DocumentRegistryPanel`. Это не равно полному закрытию memo. Нужно доработать реестр как самостоятельную рабочую зону для принятых документов после approve.

Что нужно сделать:

1. Источник данных:
   - основной источник для зоны "Реестр" в обработке базы знаний - `/api/v1/documents`;
   - detail - `/api/v1/documents/{document_id}`;
   - Registry mirror `/api/v1/registry/documents` не считать источником истины для только что принятых черновиков, потому что smoke показал: новый документ есть в `/documents`, но отсутствует в `/registry/documents/{document_id}`.
2. Список документов:
   - оставить компактный список документов;
   - убрать визуально тяжелые строки, если они мешают просмотру большого количества документов;
   - показывать минимум: название, код документа, тип источника, короткий статус;
   - добавить/проверить поиск по названию, коду, типу, разделу/категории, если поле приходит от Gateway;
   - добавить фильтр по статусу действия/дате действия, если Gateway возвращает `valid_from`, `valid_until`, `validity_status`.
3. Карточка выбранного документа должна явно показывать:
   - `document_id`;
   - `version_id` / latest version;
   - `title`;
   - `doc_code`;
   - `source_type`;
   - `title_key`;
   - `title_hash_sha256`;
   - `valid_from`;
   - `valid_until`;
   - `validity_status`;
   - `created_by`, `updated_by`, `created_at`, `updated_at`, если Gateway возвращает.
4. Бизнес-ключ:
   - `title_key` показывать человекочитаемо, не только hash;
   - `title_hash_sha256` показывать рядом как технический идентификатор;
   - если `title_key` не пришел из `/documents/{id}`, UI должен честно писать "не передан Gateway", а не вычислять его самостоятельно.
5. Версии:
   - использовать `/documents/{document_id}/versions`;
   - показать список версий;
   - дать выбрать 2 версии для сравнения, если данные позволяют;
   - если versions endpoint пустой/недоступен, показать read-only сообщение без mock-подмены в Gateway-режиме.
6. Preview:
   - preview в реестре должен быть по UX как в чате: правая панель, поиск по тексту, раскрытие на весь экран, навигация по страницам;
   - использовать `/documents/{document_id}/pages` и `/documents/{document_id}/pages/{page}/preview`, если Gateway возвращает данные;
   - если Gateway не отдал страницы/текст, показать честное "Gateway не передал preview", без демо-текста в Gateway-режиме.
7. Действия по документу:
   - "Открыть preview";
   - "Скачать";
   - "Версии";
   - "История";
   - "Ошибки";
   - "Параметры";
   - кнопки должны быть disabled или показывать понятную ошибку, если endpoint отсутствует или нет прав.
8. Переход после approve:
   - после успешного `approve` перечитать список черновиков;
   - убрать `approved/discarded` из активного списка черновиков;
   - перечитать `/documents`;
   - если Gateway вернул `document_id`, выделить/открыть этот документ в зоне "Реестр" или дать явное действие "Открыть в реестре".
9. Отделить реестр от "Базы знаний":
   - "База знаний" остается пользовательским просмотром разделов и документов;
   - "Реестр" внутри обработки - административная зона принятых документов, версий, статусов и технических данных.

### 15.3. Остаток по "Черновикам"

1. Проверить в браузере живой сценарий:
   - выбрать несколько файлов;
   - удалить один до отправки;
   - создать черновики;
   - дождаться `ready_for_approve`;
   - открыть черновик;
   - проверить metadata, Raw JSON, Gateway data, notifications, preview.
2. Дожать сохранение ручных метаданных после решения backend:
   - если backend реализует `PATCH /drafts/{id}/metadata`, кнопка "Сохранить изменения" должна обновлять "Текущее значение" только после успешного `GET /drafts/{id}`;
   - если backend решит сохранять только через `decide.metadata_overrides`, кнопку "Сохранить изменения" нужно переименовать/изменить сценарий, чтобы не обещать отдельное сохранение.
3. Проверить `confirm` после реализации backend:
   - `review_required -> confirm -> validation`;
   - polling `GET /drafts/{id}`;
   - возврат к `ready_for_approve` или другой целевой статус.
4. Проверить `notifications[]`:
   - severity `info/warning/error/critical`;
   - compact indicator в списке;
   - подробный блок уведомлений в рабочей области.

### 15.4. Остаток по "Журналам"

1. Проверить, что журнал выбранного draft берет данные из:
   - `/drafts/{id}/tasks`;
   - `/tasks/{task_id}/status`;
   - `/tasks/{task_id}/steps`, если нужен детальный drill-down.
2. Добавить фильтры для административного режима:
   - статус;
   - draft id;
   - document id;
   - сервис/этап;
   - severity;
   - дата.
3. Если Gateway не отдает данные или роль не имеет прав, показывать read-only сообщение с причиной, не подставлять demo-журнал в Gateway-режиме.

### 15.5. Остаток по свежему `query_service`

Свежий `origin/develop@d2ff355c` изменил `query_service`. Это не блокирует вкладку "Обработка базы знаний", но требует отдельной smoke-проверки чата:

1. Создание проекта:
   - UI уже отправляет `code`, `name`, `status`;
   - нужно живьем проверить `POST /chat/projects`.
2. Список проектов:
   - backend теперь возвращает `{ items, meta }`;
   - UI-маппинг это поддерживает, но нужен smoke через Gateway.
3. Chat longpoll:
   - основной путь остается `GET /chat/sessions/{session_id}/messages/{message_id}?longpoll=15`;
   - нужно проверить отправку сообщения и финальный ответ.
4. Feedback:
   - UI отправляет формат `session_id + message_id`, это соответствует новой документации;
   - нужно проверить, что Gateway не возвращает `AMBIGUOUS_FEEDBACK_FORMAT`.
5. Export:
   - `POST /chat/sessions/{id}/export` теперь streaming response, а не JSON с `url`;
   - если эта функция используется в UI, нужно адаптировать скачивание.

### 15.6. Backend-зависимости, которые остаются

1. `PATCH /drafts/{id}/metadata` - по smoke на `d2ff355c` возвращает `404`.
2. `PATCH /drafts/{id}/decide` с `action: "confirm"` - нужно проверить после backend-реализации.
3. `GET /drafts/{id}` - нужен полный detail: `preview_metadata`, `raw_data`, `metadata_overrides`, `title_key`, `valid_from`, `valid_until`.
4. Нужен воспроизводимый сценарий `review_required + notifications[]`.
5. Нужно подтвердить, должен ли новый документ после approve появляться в `/registry/documents`, или для UI административного реестра каноническим остается `/documents`.

### 15.7. Рекомендуемый следующий порядок правок

1. Доработать `DocumentRegistryPanel` под административный реестр `/documents`.
2. Убрать из Gateway-режима demo fallback в preview/versions/history/errors/parameters там, где он маскирует отсутствие данных.
3. Добавить явные поля карточки документа: `document_id`, `version_id`, `title_key`, `title_hash_sha256`, `valid_from`, `valid_until`, `validity_status`.
4. Довести preview реестра до UX чата.
5. Добавить действие "Открыть в реестре" после approve.
6. Прогнать `npm run lint`, `npm run build`.
7. Пройти ручной smoke UI + Gateway по четырем вложенным зонам.

## 16. Фактический статус после правок и live-smoke 19.06

Проверено на локальном `develop` со свежим Gateway `origin/develop@d2ff355c`.

### 16.1. Что закрыто в UI

1. "Обработка базы знаний" работает как вложенная зона по паттерну "Чата": "Загрузка", "Черновики", "Реестр", "Журналы".
2. "Черновики" больше не требуют отдельной кнопки запуска preview: если черновик пришел из Gateway в статусе `uploaded`, открытие preview запускает `POST /drafts/{id}/preview` и ожидание `GET /drafts/{id}/preview/status`.
3. После `ready_for_approve` UI разблокирует "Принять в базу знаний" и "Отклонить черновик".
4. После успешного `approve` UI убирает черновик из активного списка, сбрасывает выбранный draft и перечитывает документы.
5. "Реестр" внутри обработки переведен на Gateway/Orchestrator `/documents`, а не на `/registry/documents`.
6. В реестре добавлены компактный список, поиск, фильтры по источнику/статусу/дате, карточка выбранного документа, бизнес-ключи, срок действия, версии, история, ошибки, параметры.
7. Preview реестра больше не подставляет demo-текст в Gateway-режиме: если Gateway не передал текст/preview, UI показывает честное ограничение.
8. "Скачать файл" больше не открывает молча нерабочую ссылку; UI пытается скачать через API-клиент с токеном и показывает понятную ошибку при `404`.
9. "Реестр" переведен на рабочую двухколоночную раскладку: список документов слева, preview и действия справа, раскрытие preview остается отдельной модалкой.
10. "Журналы" переведены в плотный табличный вид: время, объект, этап, событие, статус, доступ и цветной маркер события.
11. Для документа в реестре добавлены действия "Сохранить срок" и "Удалить документ" с подтверждением перед удалением.

### 16.2. Что проверено живьем

1. `npm run lint` - успешно.
2. `npm run build` - успешно, только стандартное предупреждение Vite о размере chunk.
3. UI доступен на `http://127.0.0.1:3300/`.
4. Gateway health доступен на `http://127.0.0.1:8081/api/v1/health`, статус `ok`, `endpoints_total: 131`.
5. Авторизация в UI: `admin@example.com / admin123`, профиль и роль подтягиваются через Gateway.
6. Вложенные вкладки обработки открываются и переключаются без ошибок консоли.
7. Через Gateway создан тестовый draft `229`, UI увидел его в списке "Черновики обработки".
8. Открытие preview для draft `229` перевело его из `uploaded` в `ready_for_approve`.
9. `PATCH /drafts/229/metadata` вернул `404`; UI показал ошибку и не перенес новое значение в "Текущее значение".
10. `approve` для draft `229` прошел успешно: черновик ушел из списка, создан документ `document_id=240`, `version_id=231`.
11. Новый документ `UI live ГОСТ 2.051` появился в "Реестре", счетчик документов стал `5`.
12. `GET /drafts/229/tasks`, `GET /tasks/230/status`, `GET /tasks/230/steps` работают и отдают pipeline steps.
13. На десктопной ширине "Реестр" открывает preview справа от списка, а не только через центральную модалку.
14. Кнопка раскрытия preview открывает модалку просмотра и закрывается без ошибок.
15. Кнопка "Удалить" открывает подтверждение `DELETE /documents/{id}` и не выполняет удаление без отдельного подтверждения.
16. `PATCH /registry/documents/240` для сохранения `valid_from/valid_until` вернул `404`; UI показал ошибку и не стал локально подменять данные.
17. После финального reload новых ошибок консоли нет.

### 16.3. Что осталось только после backend-ответов/правок

1. `PATCH /drafts/{id}/metadata` - сейчас `404`; без него нельзя подтвердить отдельное сохранение ручных метаданных до approve.
2. `confirm` flow - нужен воспроизводимый `review_required + notifications[]` и поддержка `action: "confirm"`.
3. `GET /drafts/{id}` - нужен полный detail по документации: `preview_metadata`, `raw_data`, `metadata_overrides`, `title_key`, `valid_from`, `valid_until`.
4. Download документа - `/documents/{id}/file` возвращает `file_url`, но `/files/{id}/full.pdf` сейчас `404`.
5. Preview документа - `/documents/{id}/pages` не возвращает текст страницы, а `preview_url` из `/pages/{page}/preview` сейчас `404`.
6. Pipeline steps пока содержат `input_data/output_data: { "mock": true }`; для полноценного админского анализа нужны реальные входы/выходы этапов или подтверждение, что mock-данные пока ожидаемы.
7. Сохранение срока действия принятого документа не подтверждено backend: `valid_from/valid_until` описаны для `PATCH /registry/documents/{doc_id}`, но документ из `/documents/{id}` не находится в registry endpoint по тому же id.

### 16.4. Практический следующий шаг

UI-слой по текущему плану доведен до стадии, где дальнейшее улучшение полноты сценария упирается в backend-контракты выше. После backend-правок нужно повторить короткий smoke: `upload -> draft -> preview -> metadata save -> confirm/approve -> registry validity -> registry preview/download -> task steps`.
