# PKB UI Final Frontend

Frontend объединенной версии UI/UX для PKB Neuroassistant. Приложение собрано на React + Vite + MUI и работает в demo-режиме, а также в продуктивном режиме через Gateway.

## Быстрый запуск

Через Docker:

```bash
docker compose up --build
```

Открыть:

```text
http://localhost:3300
```

Для разработки без Docker:

```bash
npm ci
npm run dev -- --host 127.0.0.1 --port 3300 --strictPort
```

Открыть:

```text
http://127.0.0.1:3300
```

Проверка сборки:

```bash
npm run build
npm run lint
```

## Вход

Продуктивный режим использует Gateway:

| Роль в mock Gateway | Логин | Пароль |
| --- | --- | --- |
| Системный администратор | `admin@example.com` | `admin123` |

Demo-режим использует локальные профили:

| Роль | Логин | Пароль | Назначение |
| --- | --- | --- | --- |
| Пользователь | `a.morozov` | `demo` | Работа с чатом, поиском и историей. |
| Администратор знаний | `o.volkova` | `demo` | Работа с базой знаний, документами, OCR, QA и НСИ. |
| Системный администратор | `d.smirnov` | `demo` | Все вкладки, включая администрирование пользователей и прав. |

## Что есть в интерфейсе

| Экран | Что делает |
| --- | --- |
| `Вход` | Логин, пароль, выбор `Продуктивный` / `Демо`. В продуктивном режиме роль подтягивается через `/auth/me`. |
| `Чат` | Дерево проектов и чатов, отправка вопроса, longpoll ответа, источники, поиск по текущему чату, обратная связь. |
| `База знаний` | Поиск по базе знаний, фильтр области поиска, разделы Registry/Classifiers, провал в раздел, список документов, предпросмотр и поиск внутри открытого документа. |
| `Обработка базы знаний` | Прямая загрузка файла, draft lifecycle через `/drafts/*`, preview, approve/reject/delete, очередь и журнал обработки. |
| `История` | Поиск по диалогам, фильтры, раскрытие найденного чата, продолжение диалога, экспорт. |
| `QA` | Контрольные метрики, оценка ответов ассистента, журнал проверки. |
| `Администрирование` | Пользователи, роли, права доступа, административный журнал, журнал обработки, Registry-редакторы классификаторов, терминологии и неизвестных кодов НСИ. |
| `Фокус-режим` | Скрывает левую навигацию и оставляет только текущую рабочую область. |
| `Темы` | Темная и светлая тема. Переключатель находится в левой навигации. |
| `Видеоинструкция` | Обучающий demo-сценарий интерфейса. |

## Текущая логика данных

Demo-режим использует mock-данные из:

```text
src/utils/mockData.ts
```

HTTP-слой находится здесь:

```text
src/utils/http.ts
```

Продуктивный режим использует Gateway-first API-слой из `src/utils/http.ts`. Mock/fallback в продуктивном режиме допустим только как явно контролируемое error/empty-состояние, а не как скрытая подмена данных.

## Интеграция с Gateway

Актуальный статус интеграции и инструкция проверки лежат здесь:

```text
../docs/ui-final-gateway-current-status-2026-06-03.md
../docs/first-run-ui-final-with-gateway.md
../docs/ui-final-gateway-open-items-2026-06-12.md
```

Ожидаемый базовый URL для локального Gateway/Orchestrator:

```text
VITE_API_BASE_URL=http://127.0.0.1:8081/api/v1
VITE_GATEWAY_AUTO_LOGIN=true
VITE_GATEWAY_USERNAME=admin@example.com
VITE_GATEWAY_PASSWORD=admin123
```

По текущим API-документам:

- Auth Service отвечает за вход, профиль, роли и администрирование пользователей.
- Query Service отвечает за проекты чата, chat-сессии, сообщения, longpoll, feedback, историю и текстовый поиск.
- Orchestrator/Gateway отвечает за drafts, документы, страницы, preview, очередь обработки, поиск документов и мониторинг.
- Registry Service хранит документы НСИ, классификаторы, секции и статистику реестра.

## Ключевые backend-сценарии

| UI-сценарий | Целевые endpoints |
| --- | --- |
| Вход | `POST /auth/token`, `GET /auth/me`, `POST /auth/refresh`, `POST /auth/revoke` |
| Список пользователей и роли | `GET /admin/users`, `GET /admin/roles`, `GET /admin/audit` |
| Проекты чата | `GET /chat/projects`, `POST /chat/projects`, `PUT /chat/projects/{project_id}`, `DELETE /chat/projects/{project_id}` |
| Чаты и сообщения | `GET /chat/sessions`, `POST /chat/sessions`, `POST /chat/sessions/{id}/messages`, `GET /chat/sessions/{id}/messages/{message_id}?longpoll=15` |
| История | `GET /chat/history`, `GET /chat/history/export`, `POST /chat/sessions/{id}/export` |
| Feedback | `POST /chat/feedback` |
| Поиск | `POST /text/search` |
| Черновики | `POST /drafts`, `GET /drafts`, `GET /drafts/{draft_id}`, `GET /drafts/{draft_id}/preview`, `POST /drafts/{draft_id}/preview`, `GET /drafts/{draft_id}/preview/status`, `PATCH /drafts/{draft_id}/decide`, `DELETE /drafts/{draft_id}` |
| Документы | `GET /documents`, `GET /documents/{doc_id}`, `GET /documents/{doc_id}/status` |
| Страницы и preview | `GET /documents/{doc_id}/pages/{page_num}`, `GET /documents/{doc_id}/pages/{page_num}/text`, `GET /documents/{doc_id}/pages/{page_num}/preview`, `GET /documents/{doc_id}/file` |
| OCR и обработка | `GET /documents/queue`, `POST /documents/{doc_id}/reprocess`; внешний пользовательский поток загрузки идет через `/drafts/*` |
| База знаний | `GET /registry/documents`, `GET /registry/documents/{doc_id}`, `GET /registry/documents/{doc_id}/sections`, `GET /registry/classifiers/tree`, `GET /common/stats`, `GET /common/enums` |
| Registry: классификаторы | `GET /registry/classifiers`, `GET /registry/classifiers/tree`, `GET /registry/classifiers/{code}`, `POST/PUT/PATCH/DELETE /registry/classifiers/{code}`, `POST /registry/classifiers/import` |
| Registry: неизвестные коды | `GET /registry/classifiers/pending`, `POST /registry/classifiers/pending/{id}/accept`, `POST /registry/classifiers/pending/{id}/reject`, `POST /registry/classifiers/validate` |
| Registry: терминология | `GET /registry/terminology`, `GET /registry/terminology/{term_id}`, `POST/PUT/DELETE /registry/terminology/{term_id}`, `GET /registry/terminology/normalize`, `POST /registry/terminology/import` |
| QA/мониторинг | `GET /monitor/health`, `GET /monitor/metrics` |

## Структура проекта

| Путь | Назначение |
| --- | --- |
| `src/main.tsx` | Точка входа React-приложения. |
| `src/App.tsx` | Главный контейнер: вход, роли, навигация, рабочая область, фокус-режим. |
| `src/theme.tsx` | Тема MUI, цвета, типографика, светлый/темный режим. |
| `src/index.css` | Базовые CSS-стили. |
| `src/components/LoginScreen.tsx` | Экран входа. |
| `src/components/ModeSwitcher.tsx` | Левая навигация, проекты, чаты, переключение вкладок. |
| `src/components/Chat.tsx` | Чат инженера, вопросы, ответы, источники, feedback. |
| `src/components/Search.tsx` | Старый отдельный экран поиска; основной поиск по базе знаний перенесен во вкладку `База знаний`. |
| `src/components/KnowledgeBase.tsx` | Вкладка `База знаний`: разделы, документы, preview, поиск внутри открытого документа. |
| `src/components/KnowledgeProcessing.tsx` | Вкладка `Обработка базы знаний`: upload/drafts/preview/approve/reject/delete. |
| `src/components/History.tsx` | История диалогов и поиск по чатам. |
| `src/components/Monitor.tsx` | QA-метрики и журнал проверки. |
| `src/components/AdminPanel.tsx` | Администрирование пользователей, ролей, прав, audit и Registry-разделов. |
| `src/components/RegistryEditors.tsx` | Редакторы классификаторов, терминологии и неизвестных кодов Registry. |
| `src/components/SourcePreviewDialog.tsx` | Предпросмотр страницы или документа. |
| `src/components/VideoGuideDialog.tsx` | Видеоинструкция / обучающий сценарий. |
| `src/components/Feedback.tsx` | Оценка ответа ассистента. |
| `src/store/uiStore.ts` | Zustand-хранилище состояния UI. |
| `src/utils/access.ts` | Роли, права и доступность вкладок. |
| `src/utils/http.ts` | HTTP-клиент и fallback на mock-данные. |
| `src/utils/mockData.ts` | Demo-данные для всех экранов. |
| `src/utils/downloadPreview.ts` | Подготовка preview/скачивания источников. |

## Сборка и конфигурация

| Файл | Назначение |
| --- | --- |
| `package.json` | Зависимости и команды запуска. |
| `package-lock.json` | Зафиксированные версии npm-пакетов. |
| `vite.config.ts` | Настройки Vite, React, Tailwind и alias. |
| `index.html` | HTML-шаблон приложения. |
| `Dockerfile` | Production-сборка UI и раздача через nginx. |
| `docker-compose.yml` | Локальный запуск контейнера. |
| `nginx.conf` | Настройка nginx для SPA. |
| `.env.example` | Пример переменных окружения. |
| `.gitignore` | Исключения для git. |
| `.dockerignore` | Исключения для Docker-сборки. |
| `eslint.config.js` | Настройки проверки кода. |
| `tsconfig*.json` | TypeScript-конфигурация. |

## Документация рядом

| Документ | Что внутри |
| --- | --- |
| `../README.md` | Общий README папки `UI Final`. |
| `../docs/first-run-ui-final.md` | Инструкция первого запуска. |
| `../docs/first-run-ui-final-with-gateway.md` | Инструкция запуска связки UI Final + Gateway. |
| `../docs/ui-final-gateway-current-status-2026-06-03.md` | Исторический статус экспериментального подключения к Gateway на 03.06. |
| `../docs/ui-final-gateway-open-items-2026-06-12.md` | Остаточные вопросы к backend/Gateway и ветки-кандидаты на удаление. |
| `gateway-backend-blockers.md` | Короткий список стоперов и вопросов, переданных backend по Gateway/Registry. |

## Текущее состояние

- Интерфейс готов для демонстрации без backend и для проверки с локальным Gateway.
- Чат, проекты чата, история, база знаний, обработка базы знаний, QA, администрирование и Registry-редакторы подключены к Gateway-контрактам в текущем объеме.
- Registry-редакторы классификаторов, терминологии и неизвестных кодов НСИ проверены с актуальным Gateway на `develop`.
- UI-only проблемы по ложному offline/audit, счетчику неизвестных кодов и счетчику терминологии закрыты.
- Открытые вопросы по Gateway зафиксированы в `../docs/ui-final-gateway-open-items-2026-06-12.md`, короткий список для backend продублирован в `gateway-backend-blockers.md`.
- Код собирается через `npm run build`.
- TypeScript-проверка запускается через `npm run lint`.
- Полноценный end-to-end тест требует рабочей единой точки Gateway.
