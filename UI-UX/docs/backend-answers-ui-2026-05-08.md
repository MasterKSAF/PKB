## 1. UI ходит только в Orchestrator или в несколько сервисов?

ответ ниже

## 2. Какой финальный BASE_URL для frontend?

```docs/api/common.md#L3-4
- Базовый URL (оркестратор): `https://{host}/api/v1`
```

Все эндпоинты публичного API доступны по единому пути `/api/v1`, независимо от того, какой сервис их обслуживает (Orchestrator или Query).

---

## 3. Какие финальные роли и права?

Три роли:

| Роль                    | Код               | Описание                                                                                    |
| ----------------------- | ----------------- | ------------------------------------------------------------------------------------------- |
| Инженер-конструктор     | `engineer`        | Чтение документов, поиск, чат, проверки, просмотр реестра                                   |
| Администратор НСИ       | `knowledge_admin` | Всё выше + загрузка/удаление документов, CRUD реестра, мониторинг                           |
| Системный администратор | `system_admin`    | Полный доступ: управление пользователями, ролями, аудит, редактирование реестров документов |

**Права (permissions)** из ответа `GET /auth/me`:

```docs/api/auth_service_api.md#L132-140
"permissions": {
    "can_upload_documents": false,   // engineer
    "can_run_ocr": false,
    "can_manage_users": false,
    "can_manage_classifiers": false,
    "can_manage_terminology": false,
    "can_manage_registry": false
}
```

**Вкладки UI** (`available_tabs`):

- `engineer`: `["chat", "search", "checks", "history"]`
- `knowledge_admin`: добавляются вкладки управления реестром
- `system_admin`: добавляется `admin`

Полная матрица доступа — в `docs/api/common.md`, раздел «Матрица доступа (RBAC)».

---

## 4. Как создается чат-сессия?

Два способа:

**a) Явное создание — `POST /chat/sessions` (Query Service):**

```docs/api/query_service_api.md#L80-88
{
  "title": "Проверка требований Arc4 для проекта 21900M2",
  "document_ids": ["doc-norm-001", "doc-draw-001", "doc-spec-001"],
  "options": {
    "model": "llama-3-70b",
    "temperature": 0.2,
    "max_context_messages": 20,
    "system_prompt_override": null
  }
}
```

Поля `title`, `document_ids` и `options` — необязательны. Возвращает `session_id`.

**b) Автосоздание через `POST /chat` (Query Service):**

```docs/api/query_service_api.md#L63-66
| Полноценный диалог с сессией | `POST /chat` (Query) + автосоздание сессии | **Основной для UI** (диалоги) |
```

При первом запросе без `session_id` сессия создаётся автоматически.

---

## 5. Что считать главным экраном истории: сессии или отдельные вопросы?

Документация предусматривает **оба представления**:

- **Сессии** (`GET /chat/sessions`) — список сессий с `last_message_preview`, `message_count`. Параметр поиска: `search` (по title).

- **Плоская история** (`GET /chat/history`) — отдельные вопросы/ответы по всем сессиям. Фильтры: `user_id`, `status`, `date_from`, `date_to`.

**Рекомендация документации:** основной для UI — `POST /chat` с сессиями. Значит **главный экран истории — список сессий**, с возможностью провалиться в конкретную сессию (`GET /chat/sessions/{session_id}`) и увидеть цепочку сообщений.

---

## 6. Как искать по старым чатам?

Два уровня поиска:

1. **Поиск сессий:** `GET /chat/sessions?search=<текст>` — ищет по полю `title`.

2. **Поиск в истории вопросов:** `GET /chat/history?user_id=&status=&date_from=&date_to=` — фильтрация по статусу (`answered`, `needs_clarification`, `source_conflict`), пользователю, диапазону дат.

Прямого full-text поиска по содержимому сообщений в текущей документации **не предусмотрено**.

---

## 7. Как отличать проектные документы от НСИ?

По полю **`document_type`**:

```docs/api/common.md#L193-194
- **Типы документов** строго фиксированы: `normative`, `archival_scan`, `drawing`, `specification`.
```

| Тип             | Категория     | Назначение                                                 |
| --------------- | ------------- | ---------------------------------------------------------- |
| `normative`     | **НСИ**       | Нормативно-справочная информация (ГОСТ, Правила РС и т.д.) |
| `archival_scan` | **НСИ**       | Архивные сканы                                             |
| `drawing`       | **Проектный** | Чертежи                                                    |
| `specification` | **Проектный** | Спецификации                                               |

В запросе `POST /validate/checks` разделение явное:

- `project_document_ids` — проектные документы
- `nsi_document_ids` — документы НСИ

В Registry Service свой `doc_type`: `["OKS", "GOST", "GOST_R", "OST", "TU", "ISO", "FSN"]`.

---

## 8. Какой endpoint загрузки документов главный?

**`POST /documents` (Orchestrator)** — основной асинхронный 

После загрузки документ автоматически проходит OCR → парсинг структуры → индексацию. Статус отслеживается через `GET /documents/{doc_id}/status`.

---

## 9. Как отдавать DOCX/XLSX/PPTX для preview?

**В текущей документации поддержка DOCX/XLSX/PPTX для загрузки и preview НЕ предусмотрена.**

Вопрос для обсуждения, в каком виде предоставлять документ для просмотра

---

## 10. Какие поля обязательны для запуска проверки НСИ?

**На данный момент функционал сверки не проработан!**

Эндпоинт: `POST /validate/checks` (Orchestrator)

```docs/api/orchestrator_service_api.md#L823-835
{
  "project_document_ids": ["doc-project-001"],   // string[] — Да
  "nsi_document_ids": ["doc-nsi-001", "doc-nsi-002"],  // string[] — Да
  "parameters": ["толщина листа", "марка стали"]  // string[] — Нет
}
```

| Поле                   | Тип      | Обязательность |
| ---------------------- | -------- |:--------------:|
| `project_document_ids` | string[] | **Да**         |
| `nsi_document_ids`     | string[] | **Да**         |
| `parameters`           | string[] | Нет            |

`user_id` определяется из токена аутентификации, не передаётся в теле запроса.

---

## 11. Где в UI должен жить Registry Service: отдельная вкладка, Реестр или Администрирование?

Исходя из `GET /auth/me`:

```docs/api/auth_service_api.md#L128-131
"available_tabs": ["chat", "search", "checks", "history"],
```

- Для роли `engineer` реестр не отображается как отдельная вкладка, но **чтение** `/registry/*` разрешено (матрица RBAC).
- Для `knowledge_admin` — чтение + CRUD реестра.
- Для `system_admin` — дополнительная вкладка «Администрирование» (пользователи, роли, аудит).

**Вывод:** Registry Service логически размещается в **отдельной вкладке «Реестр»** (или «НСИ»), доступной для `knowledge_admin` и `system_admin`. Для `engineer` может быть встроен в поиск (реестр как источник НСИ-документов), но без CRUD-действий.

---

## 12. Как связываются `/documents` и `/registry/documents`?

Это **разные сущности** с разными ID.

- `/documents` —  журнал хранения всех загружаемых в систему документов, включая нераспознанные до конца или с ошибками.
- `/registry/documents` — классифицированный и обработанный документ относящийся к общим нормативным данным.

**Связь** реализуется через поле `registry_doc_id` в метаданных файлового документа:

- `/registry/documents` — **метаданные НСИ-документа** (название, номер ГОСТ, статус, классификатор). Это карточка в реестре.
- `/documents` — **файловый документ** (PDF/изображение с OCR, индексом, страницами). Это физический файл в системе.
- Связь: `documents.metadata.registry_doc_id` → `registry.documents.doc_id`

---

## 13. Какие операции Registry входят в MVP: просмотр, CRUD, импорт, экспорт?

**Все перечисленные операции входят в MVP.** Полный перечень:

| Операция                   | Метод    | Путь                                              |
| -------------------------- | -------- | ------------------------------------------------- |
| **Просмотр списка**        | `GET`    | `/registry/documents`                             |
| **Просмотр одного**        | `GET`    | `/registry/documents/{doc_id}`                    |
| **Создать (CRUD)**         | `POST`   | `/registry/documents`                             |
| **Обновить (CRUD)**        | `PUT`    | `/registry/documents/{doc_id}`                    |
| **Обновить статус (CRUD)** | `PATCH`  | `/registry/documents/{doc_id}/status`             |
| **Удалить (CRUD)**         | `DELETE` | `/registry/documents/{doc_id}`                    |
| **Экспорт**                | `GET`    | `/registry/documents/export` (CSV)                |
| **Массовый импорт**        | `POST`   | `/registry/documents/import` (XLSX/CSV + mapping) |

Аналогичные операции доступны для **классификаторов** (`/registry/classifiers`) и **терминологии** (`/registry/terminology`).
