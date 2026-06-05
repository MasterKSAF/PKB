# Аудит API-документации PKB Neuroassistant

**Дата аудита:** 2026-06-06  
**Правило:** `check_rule.md` (пункт 1)  
**Аудитор:** Zed AI Agent  
**Объём:** 13 файлов документации, 124+ эндпоинтов

---

## 1. Общая сводка по сервисам

| Сервис | Файл | Эндпоинтов | Статус документации | Критичных проблем |
|--------|------|------------|---------------------|-------------------|
| **Auth Service** | `auth_service_api.md` | 14 | ⭐⭐⭐ Хорошо | 1 серьёзная |
| **Analyse Service** | `analyse_service_api.md` | 5 | ⭐⭐ Удовлетворительно | 1 блокирующая, 2 серьёзных |
| **Common API** | `common_api.md` | 0 (контракт) | ⭐⭐⭐⭐ Очень хорошо | 3 серьёзных |
| **Converter-Validator** | `converter_validator_service_api.md` | 3 | ⭐⭐⭐ Хорошо | 1 серьёзная |
| **Gateway Service** | `gateway_service_api.md` | 1 + прокси | ⭐⭐⭐ Хорошо | 2 серьёзных |
| **Integration Service** | `integration_service_api.md` | 6 | ⭐⭐⭐ Хорошо | 1 серьёзная |
| **OCR Service** | `ocr_service_api.md` | 5 | ⭐⭐⭐ Хорошо | 2 серьёзных |
| **Orchestrator Service** | `orchestrator_service_api.md` | 28 | ⭐⭐⭐ Хорошо | 4 серьёзных |
| **Parser Service** | `parser_service_api.md` | 5 | ⭐⭐⭐ Хорошо | 2 серьёзных |
| **Query Service** | `query_service_api.md` | 20 | ⭐⭐⭐⭐ Очень хорошо | 3 серьёзных |
| **RAG Builder** | `rag_builder_service_api.md` | 3 | ⭐⭐ Удовлетворительно | 2 блокирующих |
| **RAG Search** | `rag_search_service_api.md` | 1 | ⭐⭐⭐ Хорошо | 1 серьёзная |
| **Registry Service** | `registry_service_api.md` | 33 | ⭐⭐⭐ Хорошо | 5 серьёзных |

---

## 2. Список проблем по критичности

### 🔴 БЛОКИРУЮЩИЕ (невозможно разрабатывать/интегрироваться без уточнения)

#### Б-1. RAG Builder: несуществующий тип секции `drawing`
- **Файл:** `rag_builder_service_api.md`
- **Место:** таблица типов секций, столбец `type`, а также описание поля `sections[].type`
- **Проблема:** В перечне допустимых типов указан `drawing`, которого **не существует** в системе. В glossary, Registry и Converter-validator типы секций: `text`, `textBlock`, `headerFooter`, `table`, `list`, `image`, `formula`. Сервис RAG Builder не знает, как обрабатывать `drawing`, и не определено сопоставление `drawing` → `image`.
- **Последствие:** Разработчик RAG Builder не поймёт, какой алгоритм чанкинга применять для несуществующего типа. Возможен сбой индексации при получении такого типа.

#### Б-2. RAG Builder: несоответствие именования ID секции (`sections[].id` vs `section_id`)
- **Файл:** `rag_builder_service_api.md`
- **Место:** таблица полей запроса `sections[].id` vs пример JSON `section_id`
- **Проблема:** В таблице параметров указано `sections[].id` (bigint, обязательно), а в примере JSON и в glossary/Registry используется `section_id`. Сервису на вход подаётся JSON от Registry, где поле называется `section_id`.
- **Последствие:** Непонятно, какое имя поля ожидает RAG Builder на самом деле. Контракт нарушен.

#### Б-3. Registry: один эндпоинт `POST /registry/documents` принимает два несовместимых формата тела
- **Файл:** `registry_service_api.md`
- **Место:** раздел 3.3 «Создать (основной / из Пайплайна 1)»
- **Проблема:** Эндпоинт описан как имеющий два режима: (а) прямое создание с полями `title`, `doc_code`, `source_type` и т.д.; (b) создание из пайплайна с телом `{ "document": { "source": ..., "metadata": ..., "content": [...] } }`. Не описано, как сервис различает режим (по наличию поля `document`? по Content-Type? по заголовку?). Не описаны разные коды ошибок для разных режимов.
- **Последствие:** Интегратор не может корректно сформировать запрос, не зная логики маршрутизации на стороне сервера.

#### Б-4. Registry vs Orchestrator: несовпадение FSM-статусов документа
- **Файл:** `registry_service_api.md` (раздел 4.2, enum `document_status`) vs `glossary.md` vs `orchestrator_service_api.md`
- **Место:** `registry_service_api.md` перечисляет: `["draft", "uploaded", "validating", "processing", "review_required", "ready_for_promotion", "approved", "failed", "archived"]`. В glossary и Orchestrator используются: `previewing`, `awaiting_decision`, `parsing`, `validation`, `registry`, `pending_index`, `indexing`, `indexed`, `duplicate`, `new_version`.
- **Проблема:** Registry является хранилищем статусов, но его enum не содержит ключевых статусов пайплайна (например, `previewing`, `parsing`, `indexing`). Не описано, как Orchestrator хранит промежуточные статусы — в Registry или в своей БД.
- **Последствие:** Невозможно понять, кто является source of truth для статусов документа.

---

### 🟠 СЕРЬЁЗНЫЕ (вызовут ошибки или путаницу при реализации)

#### С-1. Auth Service: несоответствие ID роли (`id` vs `role_id`)
- **Файл:** `auth_service_api.md`
- **Место:** `POST /admin/roles` ответ содержит `"id": 1` (bigint); `GET /admin/roles` ответ содержит `"role_id": "r-admin"` (string).
- **Проблема:** Один и тот же объект (роль) имеет разные имена и типы идентификатора в разных эндпоинтах.

#### С-2. Common API: `promotion_task_id` — тип bigint в таблице идентификаторов, но string в примере Orchestrator
- **Файл:** `common_api.md` (таблица идентификаторов) vs `orchestrator_service_api.md` (`POST /documents/{doc_id}/approve`)
- **Место:** В `common_api.md` указано `promotion_task_id: BIGINT (sequence)`. В `orchestrator_service_api.md` пример ответа: `"promotion_task_id": "promo-task-001"` (string).
- **Проблема:** Несоответствие типа идентификатора между общей спецификацией и конкретным сервисом.

#### С-3. Common API: устаревшая ссылка на несуществующий эндпоинт `/chat/ask`
- **Файл:** `common_api.md`
- **Место:** раздел «Идемпотентность» и «Примечания по реализации»
- **Проблема:** Упоминается `POST /chat/ask` как эндпоинт, поддерживающий `Idempotency-Key`. В реальности в `query_service_api.md` нет `/chat/ask` — есть `POST /chat/sessions/{id}/messages`.

#### С-4. Gateway: `/api/v1/tasks/*` маршрутизируется, но объявлен внутренним
- **Файл:** `gateway_service_api.md` и `orchestrator_service_api.md`
- **Место:** Gateway таблица маршрутизации: `/api/v1/tasks/*` → Orchestrator. В Orchestrator: «внешние клиенты используют `/drafts/*`».
- **Проблема:** Gateway пропускает запросы к `/tasks/*`, но заявляет, что они только для администрирования. Нет описания RBAC-ограничения на этом маршруте.

#### С-5. OCR/Parser: единицы измерения размеров страницы
- **Файл:** `ocr_service_api.md`, `parser_service_api.md`
- **Место:** поле `document.pages[].width/height` — описано как "Ширина/Высота страницы в мм".
- **Проблема:** В `raw_ocr_v4` (glossary) размеры страницы и bbox — в пикселях. Converter-validator отвечает за нормализацию. Но в API OCR/Parser написано "в мм", что противоречит внутренней схеме `raw_ocr_v4`.

#### С-6. OCR/Parser: множества типов блоков не сопоставлены с Registry/RAG типами секций
- **Файл:** `ocr_service_api.md`, `parser_service_api.md`, `converter_validator_service_api.md`, `registry_service_api.md`
- **Место:** OCR/Parser `block[].type`: `heading`, `paragraph`, `text_block`, `caption`, etc. Registry `type`: `text`, `textBlock`, `headerFooter`, `table`, `list`, `image`, `formula`.
- **Проблема:** Не описано сопоставление типов между этапами. Converter-validator принимает `raw_ocr_v4`, но в его выходе (`validated_v3`) другие типы. Как `heading`/`paragraph`/`text_block` превращаются в `text`/`textBlock`/`headerFooter`?

#### С-7. Orchestrator: `POST /documents/{doc_id}/reprocess` — дублирование полей `mode` и `options.engine`
- **Файл:** `orchestrator_service_api.md`
- **Место:** раздел `POST /documents/{doc_id}/reprocess`
- **Проблема:** `mode` принимает `full`, `ocr_only`, `chunking_only`, `validation_only`, `reindex`. `options.engine` принимает `ocr_only`, `parser_only`, `full`. Поля дублируют друг друга и могут противоречить (`mode: chunking_only` + `options.engine: ocr_only`). Не описано приоритета.

#### С-8. Orchestrator: `POST /documents/{doc_id}/reprocess` ответ "аналогичен POST /drafts"
- **Файл:** `orchestrator_service_api.md`
- **Место:** ответ `POST /documents/{doc_id}/reprocess`
- **Проблема:** `POST /drafts` возвращает `draft_id`, `task_id`, `version_id`. Но при reprocess существующего документа неясно, создаётся ли новый draft. Если да — ок; если нет — структура ответа должна отличаться.

#### С-9. Query Service: несоответствие статусов сообщения в таблице и в longpoll-описании
- **Файл:** `query_service_api.md`
- **Место:** таблица "Поле `status` в сообщениях чата" содержит `processing`, `needs_clarification`, `source_conflict`. В longpoll-описании: `pending`, `enriching`, `searching`, `generating`, `enriching_citations`, `answered`, `failed`.
- **Проблема:** `processing`, `needs_clarification`, `source_conflict` не фигурируют в longpoll-логике. Не описано, являются ли они финальными, и как клиент должен на них реагировать.

#### С-10. Query Service: два формата `POST /chat/feedback` не разграничены
- **Файл:** `query_service_api.md`
- **Место:** `POST /chat/feedback`
- **Проблема:** Поддерживаются два тела запроса (с `session_id`/`message_id` и с `answer_id`). Не описано: (a) являются ли они взаимоисключающими; (b) что произойдёт, если переданы оба набора; (c) в каком сценарии какой использовать.

#### С-11. Query Service: `GET /chat/sessions/{session_id}` vs longpoll на сообщение — дублирование
- **Файл:** `query_service_api.md`
- **Место:** `GET /chat/sessions/{session_id}` поддерживает `longpoll` для обратной совместимости, но рекомендуется `GET .../messages/{message_id}?longpoll=15`.
- **Проблема:** Два эндпоинта с одинаковой функцией создают путаницу. Не описан план депрекации старого.

#### С-12. Analyse Service: отсутствуют коды ошибок
- **Файл:** `analyse_service_api.md`
- **Место:** весь документ
- **Проблема:** Нет таблицы кодов ошибок (кроме общей ссылки на common). Не описаны 400, 404, 422, 500 для конкретных эндпоинтов.

#### С-13. Converter-Validator: отсутствуют коды ошибок
- **Файл:** `converter_validator_service_api.md`
- **Место:** весь документ
- **Проблема:** Нет специфичных кодов ошибок (кроме общего `CONVERSION_FAILED`). Не описаны 400, 413, 422, 502.

#### С-14. Gateway: Rate limiting задокументирован, но не реализован
- **Файл:** `gateway_service_api.md`, `common_api.md`
- **Место:** раздел "Rate limiting"
- **Проблема:** В документации присутствуют таблицы лимитов и ответ 429, но прямо указано: "в текущей (мок) реализации rate limiting не применяется". Документация обещает поведение, которое не гарантируется кодом.

#### С-15. RAG Search: отсутствует описание кодов ошибок
- **Файл:** `rag_search_service_api.md`
- **Место:** таблица специфичных кодов содержит только 200 и 500.
- **Проблема:** Не описаны 400 (невалидный `top_k` > 100, невалидный `search_type`), 422.

#### С-16. Registry: неполнота PUT/PATCH/DELETE/Export/Import документов
- **Файл:** `registry_service_api.md`
- **Место:** разделы 3.4, 3.5, 3.10, 3.11, 3.12
- **Проблема:** Отсутствуют примеры тела запроса и ответа для PUT, PATCH, DELETE, Export, Import документов. Для импорта не описан формат файла и mapping.

#### С-17. Registry: `PATCH /registry/documents/{doc_id}/status` — security/аутентификация не описана
- **Файл:** `registry_service_api.md`
- **Место:** раздел 3.6
- **Проблема:** Эндпоинт помечен как internal (только для Orchestrator), но не описан механизм защиты (mTLS, internal token, IP whitelist).

#### С-18. Common API / OCR/Parser: противоречие о формате bbox
- **Файл:** `common_api.md` (раздел "Координаты блоков (bbox)") vs `ocr_service_api.md`/`parser_service_api.md`
- **Место:** `common_api.md` утверждает: "bbox нормализован (0..1) на всех этапах". OCR/Parser явно пишут: "Координаты в пикселях (сырые, px)". Glossary подтверждает: raw_ocr_v4 = пиксели; validated_v3 = нормализованные.
- **Проблема:** Общая спецификация врёт о едином формате на всех этапах.

#### С-19. Integration Service: `POST /meridian/export` — `document_id` тип string vs bigint
- **Файл:** `integration_service_api.md`
- **Место:** запрос `POST /meridian/export`, поле `document_id`
- **Проблема:** В таблице полей указано `document_id: string` (Да, обязательно). Во всей системе `document_id` — bigint (glossary, Registry, Orchestrator). Несоответствие типа.

#### С-20. Внутренние сервисы (OCR, Parser, Converter, RAG Builder/Search, Analyse): аутентификация не описана
- **Файл:** все internal-сервисы
- **Место:** заголовки документов
- **Проблема:** Сервисы слушают TCP-порты, но не описано, как они аутентифицируют входящие запросы от Orchestrator/Query. Только Gateway описывает JWT. Нет mTLS, API-Key или service account токенов.

---

### 🟡 КОСМЕТИЧЕСКИЕ (стилистические, не влияющие на интеграцию)

#### К-1. Auth Service: `GET /auth/me` — формат "snake_case", но `role_title` и `available_tabs` в camelCase? Нет, это тоже snake_case. OK.
#### К-2. Gateway: устаревший алиас `/api/v1/pages/*` помечен как "будет удалён после рефакторинга" — без ETA.
#### К-3. OCR Service: GET `/ocr/process/{task_id}/result` — в конце документа таблица полей выходит за пределы markdown-форматирования (нет заголовка таблицы перед полями).
#### К-4. Orchestrator: `GET /documents/{doc_id}/status` содержит очень длинные JSON-примеры, разделённые подзаголовками. Сложно навигировать.
#### К-5. Registry: модели данных (раздел 5) дублируют поля, описанные в эндпоинтах. Можно было бы вынести в отдельный файл схемы.
#### К-6. Названия эндпоинтов с глаголами: `/auth/refresh`, `/auth/revoke`, `/converter/convert`, `/analyse/compare`, `/rag/search`, `/text/search`. Согласно best practices REST, предпочтительны существительные (`/auth/tokens/refresh`, `/converter/conversions`, `/analyse/comparisons`). Однако это архитектурное решение проекта.
#### К-7. В `orchestrator_service_api.md` отсутствует пример запроса `GET /documents` с query-параметрами (фильтры, сортировка).
#### К-8. В `query_service_api.md` `POST /chat/feedback` — ответ содержит `feedback_id: "fb-001"` (string), но для запроса с `answer_id` нет привязки к `message_id`/`session_id`. Непонятна связность метрик.
#### К-9. Не во всех сервисах указана версия API в заголовках или пути (внутренние вызовы — `/api/v1`).

---

## 3. Детальные примеры с указанием файла и места

### Блокирующие

**Б-1: `rag_builder_service_api.md` — тип `drawing`**
```
| type | Как формируется чанк | Источник данных |
|------|---------------------|----------------|
| `text` | ... | ... |
| ... | ... | ... |
| `drawing` | Один чанк | `content.markdown` или ... |
```
А в `glossary.md`: Chunk (чанк) — "таблица/изображение/формула → один чанк". В Registry: `type: image`.  
**Рекомендация:** Заменить `drawing` на `image` во всём RAG Builder. Добавить mapping-таблицу OCR/Parser → Converter → Registry → RAG Builder.

**Б-2: `rag_builder_service_api.md` — `sections[].id` vs `section_id`**
```
| `sections[].id` | bigint | Да | ID секции |
```
vs пример JSON:
```json
{
  "section_id": 420001,
  "document_id": 1,
  ...
}
```
**Рекомендация:** Исправить в таблице на `sections[].section_id`.

**Б-3: `registry_service_api.md` — два формата `POST /registry/documents`**
Раздел 3.3 содержит два заголовка "Тело запроса (прямое создание)" и "Тело запроса (из пайплайна — enriched JSON от Converter-validator)".
**Рекомендация:** Явно указать: (a) режим определяется по наличию корневого поля `document`; (b) для прямого создания используется плоский список полей; (c) для пайплайна — структура `validated_v3`.

**Б-4: `registry_service_api.md` vs `orchestrator_service_api.md` — статусы**
Registry enum (4.2): `validating`, `processing`.  
Orchestrator/glossary: `parsing`, `validation`, `previewing`, `awaiting_decision`.
**Рекомендация:** Унифицировать enum или явно разделить: `registry.document_status` — финальные статусы, `orchestrator.task_status` — все статусы пайплайна.

### Серьёзные

**С-1: `auth_service_api.md` — `id` vs `role_id`**
`POST /admin/roles` ответ:
```json
{ "id": 1, "name": "knowledge_admin", ... }
```
`GET /admin/roles` ответ:
```json
{ "role_id": "r-admin", "name": "Администратор", ... }
```
**Рекомендация:** Унифицировать на `role_id` (string) или `id` (bigint) во всех эндпоинтах ролей.

**С-2: `common_api.md` vs `orchestrator_service_api.md` — `promotion_task_id`**
`common_api.md` таблица идентификаторов: `promotion_task_id | BIGINT (sequence)`.  
`orchestrator_service_api.md`: `"promotion_task_id": "promo-task-001"`.
**Рекомендация:** Исправить либо в common (string), либо в Orchestrator (bigint).

**С-3: `common_api.md` — `/chat/ask`**
```
Идемпотентность: опциональный заголовок Idempotency-Key поддерживается для POST /drafts и POST /chat/ask.
```
**Рекомендация:** Заменить `/chat/ask` на `/chat/sessions/{id}/messages`.

**С-5, С-6, С-18: `ocr_service_api.md`/`parser_service_api.md`/`common_api.md` — bbox и типы**
OCR/Parser: `block[].type` ∈ `{heading, paragraph, text_block, list, table, image, caption, formula, headerFooter}`  
Converter/Registry: `type` ∈ `{text, textBlock, headerFooter, table, list, image, formula}`  
OCR/Parser bbox: пиксели. Common: "все этапы нормализованы".
**Рекомендация:** (1) В common_api.md разделить этапы: raw_ocr_v4 → пиксели, validated_v3+ → нормализованные. (2) Добавить таблицу mapping типов OCR/Parser → Converter.

**С-7, С-8: `orchestrator_service_api.md` — reprocess**
```json
// Запрос
{
  "mode": "full",
  "options": { "engine": "paddleocr", ... }
}
```
**Рекомендация:** Убрать `options.engine` (оставить только `mode`), либо чётко описать приоритет и взаимоисключения.

**С-9, С-10, С-11: `query_service_api.md` — статусы сообщений и feedback**
Таблица статусов чата содержит `processing`, `needs_clarification`, `source_conflict`. Longpoll-логика их не упоминает. Feedback имеет два несвязанных формата.
**Рекомендация:** (1) Добавить `needs_clarification` и `source_conflict` в longpoll-описание (финальные статусы?). (2) Для feedback указать: "используйте либо формат с `session_id`+`message_id` (для новых интеграций), либо формат с `answer_id` (legacy). Передача обоих наборов — ошибка 400."

**С-14: `gateway_service_api.md` — Rate limiting**
```
Rate limiting (ограничение запросов) запланирован, пока не реализован в мок-версии.
```
**Рекомендация:** Убрать из документации обещания о 429 до реализации. Или добавить явный дисклеймер: "В текущей версии rate limiting не возвращает 429".

**С-19: `integration_service_api.md` — `document_id: string`**
```
| `document_id` | string | Да | ID документа |
```
**Рекомендация:** Исправить на `bigint`.

**С-20: Все internal-сервисы**
Ни в одном из файлов OCR, Parser, Converter, RAG Builder, RAG Search, Analyse не описано:
- Как сервис аутентифицирует входящие запросы.
- Какие заголовки ожидаются (X-Internal-Token, Authorization?).
**Рекомендация:** Добавить раздел "Аутентификация" в каждый internal-сервис: "Сервис принимает запросы только из внутренней сети. Рекомендуется mTLS или NetworkPolicy. При вызове через Gateway — JWT проверяется Gateway. Прямые вызовы между сервисами — с service-token в заголовке `X-Service-Token`".

---

## 4. Рекомендации по исправлению критичных мест (приоритеты)

### Приоритет 1 (блокирующие — исправить до начала разработки)

1. **`rag_builder_service_api.md`**:  
   - Исправить `sections[].id` → `sections[].section_id`.  
   - Убрать `drawing` из списка типов; добавить `image`, `list`, `formula`, `headerFooter` с правилами чанкинга.  
   - Свериться со `schema_registry_for_rag.json`.

2. **`registry_service_api.md` + `orchestrator_service_api.md` + `glossary.md`**:  
   - Создать единую таблицу FSM-статусов с разделением: `task_status` (Orchestrator) vs `document_status` (Registry).  
   - Убедиться, что Registry может хранить все статусы или что Orchestrator хранит промежуточные в своей схеме.

3. **`registry_service_api.md` (раздел 3.3)**:  
   - Для `POST /registry/documents` явно описать детекцию режима (по наличию поля `document` в корне).  
   - Привести два отдельных примера запроса с пометкой "Режим А / Режим Б".

### Приоритет 2 (серьёзные — исправить до интеграционного тестирования)

4. **`auth_service_api.md`**: Унифицировать `id`/`role_id` для ролей.
5. **`common_api.md`**: Исправить `promotion_task_id` тип (string vs bigint) и убрать `/chat/ask`.
6. **`ocr_service_api.md` + `parser_service_api.md` + `common_api.md`**:  
   - Поправить единицы bbox (px → мм или наоборот, согласно реальности).  
   - Добавить mapping-таблицу типов блоков OCR/Parser → типов секций Registry.
7. **`orchestrator_service_api.md`**: Упростить `POST /documents/{doc_id}/reprocess`: оставить только `mode`, убрать `options.engine`.
8. **`query_service_api.md`**:  
   - Дополнить longpoll-описание статусами `needs_clarification` и `source_conflict`.  
   - Для feedback указать взаимоисключение форматов.
9. **`gateway_service_api.md`**: Добавить RBAC-ограничение для `/api/v1/tasks/*` (только `system_admin`).
10. **Все internal-сервисы**: Добавить раздел аутентификации (service-to-service).

### Приоритет 3 (косметические — перед публикацией документации)

11. Добавить недостающие примеры запросов/ответов в Registry (PUT/PATCH/DELETE/Import/Export документов).
12. Исправить markdown-форматирование в OCR Service (таблица полей результата).
13. Добавить пример `GET /documents?source_type=GOST&page=1` в Orchestrator.
14. Унифицировать URL-пути (глаголы → существительные) или задокументировать сознательное отступление от REST.

---

## 5. Дополнительные замечания (не требующие действий, но важные для понимания)

- **Идемпотентность**: `Idempotency-Key` задокументирован только для `POST /drafts` и `POST /chat/sessions/{id}/messages`. Для массовых операций (import, batch) идемпотентность не описана.
- **Версионирование**: Внутренние вызовы между сервисами не версионируются (`/api/v1`). Это риск при rolling update.
- **CORS**: Gateway допускает `*` в development. CI-проверка production — хорошая практика, но не документирована в API (это инфраструктура).
- **Audit**: В Auth Service audit-лог маскирует IP (последний октет). Это хорошо, но не описано в API других сервисов (Orchestrator, Query) — там audit тоже нужен.
- **Soft-delete**: Единообразно применяется (documents, users, drafts). Хорошая практика.
