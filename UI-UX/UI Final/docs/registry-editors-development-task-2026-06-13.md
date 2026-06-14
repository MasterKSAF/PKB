# Задание на разработку редакторов Registry API: classifiers и terminology

Дата: 13.06.2026

Источник контракта: `docs/api/registry_service_api.md`, ветка `develop`.

## Цель

Реализовать в UI Final административные редакторы справочников Registry Service по группам API:

- `classifiers` — классификаторы НСИ;
- `terminology` — терминология и нормализация терминов.

Редакторы должны работать через Gateway API. UI не должен обращаться напрямую к внутреннему Registry Service.

## Общие требования

1. Добавить административный раздел `Справочники НСИ`.
2. Внутри раздела сделать две вкладки: `Классификаторы` и `Терминология`.
3. Все списочные ответы обрабатывать в формате `{ data, meta }`.
4. Все одиночные ответы обрабатывать в формате `{ data }`.
5. Поддержать состояния загрузки, пустого списка, ошибки API и успешного сохранения.
6. В Gateway-режиме не использовать silent fallback на mock-данные.
7. Все операции удаления, отклонения и импорта выполнять только после подтверждения пользователя.
8. После создания, обновления, удаления и импорта обновлять список данных.
9. Ошибки backend показывать понятным текстом, сохраняя технический `error.code` в деталях.
10. Доступ к разделу должен быть у администратора; точная видимость и права изменения определяются `permissions`.

## 1. Редактор классификаторов

### API

Необходимо реализовать UI-обвязку для эндпоинтов:

- `GET /registry/classifiers`
- `GET /registry/classifiers/tree`
- `GET /registry/classifiers/{code}?classifier_system=...`
- `POST /registry/classifiers`
- `PUT /registry/classifiers/{code}?classifier_system=...`
- `PATCH /registry/classifiers/{code}?classifier_system=...`
- `DELETE /registry/classifiers/{code}?classifier_system=...`
- `POST /registry/classifiers/import`
- `GET /registry/classifiers/pending`
- `POST /registry/classifiers/pending/{pending_id}/accept`
- `POST /registry/classifiers/pending/{pending_id}/reject`
- `POST /registry/classifiers/validate`

### Поля классификатора

Редактор должен поддерживать поля:

- `classifier_system` — `MKS`, `OKSTU`, `UDC`, `EXTERNAL`;
- `code`;
- `parent_code`;
- `full_name`;
- `status` — `active`, `deprecated`, `archived`;
- `effective_date`;
- `replaced_by`;
- `created_at`.

### Функции UI

1. Переключатель системы классификации: `MKS`, `OKSTU`, `UDC`, `EXTERNAL`.
2. Два режима просмотра:
   - дерево классификаторов;
   - плоский список.
3. Фильтры для плоского списка:
   - `classifier_system`;
   - `code`;
   - `full_name`;
   - `status`;
   - `parent_code`;
   - `page`;
   - `page_size`.
4. Фильтры для дерева:
   - `classifier_system`;
   - `root_code`;
   - `max_depth`;
   - `search`;
   - `status`.
5. Панель выбранного узла справа:
   - просмотр полей;
   - редактирование;
   - сохранение;
   - удаление.
6. Создание нового узла через модальное окно.
7. Обновление узла через `PUT` или `PATCH`.
8. Удаление узла через `DELETE` с подтверждением.
9. Импорт `.xlsx` или `.csv` через `POST /registry/classifiers/import`.
10. Для импорта передавать:
    - `file`;
    - `classifier_system`;
    - `mapping` как JSON-строку.

### Pending-коды классификаторов

Неизвестные коды связаны с классификатором. UI может показывать их:

- в одной общей форме вместе с редактором классификаторов;
- либо в отдельной форме, если так проще по реализации.

Нужно реализовать отдельный блок `Неизвестные коды`.

API:

- `GET /registry/classifiers/pending`;
- `POST /registry/classifiers/pending/{pending_id}/accept`;
- `POST /registry/classifiers/pending/{pending_id}/reject`.

Функции:

1. Показывать список неизвестных кодов.
2. Фильтровать по:
   - `system`;
   - `status`;
   - `page`;
   - `page_size`.
3. Для элемента показывать:
   - `id`;
   - `system`;
   - `code`;
   - `found_in_document_id`;
   - `found_in_document_title`;
   - `status`;
   - `suggested_parent_code`;
   - `suggested_parent_name`;
   - `admin_comment`;
   - `created_at`.
4. При принятии кода запрашивать:
   - `parent_code`;
   - `full_name`;
   - `admin_comment`.
5. При отклонении кода запрашивать `admin_comment`.

### Валидация классификации

Добавить небольшую форму проверки классификации.

API:

- `POST /registry/classifiers/validate`

Поля запроса:

- `classification.mks_oks_code`;
- `classification.okstu_code`;
- `classification.udk_code`.

UI должен показывать результат проверки:

- `CONFIRMED`;
- `PENDING_REVIEW`;
- `NOT_FOUND`;
- `NOT_USED`;
- `UNASSIGNED`;
- общий статус проверки.

### Ошибки

Нужно корректно обработать:

- `CLASSIFIER_NOT_FOUND`;
- `DUPLICATE_CODE`;
- `HAS_CHILDREN`;
- `HAS_DOCUMENTS`;
- `CROSS_SYSTEM_PARENT`;
- общие ошибки `400`, `404`, `409`, `500`.

## 2. Редактор терминологии

### API

Необходимо реализовать UI-обвязку для эндпоинтов:

- `GET /registry/terminology`
- `GET /registry/terminology/{term_id}`
- `POST /registry/terminology`
- `PUT /registry/terminology/{term_id}`
- `DELETE /registry/terminology/{term_id}`
- `GET /registry/terminology/normalize?term=...`
- `POST /registry/terminology/import`

### Поля термина

Редактор должен поддерживать поля:

- `id`;
- `raw_term`;
- `standard_term`;
- `normalized_value`;
- `term_type` — `acronym`, `foreign_term`, `standard_code`, `avatar`, `symbol`;
- `is_case_sensitive`;
- `definition`;
- `synonyms`;
- `related_docs`;
- `scope`;
- `is_blocked`;
- `created_at`;
- `updated_at`.

### Функции UI

1. Таблица терминов.
2. Фильтры:
   - `raw_term`;
   - `standard_term`;
   - `term_type`;
   - `is_blocked`;
   - `scope`;
   - `page`;
   - `page_size`.
3. Панель выбранного термина справа:
   - просмотр;
   - редактирование;
   - сохранение;
   - удаление.
4. Создание термина через модальное окно.
5. Редактирование термина через `PUT`.
6. Удаление термина через `DELETE` с подтверждением.
7. Для массивов сделать ввод тегами:
   - `synonyms`;
   - `related_docs`;
   - `scope`.
8. Для `is_case_sensitive` и `is_blocked` использовать переключатели.
9. Для `term_type` использовать выпадающий список.
10. Добавить импорт `.xlsx` или `.csv` через `POST /registry/terminology/import`.
11. Для импорта передавать файл и `mapping`, аналогично импорту классификаторов.

### Нормализация термина

Добавить быстрый инструмент проверки нормализации:

1. Пользователь вводит произвольный термин.
2. UI вызывает `GET /registry/terminology/normalize?term=...`.
3. UI показывает:
   - `raw_term`;
   - `standard_term`;
   - `normalized_value`;
   - `term_type`;
   - `is_blocked`.
4. Если термин не найден и API возвращает `term_type: "unknown"`, показать это как нормальный результат, а не как ошибку.

### Ошибки

Нужно корректно обработать:

- `TERM_NOT_FOUND`;
- `DUPLICATE_TERM`;
- общие ошибки `400`, `404`, `409`, `500`.

## 3. Техническая реализация в UI

### API-слой

Добавить в UI API-слой методы, например в `registryApi`:

- `listClassifiers`;
- `getClassifierTree`;
- `getClassifier`;
- `createClassifier`;
- `updateClassifier`;
- `patchClassifier`;
- `deleteClassifier`;
- `importClassifiers`;
- `listPendingClassifiers`;
- `acceptPendingClassifier`;
- `rejectPendingClassifier`;
- `validateClassification`;
- `listTerminology`;
- `getTerm`;
- `createTerm`;
- `updateTerm`;
- `deleteTerm`;
- `normalizeTerm`;
- `importTerminology`.

### Типы

Добавить типы:

- `ClassifierNode`;
- `ClassifierPending`;
- `TerminologyEntry`;
- `RegistryListResponse<T>`;
- `RegistryObjectResponse<T>`.

### Ограничения

1. UI ходит только через Gateway base URL.
2. Не использовать прямой URL Registry Service `8084`.
3. В продуктивном режиме не подменять ошибки mock-данными.
4. В demo-режиме можно использовать демонстрационные данные, но только если demo-режим выбран явно.
5. Все ID, которые приходят числом, нормализовать к строке только на уровне UI-представления, не меняя контракт API.

## 4. UX-требования

1. Визуальный стиль должен соответствовать текущему UI Final.
2. Таблицы должны быть компактными.
3. Редактирование должно происходить без перегрузки экрана:
   - список слева или по центру;
   - детали выбранного элемента справа;
   - создание и импорт через модальные окна.
4. Для больших списков обязательна пагинация.
5. Для дерева классификаторов нужна прокрутка и поиск.
6. Для опасных действий использовать подтверждение.
7. После успешного действия показывать короткое уведомление.

## 5. Критерии приемки

1. Администратор видит раздел `Справочники НСИ`.
2. Пользователь без прав администратора раздел не видит или получает запрет.
3. Классификаторы загружаются из Gateway.
4. Работает дерево классификаторов.
5. Работает плоский список классификаторов.
6. Работают фильтры классификаторов.
7. Работает создание классификатора.
8. Работает редактирование классификатора.
9. Работает удаление классификатора с подтверждением.
10. Работает импорт классификаторов.
11. Работает список неизвестных кодов.
12. Работает принятие неизвестного кода.
13. Работает отклонение неизвестного кода.
14. Работает валидация классификации.
15. Терминология загружается из Gateway.
16. Работают фильтры терминологии.
17. Работает создание термина.
18. Работает редактирование термина.
19. Работает удаление термина с подтверждением.
20. Работает нормализация термина.
21. Работает импорт терминологии.
22. Ошибки API отображаются без падения интерфейса.
23. `npm run lint` проходит.
24. `npm run build` проходит.
25. Smoke-тест в браузере подтверждает работу с реальным Gateway.

## 6. Зафиксировано по backend

1. Все перечисленные endpoints должны быть доступны через Gateway. Если какой-то endpoint или код ошибки недоступен, это баг backend и его нужно исправлять.
2. Доступ к редакторам у администратора, но фактические права читать и менять данные определяются `permissions`.
3. Формат `mapping` для импортов уже описан в API, UI должен брать его оттуда без дополнительных договорённостей.
4. Отдельный вопрос про справочник допустимых значений сейчас не нужен для реализации редакторов.
5. Unknown-коды связаны с классификатором; UI можно сделать либо одной формой, либо двумя отдельными формами, если так проще и чище по UX.

## 7. Статус реализации на 13.06.2026

Сделано в первом рабочем слое:

1. Добавлен компонент `RegistryEditors` в раздел `Администрирование`.
2. Добавлены вкладки `Классификаторы` и `Терминология`.
3. Добавлены режимы классификаторов: список, дерево, неизвестные коды, проверка классификации.
4. Добавлен API-слой `registryApi.classifiers.*` и `registryApi.terminology.*`.
5. Поддержаны ответы `{ data, meta }` и одиночные ответы `{ data }`.
6. Подключены `permissions` из `/auth/me`: `can_manage_classifiers`, `can_manage_terminology`, `can_manage_registry`, `can_manage_users`.
7. Интерфейс не использует mock fallback в Gateway-режиме.
8. Опасные действия удаления и импорта открываются через подтверждение/модальное окно.
9. Smoke с локальным Gateway подтвержден: login, админка, список классификаторов, дерево, неизвестные коды, терминология, validate.
10. `npm run lint` и `npm run build` проходят.

Не считать полностью закрытым без отдельного тестового набора данных:

1. Создание классификатора.
2. Редактирование классификатора.
3. Удаление классификатора.
4. Импорт классификаторов.
5. Принятие/отклонение unknown-кодов.
6. Создание, редактирование, удаление и импорт терминологии.
