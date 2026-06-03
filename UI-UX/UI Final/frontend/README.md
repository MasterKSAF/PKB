# PKB UI Final Frontend

Frontend объединенной версии UI/UX для PKB Neuroassistant. Приложение собрано на React + Vite + MUI и сейчас работает в demo/mock-режиме, но структура экранов подготовлена под дальнейшую интеграцию с Gateway/backend.

## Быстрый запуск

Через Docker:

```bash
docker compose up --build
```

Открыть:

```text
http://localhost:3000
```

Для разработки без Docker:

```bash
npm ci
npm run dev -- --host 127.0.0.1 --port 3310 --strictPort
```

Открыть:

```text
http://127.0.0.1:3310
```

Проверка сборки:

```bash
npm run build
npm run lint
```

## Демо-вход

| Роль | Логин | Пароль | Назначение |
| --- | --- | --- | --- |
| Пользователь | `s.orlov` | `demo` | Работа с чатом, поиском, проверкой и историей. |
| Администратор знаний | `a.volkova` | `demo` | Работа с базой знаний, документами, OCR, QA и НСИ. |
| Системный администратор | `i.smirnov` | `demo` | Все вкладки, включая администрирование пользователей и прав. |

## Что есть в интерфейсе

| Экран | Что делает |
| --- | --- |
| `Вход` | Логин, пароль и быстрый выбор demo-роли. В реальном режиме должен работать через `/auth/token` и `/auth/me`. |
| `Чат` | Дерево проектов и чатов, отправка вопроса, ответы ассистента, источники, поиск по текущему чату, обратная связь. |
| `Поиск` | Поиск по базе знаний, фильтры, разделы, карточки результата и открытие источников. |
| `База знаний` | Состояние документов, разделы базы знаний, таблица документов, загрузка, загрузка по ссылке, повтор OCR. |
| `Проверка` | Выбор документов, сверка проектного решения с требованиями НСИ, статусы, источники, экспорт результата. |
| `История` | Поиск по диалогам, фильтры, раскрытие найденного чата, продолжение диалога, экспорт. |
| `QA` | Контрольные метрики, оценка ответов ассистента, журнал проверки. |
| `Администрирование` | Пользователи, роли, права доступа, сохранение прав, административный журнал, журнал обработки. |
| `Фокус-режим` | Скрывает левую навигацию и оставляет только текущую рабочую область. |
| `Темы` | Темная и светлая тема. Переключатель находится в левой навигации. |
| `Видеоинструкция` | Обучающий demo-сценарий интерфейса. |

## Текущая логика данных

Сейчас приложение использует mock-данные из:

```text
src/utils/mockData.ts
```

HTTP-слой находится здесь:

```text
src/utils/http.ts
```

При подключении backend нужно заменить mock-вызовы на реальные Gateway/API-запросы, сохранив те же пользовательские сценарии.

## Интеграция с Gateway

Актуальный статус интеграции и инструкция проверки лежат здесь:

```text
../docs/ui-final-gateway-current-status-2026-06-03.md
../docs/first-run-ui-final-with-gateway.md
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
- Query Service отвечает за чатовые сессии, сообщения, longpoll, feedback, историю и текстовый поиск.
- Orchestrator/Gateway отвечает за документы, страницы, preview, очередь обработки, поиск документов и мониторинг.
- Registry Service хранит документы НСИ, классификаторы, секции и статистику реестра.

## Ключевые backend-сценарии

| UI-сценарий | Целевые endpoints |
| --- | --- |
| Вход | `POST /auth/token`, `GET /auth/me`, `POST /auth/refresh`, `POST /auth/revoke` |
| Список пользователей и роли | `GET /admin/users`, `GET /admin/roles`, `GET /admin/audit` |
| Чаты и сообщения | `GET /chat/sessions`, `POST /chat/sessions`, `POST /chat/sessions/{id}/messages`, `GET /chat/sessions/{id}/messages/{message_id}?longpoll=15` |
| История | `GET /chat/history`, `GET /chat/history/export`, `POST /chat/sessions/{id}/export` |
| Feedback | `POST /chat/feedback` |
| Поиск | `POST /text/search`, `POST /documents/search`, `GET /documents/search` |
| Документы | `GET /documents`, `POST /documents`, `GET /documents/{doc_id}`, `GET /documents/{doc_id}/status` |
| Страницы и preview | `GET /documents/{doc_id}/pages/{page_num}`, `GET /documents/{doc_id}/pages/{page_num}/text`, `GET /documents/{doc_id}/pages/{page_num}/preview`, `GET /documents/{doc_id}/file` |
| OCR и обработка | `POST /tasks/{task_id}/preview`, `GET /tasks/{task_id}/preview/status`, `POST /tasks/{task_id}/decide`, `POST /documents/{doc_id}/reprocess`, `GET /documents/queue` |
| База знаний | `GET /registry/documents`, `GET /registry/documents/{doc_id}/sections`, `GET /registry/classifiers/tree`, `GET /registry/stats` |
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
| `src/components/Search.tsx` | Поиск по базе знаний. |
| `src/components/DocumentRegistry.tsx` | Вкладка `База знаний`. |
| `src/components/ChecksPanel.tsx` | Проверка на соответствие требованиям НСИ. |
| `src/components/History.tsx` | История диалогов и поиск по чатам. |
| `src/components/Monitor.tsx` | QA-метрики и журнал проверки. |
| `src/components/AdminPanel.tsx` | Администрирование пользователей, ролей и прав. |
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
| `../docs/ui-final-gateway-current-status-2026-06-03.md` | Фактический статус экспериментального подключения к актуальному Gateway. |

## Текущее состояние

- Интерфейс готов для демонстрации без backend.
- Чат, поиск, история, база знаний, QA и администрирование частично подключены к Gateway-контрактам с fallback на mock-данные.
- Код собирается через `npm run build`.
- TypeScript-проверка запускается через `npm run lint`.
- Полноценный end-to-end тест требует рабочей единой точки Gateway.
