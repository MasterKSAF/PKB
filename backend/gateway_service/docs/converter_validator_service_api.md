## API Converter-validator Service (converter-validator:8086)

Сервис конвертации и валидации документов. Объединяет конвейер преобразования сырого JSON (результат Parser/OCR) в иерархический типизированный JSON с опциональным использованием LLM.

> **Спецификация сервиса (алгоритмы, сценарии, архитектура «чёрного ящика»):** [`docs/specifications/converter_specification.md`](../specifications/converter_specification.md)

**Внутренний сервис.** Имеет два режима работы:
1. **Preview** — быстрые операции без записи в БД и без LLM (если не указано иное).
2. **Full** — полная конвертация с построением иерархии, LLM-обработкой, валидацией и кросс-ссылками.

**Базовый URL (внутренний)**: `http://127.0.0.1:8086/api/v1`

### Формат ответа

Успех — данные возвращаются напрямую.  
При ошибке: `{ "error": { "code": "...", "message": "...", "details": {} } }`

**Специфичные коды ошибок:**
| HTTP | `error.code` | Описание |
|------|-------------|----------|

---

## Межсервисное взаимодействие

Авторизацию контролирует только Gateway. Внутренние сервисы не имеют своей аутентификации — см. [common_api.md](common_api.md#межсервисное-взаимодействие).

| 400 | `INVALID_INPUT` | Входной JSON не соответствует схеме `raw_ocr_v4` |
| 422 | `METADATA_EXTRACTION_FAILED` | Не удалось извлечь обязательные метаданные (doc_code, title) |
| 422 | `VALIDATION_FAILED` | Ошибка валидации структуры документа |
| 500 | `CONVERSION_FAILED` | Ошибка конвертации (общая) |
| 502 | `LLM_TIMEOUT` | Таймаут LLM-запроса |
| 504 | `REGISTRY_TIMEOUT` | Таймаут при проверке классификаторов в Registry |

---

## Preview API

Эндпоинты предварительного просмотра. Выполняются быстро, без записи в БД, без полного цикла валидации.

### POST /converter/preview

Извлечение метаданных из частичного сырого JSON (первые N страниц).

**Вход:** сырой JSON (результат Parser/OCR) — может содержать неполные данные.

**Выход:** см. [_schemas.md](_schemas.md#PreviewMetadata) — preview-метаданные (14 полей, без бизнес-ключа).

> **Полный формат данных:** [`docs/schema/schema_converter_preview.json`](../schema/schema_converter_preview.json) (схема `converter_validator_preview_v1`)

**Запрос:**

```json
{
  "task_id": 420000,
  "version_id": 420001,
  "raw_json": { ... }
}
```

**Ответ `200`:**

```json
{
  "doc_code": "311-05-1950ц",
  "title": "ЦИРКУЛЯРНОЕ ПИСЬМО № 311-05-1950ц от 09.06.2023",
  "mks_oks_code": null,
  "okstu_code": null,
  "udk_code": null,
  "pkb_codes": [],
  "document_type": "normative",
  "year": 2023,
  "era": "CURRENT",
  "validity_status": "active",
  "issuing_body": "РОССИЙСКИЙ МОРСКОЙ РЕГИСТР СУДОХОДСТВА",
  "jurisdiction": "RU",
  "source_type": "RMRS",
  "language": "ru"
}
```

> 📖 **Схема полей PreviewMetadata** — [_schemas.md](_schemas.md#PreviewMetadata).

---

## Full API

Эндпоинты полного цикла конвертации и валидации.

### POST /converter/convert

Полная конвертация: построение иерархии документа, LLM-обработка, валидация, кросс-ссылки.

**Вход:** полный сырой JSON (результат Parser/OCR: все секции, таблицы, изображения, метаданные).

**Выход:** иерархический типизированный JSON (схема `validated_v3`)

> ⚠️ **Полный формат данных:** [`docs/schema/schema_converter_result.json`](../schema/schema_converter_result.json) (схема `validated_v3`) — **обязательно** смотри этот файл, здесь приведён только сокращённый пример.

**Процесс внутри:**

| Шаг | Действие | Зависимости |
|---|---|---|
| 1 | Построение иерархии документа | Нет |
| 2 | LLM-обработка (если `use_llm = true`) | Шаг 1 |
| 3 | Извлечение и валидация метаданных | Шаг 1–2 |
| 4 | Валидация структуры JSON | Шаг 1 |
| 5 | Классификация документа (тип, эра, юрисдикция) | Шаг 3 |
| 6 | Вычисление хэшей SHA-256 (content_hash, title_hash, title_key) | Шаг 3 |
| 7 | Сопоставление с существующими документами (predecessor/successor) | Шаг 3 |
| 8 | Валидация классификационных кодов (через Registry) | Шаг 5 |
| 9 | Построение кросс-ссылок | Шаг 1, 7 |

**LLM-параметры** (передаются в корне запроса):

| Поле | Тип | Описание | По умолчанию |
|---|---|---|---|
| `use_llm` | bool | Включить LLM-обработку | `false` |
| `llm_model` | string | Модель LLM (например, `gpt-4o`, `gpt-4o-mini`) | `"gpt-4o-mini"` |
| `llm_max_tokens` | int | Максимальное количество токенов на запрос | `4096` |
| `llm_timeout` | int | Таймаут LLM-запроса в секундах | `60` |

**Запрос:**

```json
{
  "task_id": 420000,
  "version_id": 420001,
  "use_llm": true,
  "llm_model": "gpt-4o-mini",
  "llm_max_tokens": 4096,
  "llm_timeout": 60,
  "raw_json": { ... }
}
```

**Ответ `200` (схема `validated_v3`):**

```json
{
  "task_id": 420000,
  "version_id": 420001,
  "metadata": {
    "schema": "validated_v3",
    "task_id": 420000,
    "created_at": "2026-05-17T09:15:00Z",
    "parser": { "name": "docling", "version": "2.1.0", "ocr_engine": "paddleocr", "ocr_fallback": false }
  },
  "document": {
    "source": { "file_name": "GOST_20868-81_scan.pdf", "file_hash_sha256": "...", "page_count": 2 },
    "metadata": {
      "doc_code": "ГОСТ 20868-81",
      "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования"
    },
    "content": [
      {
        "clause": "1",
        "level": 1,
        "path": "1",
        "page": 1,
        "bbox": [0.05, 0.056, 1.0, 0.111],
        "type": "text",
        "content": { "text": "Настоящий стандарт распространяется..." }
      }
    ],
    "terminology": [],
    "references": []
  },
  "validation": {
    "validation_id": 1,
    "structure_valid": true,
    "classification": { "mks_oks_code": "47.020", "overall_status": "CONFIRMED" },
    "fingerprint": { "file_hash_sha256": "...", "title_hash_sha256": "...", "title_key": "..." },
    "matching": { "predecessor_doc_id": null, "successor_doc_id": null },
    "decision": "auto",
    "status": "completed"
  },
  "llm_usage": { "model": "gpt-4o-mini", "tokens_used": 2048, "processing_time_ms": 3200 }
}
```

> **Полный формат данных:** см. [`docs/schema/schema_converter_result.json`](../schema/schema_converter_result.json) (схема `validated_v3`).
> Приведённый ниже пример — сокращённый. Все типы секций и полный состав полей — в эталонном JSON.

**Поля ответа (верхний уровень):**

| Поле | Тип | Описание |
|---|---|---|
| `task_id` | bigint | ID задачи, переданный в запросе |
| `version_id` | bigint | ID версии файла, переданный в запросе |
| `metadata` | object | Служебные метаданные ответа (схема, дата, информация о парсере) |
| `document` | object | Полная структура документа: источник, метаданные, контент, терминология, ссылки |
| `validation` | object | Результаты полной валидации (структура, классификация, fingerprint, сопоставление, кросс-ссылки) |
| `llm_usage` | object | Статистика использования LLM (если `use_llm = true`) |

**Поля `metadata`:**

| Поле | Тип | Описание |
|---|---|---|
| `schema` | string | Идентификатор схемы ответа — `"validated_v3"` |
| `created_at` | datetime | Дата и время формирования ответа (ISO 8601) |
| `parser` | object | Информация о парсере, выполнившем первичную обработку |

**Поля `document.source`:**

| Поле | Тип | Описание |
|---|---|---|
| `file_name` | string | Имя исходного файла |
| `file_hash_sha256` | string | SHA-256 хеш исходного файла |
| `page_count` | int | Количество страниц |

**Поля `document.metadata`:**

| Поле | Тип | Описание |
|---|---|---|
| `doc_code` | string | Обозначение документа (например, `ГОСТ 20868-81`) |
| `title` | string | Полное название документа |
| `normalized_title` | string | Нормализованное название (для поиска) |
| `title_hash_sha256` | string | SHA-256 хеш названия (бизнес-ключ) |
| `group` | string | Группа классификации (например, `ПО4`) |
| `mks_oks_code` | string | Код МКС/ОКС |
| `okstu_code` | string | Код ОКСТУ (может быть `null`) |
| `udk_code` | string | **D-51**: переименовано из `udc`. Код УДК (может быть `null`) |
| `era` | string | Историческая эра (`USSR`, `RF`, ...) |
| `validity_status` | string | Статус действия (`active`, `superseded`, ...) |
| `issuing_body` | string | Орган, утвердивший документ |
| `adoption` | object | Информация о принятии (дата, орган, номер, дата введения) |
| `replaces` | string | Какой документ заменяет данный |
| `validity_restriction_removed` | object | Информация о снятии ограничения срока действия |
| `amendments` | array | Список изменений/поправок к документу |
| `status_note` | string | Примечание о статусе |

**Поля `document.content`:**

| Поле | Тип | Описание |
|---|---|---|
| `content` | array | Единый плоский массив секций документа |
| `content[].clause` | string | Номер пункта/раздела |
| `content[].title` | string | Заголовок секции (может быть `null`) |
| `content[].level` | int | Уровень вложенности |
| `content[].parent_clause` | string | Родительский пункт |
| `content[].path` | string | Путь к секции (уникальный идентификатор в рамках документа) |
| `content[].page` | int | Номер страницы |
| `content[].bbox` | array | Координаты bounding box `[x1, y1, x2, y2]` |
| `content[].type` | string | Тип секции: `text`, `table`, `image`, `formula`, `list`, `headerFooter`, `textBlock` |
| `content[].content` | object | Объектный контент, структура зависит от `type`. `list`: `{ numbering_style, items[] }`. `headerFooter`: `{ text }`. `textBlock`: `{ block[] }` с элементами `{ font, content }`. |

**Поля `document.terminology`:**

| Поле | Тип | Описание |
|---|---|---|
| `term` | string | Термин |
| `definition` | string | Определение |
| `source_clause` | string | Пункт, где встречается термин |
| `normalized_term` | string | Нормализованная форма термина |

**Поля `document.references`:**

| Поле | Тип | Описание |
|---|---|---|
| `target_doc_code` | string | Обозначение целевого документа |
| `type` | string | Тип ссылки: `single`, `range` |
| `context` | string | Контекст ссылки |
| `current_status` | string | Статус целевого документа (`active`, `superseded`, ...) |
| `note` | string | Примечание (может быть `null`) |
| `replaced_by` | string | Новый документ, заменивший целевой (если `superseded`) |
| `replacement_date` | string | Дата замены |

**Поля `validation`:**

| Поле | Тип | Описание |
|---|---|---|
| `validation_id` | string | ID валидации |
| `structure_valid` | bool | Результат проверки структуры |
| `classification` | object | Статусы классификационных кодов |
| `fingerprint` | object | Хэши документа (`file_hash_sha256`, `title_hash_sha256`, `title_key`) |
| `matching` | object | Связи с существующими документами (`predecessor_doc_id`, `successor_doc_id`) |
| `cross_references` | array | Список кросс-ссылок на другие документы |
| `decision` | string | `auto` — автоматическое завершение, `manual` — требуется ручное подтверждение |
| `status` | string | Статус: `completed`, `failed` |

---

## Отдельные эндпоинты валидации (`/validate/*`)

Эндпоинты валидации могут вызываться как часть полного цикла `/converter/convert` (шаги 4–8), так и отдельно для повторной проверки отдельных аспектов документа.

### POST /validate/document

Комплексная валидация документа.  
Принимает JSON-контейнер, выполняет все проверки (структура, классификация, уникальность, сопоставление).

**Запрос:**

```json
{
  "task_id": 420000,
  "version_id": 420001,
  "raw_json": { ... }
}
```

**Ответ `200`:**

```json
{
  "validation_id": 1,
  "structure_valid": true,
  "classification": {
    "mks_oks_code": "47.020",
    "mks_status": "CONFIRMED",
    "okstu_status": "NOT_USED",
    "udk_code": "629.5.021",
    "overall_status": "CONFIRMED"
  },
  "fingerprint": {
    "file_hash_sha256": "abc123...",
    "title_hash_sha256": "def456...",
    "title_key": "USSR|gost|47.020||20868-81|стойки..."
  },
  "matching": {
    "predecessor_doc_id": null,
    "successor_doc_id": null
  },
  "decision": "auto",
  "status": "completed"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `validation_id` | string | ID валидации |
| `structure_valid` | bool | Результат проверки структуры |
| `classification` | object | Статусы классификационных кодов |
| `fingerprint` | object | Хэши документа (`file_hash_sha256`, `title_hash_sha256`, `title_key`) |
| `matching` | object | Связи с существующими документами |
| `decision` | string | `auto` — автоматическое завершение, `manual` — требуется ручное подтверждение |
| `status` | string | Статус: `completed`, `failed` |

---

### POST /validate/metadata

Валидация и нормализация метаданных. **Единственная точка вычисления `title_hash_sha256`/`title_key` при ручных правках метаданных.**

Принимает поля метаданных напрямую (без `raw_json`), нормализует название (терминологический реестр, lowercasing, детект аватаров), приводит `source_type` и `era` к нижнему регистру, вычисляет бизнес-ключ.

**Используется:**
- Orchestrator при `PATCH /drafts/{id}/metadata` (ручные правки метаданных)
- Orchestrator при `PATCH /drafts/{id}/decide` с `metadata_overrides`

**Запрос:**

```json
{
  "era": "USSR",
  "source_type": "GOST",
  "mks_oks_code": "47.020",
  "okstu_code": null,
  "doc_code": "20868-81",
  "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|---------------|----------|
| `era` | string | Да | `USSR`, `CIS`, `RF`, `CURRENT` |
| `source_type` | string | Да | `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `RMRS`, `OTHER` |
| `mks_oks_code` | string \| null | Нет | Код МКС/ОКС |
| `okstu_code` | string \| null | Нет | Код ОКСТУ |
| `doc_code` | string | Да | Регистрационный номер документа |
| `title` | string | Да | Название документа (сырое, до нормализации) |

**Ответ `200`:**

```json
{
  "title_hash_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "title_key": "USSR|gost|47.020||20868-81|стойки установочные крепежные",
  "normalized_title": "стойки установочные крепежные",
  "source_type_normalized": "gost",
  "era_normalized": "ussr"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `title_hash_sha256` | string | SHA-256 бизнес-ключа (6-польная формула по `normalizer_specification.md` §2.1) |
| `title_key` | string | Исходная строка конкатенации для аудита |
| `normalized_title` | string | Нормализованное название (lowercase, аватары заменены) |
| `source_type_normalized` | string | `source_type` в нижнем регистре (как используется в хеше) |
| `era_normalized` | string | `era` в нижнем регистре |

**Коды ошибок:**

| HTTP | `error.code` | Описание |
|------|-------------|----------|
| 400 | `VALIDATION_ERROR` | Некорректные или отсутствующие обязательные поля |
| 422 | `NORMALIZATION_FAILED` | Ошибка нормализации названия |

---

> **Внутренние функции валидации:**
> - `/validate/classifiers` — валидация классификационных кодов по справочнику Registry.
> - `/validate/check` — проверка текста на соответствие набору правил.
> - `/validate/extract/parameters` — извлечение структурированных параметров из документов (спецификации, материалы, размеры).
>
> Эти эндпоинты являются внутренними и вызываются Orchestrator'ом (для пост-обработки документа) или Analyse Service (для анализа проектных решений).
> Детальное описание форматов запроса/ответа — во внутренней документации сервиса.

---

## Сводная информация

| Аспект | Значение |
|---|---|
| Доступ к БД | **Нет** (сервис изолирован от БД; данные для работы получает через Orchestrator в теле запроса) |
| LLM | Опционально (управляется параметром `use_llm`) |
| Режимы | Preview (быстрые проверки) + Full (полный цикл конвертации и валидации) |
| Пайплайн | 1 (Формирование документа), Этап 1.5 (Converter-validator) |
| Вход | Raw JSON (частичный — для Preview, полный — для Full) |
| Выход | Иерархический типизированный JSON (схема `validated_v3`) с результатами валидации |

### Матрица эндпоинтов

| Метод | Путь | Режим | Описание | Запись в БД |
|---|---|---|---|---|
| `POST` | `/converter/preview` | Preview | Извлечение метаданных — см. [_schemas.md](_schemas.md#PreviewMetadata). **Без** бизнес-ключа | Нет |
| `POST` | `/converter/convert` | Full | Полная конвертация + валидация + LLM + кросс-ссылки (схема `validated_v3`) | Нет |
| `POST` | `/validate/document` | Standalone | Комплексная валидация документа без переконвертации | Нет |
| `POST` | `/validate/metadata` | Validate | **Единая точка** нормализации метаданных и вычисления бизнес-ключа. Принимает поля напрямую, без `raw_json` | Нет |

