# Контекст проекта для UI/UX

Цель файла - не тащить в UI-команду весь репозиторий, а держать под рукой только то, что помогает шире понимать проект и принимать решения по интерфейсу.

Актуальный источник для ссылок: ветка `develop`.

## 1. Что берем в рабочий контекст

### Основная архитектура проекта

Ссылка:

- [Abzalov_Igor/architecture.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/Abzalov_Igor/architecture.md)

Зачем UI-команде:

- это главный end-to-end pipeline всего проекта;
- показывает путь от источников документов до frontend;
- связывает загрузку, OCR, извлечение данных, базу знаний, поиск, диалог, проверку, рекомендации, расчеты, историю и интеграции;
- помогает объяснять, зачем в UI нужны `Реестр`, `Проверка`, `История`, `QA` и `Администрирование`.

Как использовать:

- считать базовой картой проекта для UI/UX;
- сверять с актуальными API из `docs/api`;
- если архитектура и API расходятся, фиксировать вопрос, а не молча выбирать одну сторону.

### Gateway и API backend

Ссылки:

- [backend/gateway_service](https://github.com/NeuronsUII/PKB_neuroassistant/tree/develop_gateway/backend/gateway_service)
- [docs/api/common.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/common.md)
- [docs/api/pipeline.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/pipeline.md)
- [docs/api/orchestrator_service_api.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/orchestrator_service_api.md)
- [docs/api/query_service_api.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/query_service_api.md)
- [docs/api/auth_service_api.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/auth_service_api.md)
- [docs/api/registry_service_api.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/registry_service_api.md)
- [docs/api/integration_service_api.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/integration_service_api.md)
- [docs/api/validate_service_api.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/validate_service_api.md)
- [docs/api/ocr_service_api.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/api/ocr_service_api.md)

Зачем UI-команде:

- понимать, что UI должен стыковаться с единым Gateway, а не напрямую с отдельными сервисами;
- считать базовым публичным префиксом `http://localhost:8081/api/v1`;
- сверять реальные endpoint'ы с актуальными документами `docs/api`;
- не придумывать поля, которые backend уже описал;
- заранее видеть расхождения с нашим UI и фиксировать их в плане адаптации.

Что использовать в UI:

- публичная точка входа для frontend: `Gateway`;
- вход, профиль, роли и права: через Gateway к `Auth Service`;
- чат, документы, поиск, preview, проверка, QA: через Gateway к `Orchestrator Service`;
- чат-сессии, история, feedback: через Gateway к `Query Service`;
- классификаторы, термины, реестр НСИ: через Gateway к `Registry Service`;
- OCR-процессы и статусы обработки: через Gateway к OCR/API pipeline.

Практическое правило: в UI V1 не зашивать прямые вызовы внутренних сервисов. Все новые реальные запросы оформлять как `VITE_API_BASE_URL + /...`, где `VITE_API_BASE_URL` указывает на Gateway.

### Сравнение UI и API

Ссылка:

- [docs/ui_compare.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/docs/ui_compare.md)

Зачем UI-команде:

- быстро видеть, где frontend и backend расходятся;
- использовать как основу для вопросов backend-команде;
- не спорить на уровне ощущений, а ссылаться на конкретные несовпадения.

### Document Pipeline

Ссылки:

- [Documents_Pipeline/Docs/Document_Pipeline_Tasks.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/Documents_Pipeline/Docs/Document_Pipeline_Tasks.md)
- [Documents_Pipeline/Docs/StepanovP_AIAssistArchitecture.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/Documents_Pipeline/Docs/StepanovP_AIAssistArchitecture.md)

Зачем UI-команде:

- понять путь документа: загрузка, OCR, parsing, нормализация, chunking, embeddings, поиск;
- понять, почему в UI есть `Реестр`, OCR-статусы, ошибки обработки и QA;
- брать названия этапов pipeline для интерфейса и demo-сценариев.

Что влияет на UI:

- статусы загрузки и обработки документов;
- ошибки OCR и страницы с низким качеством;
- повторная обработка документа;
- структура источника: документ, раздел, страница, фрагмент.

### OCR и качество распознавания

Ссылка:

- [Vitalyy_Novozhilov/Chandra_ocr_2_test/ocr_test.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/Vitalyy_Novozhilov/Chandra_ocr_2_test/ocr_test.md)

Зачем UI-команде:

- понимать риски OCR: скорость, качество, зацикливание, сложные сканы;
- корректнее проектировать QA и журнал ошибок;
- не обещать пользователю идеальное распознавание без проверки.

Что влияет на UI:

- индикаторы качества OCR;
- предупреждения по страницам;
- сценарий повторной обработки;
- необходимость ручной проверки.

### Ingestion MVP

Ссылка:

- [Eugene_Rizov/ingestion_mvp/README.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/Eugene_Rizov/ingestion_mvp/README.md)

Зачем UI-команде:

- понять, как может выглядеть загрузка датасета и отчет по загрузке;
- увидеть, какие отчеты и preview уже предполагаются;
- использовать идеи для вкладок `Реестр`, `QA`, `Администрирование`.

Что влияет на UI:

- отчеты загрузки;
- список файлов;
- ошибки загрузки;
- preview данных из xlsx;
- статус ingestion.

### Backend README

Ссылки:

- [backend/orchestrator_service/readme.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/backend/orchestrator_service/readme.md)
- [backend/auth_service/readme.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/backend/auth_service/readme.md)
- [backend/query_service/readme.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/backend/query_service/readme.md)
- [backend/integration_service/readme.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/backend/integration_service/readme.md)
- [backend/registry_service/README.md](https://github.com/NeuronsUII/PKB_neuroassistant/blob/develop/backend/registry_service/README.md)

Зачем UI-команде:

- понимать, какие сервисы реально появляются в backend;
- смотреть статусы разработки;
- не проектировать UI-функции в отрыве от backend-структуры.

## 2. Что пока не тащим в работу

Пока не берем как основу для UI:

- личные черновики без связи с API или ТЗ;
- экспериментальный код, если он не оформлен в README или API;
- старые варианты архитектуры, если они противоречат свежему `develop/docs/api`;
- внутренние реализации моделей, если они не влияют на экран, кнопку, статус или пользовательский сценарий.

Идея простая: для UI важны не все технические детали, а только то, что меняет пользовательский сценарий, данные на экране, права доступа, статусы, ошибки и preview.

## 3. Как использовать этот контекст

Перед изменением UI проверяем:

1. Есть ли это в ТЗ или ответах заказчика.
2. Есть ли это в `docs/api`.
3. Есть ли это в `docs/ui_compare.md` как расхождение.
4. Есть ли влияние на pipeline документов.
5. Нужно ли это показывать инженеру, администратору или только backend-команде.

Если ответ неясен, фиксируем вопрос в плане адаптации backend/UI, а не зашиваем решение в интерфейс.

## 4. Что это добавляет к нашему UI V1

Нужно держать в поле зрения:

- `Реестр` сейчас про загруженные документы, OCR, индекс и ошибки обработки.
- `Registry Service` - это отдельный слой НСИ: классификаторы, терминология, карточки НСИ-документов.
- `Проверка` должна опираться на связку проектных документов и НСИ-документов.
- `История` должна учитывать чат-сессии, поиск по чатам и feedback.
- `QA` должен показывать не просто красивые метрики, а качество OCR, поиска, ответов и инженерной оценки.
- `Администрирование` может вырасти до управления ролями, пользователями, Registry и журналом действий.

## 5. Главный вывод

Для широкого взгляда на проект UI-команде достаточно держать рядом пять слоев:

1. Основная архитектура проекта.
2. API-контракты.
3. Pipeline документов.
4. OCR/качество.
5. История, feedback, роли и Registry.

Все остальное смотрим только если оно помогает принять конкретное UI-решение.
