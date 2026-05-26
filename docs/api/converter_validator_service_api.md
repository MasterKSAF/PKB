## API Converter-validator Service (converter-validator:8086)

Сервис конвертации и валидации документов. Объединяет конвейер преобразования сырого JSON (результат Parser/OCR) в иерархический типизированный JSON с опциональным использованием LLM.

**Внутренний сервис.** Имеет два режима работы:
1. **Preview** — быстрые операции без записи в БД и без LLM (если не указано иное).
2. **Full** — полная конвертация с построением иерархии, LLM-обработкой, валидацией и кросс-ссылками.

**Базовый URL (внутренний)**: `http://127.0.0.1:8086/api/v1`

### Формат ответа

Успех — данные возвращаются напрямую.  
При ошибке: `{ "error": { "code": "CONVERSION_FAILED", "message": "...", "details": {} } }`

---

## Preview API

Эндпоинты предварительного просмотра. Выполняются быстро, без записи в БД, без полного цикла валидации.

### POST /converter/preview/metadata

Извлечение базовых метаданных из частичного сырого JSON.

**Вход:** сырой JSON (результат Parser/OCR) — может содержать неполные данные.

**Выход:** doc_code, title, document_type, year, revision.

> **Полный формат данных:** [`docs/schema/document2b_preview.json`](../schema/document2b_preview.json) (схема `converter_validator_preview_v1`)

**Запрос:**

```json
{
  "task_id": "task-8a3f2b",
  "version_id": "c4b9f2d3-...",
  "raw_json": { ... }
}
```

**Ответ `200`:**

```json
{
  "doc_code": "ГОСТ 20868-81",
  "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
  "document_type": "normative",
  "year": "1981",
  "revision": null
}
```

| Поле | Тип | Описание |
|---|---|---|
| `doc_code` | string | Обозначение документа |
| `title` | string | Полное название документа |
| `document_type` | string | Тип документа (`normative`, `drawing`, `specification`, ...) |
| `year` | string | Год издания/утверждения |
| `revision` | string\|null | Номер редакции, если применимо |

---

## Full API

Эндпоинты полного цикла конвертации и валидации.

### POST /converter/convert

Полная конвертация: построение иерархии документа, LLM-обработка, валидация, кросс-ссылки.

**Вход:** полный сырой JSON (результат Parser/OCR: все секции, таблицы, изображения, метаданные).

**Выход:** иерархический типизированный JSON (схема `validated_v3`)

> **Полный формат данных:** [`docs/schema/document2_validate.json`](../schema/document2_validate.json) (схема `validated_v3`)

**Процесс внутри:**

| Шаг | Действие | Зависимости |
|---|---|---|
| 1 | Построение иерархии документа | Нет |
| 2 | LLM-обработка (если `use_llm = true`) | Шаг 1 |
| 3 | Извлечение и валидация метаданных | Шаг 1–2 |
| 4 | Валидация структуры JSON | Шаг 1 |
| 5 | Классификация документа (тип, эра, юрисдикция) | Шаг 3 |
| 6 | Вычисление хэшей SHA-256 (content_hash, title_hash) | Шаг 3 |
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
  "task_id": "task-8a3f2b",
  "version_id": "c4b9f2d3-...",
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
  "task_id": "task-8a3f2b",
  "version_id": "c4b9f2d3-...",
  "document_id": "b3a8f1c2-...",
  "metadata": {
    "schema": "validated_v3",
    "task_id": "task-8a3f2b",
    "created_at": "2026-05-17T09:15:00Z",
    "parser": {
      "name": "docling",
      "version": "2.1.0",
      "ocr_engine": "paddleocr",
      "ocr_fallback": false
    }
  },
  "document": {
    "source": {
      "file_name": "GOST_20868-81_scan.pdf",
      "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "page_count": 2
    },
    "metadata": {
      "doc_code": "ГОСТ 20868-81",
      "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
      "normalized_title": "стойки установочные крепежные технические требования",
      "group": "ПО4",
      "mks_oks_code": "31.240",
      "okstu_code": null,
      "udc": null,
      "era": "USSR",
      "validity_status": "active",
      "issuing_body": "Государственный Комитет СССР по стандартам",
      "adoption": {
        "date": "1981-04-15",
        "authority": "Государственный Комитет СССР по стандартам",
        "document_number": "1983",
        "effective_from": "1982-07-01"
      },
      "replaces": "ГОСТ 20868-75",
      "validity_restriction_removed": {
        "date": "1992-09-10",
        "authority": "Госстандарт",
        "document_number": "1166"
      },
      "amendments": [
        { "type": "Изменение № 1", "source": "ИУС 4-87", "affected_clauses": ["6.4"], "note": null },
        { "type": "Поправка", "source": "ИУС 5-82", "affected_clauses": ["2"], "note": null }
      ],
      "status_note": "С 01.07.2005 введены ГОСТ 24705-2004 и ГОСТ 16093-2004",
      "title_hash_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    },
    "content": [
      {
        "clause": "1",
        "title": null,
        "level": 1,
        "parent_clause": null,
        "path": "1",
        "page": 1,
        "bbox": [10, 20, 200, 40],
        "type": "section",
        "content": {
          "text": "Настоящий стандарт распространяется...",
          "amendments": []
        }
      },
      {
        "clause": "6.1",
        "title": "Допуск соосности при степени точности",
        "level": 2,
        "parent_clause": "6",
        "path": "6.1.table1",
        "page": 2,
        "bbox": [10, 150, 200, 250],
        "type": "table",
        "content": {
          "caption": "Допуск соосности при степени точности",
          "columns": [
            { "name": "L_range", "header": "L, мм", "index": 0, "type": "range", "value_type": "number", "unit": "мм" },
            { "name": "normal", "header": "нормальная", "index": 1, "type": "value", "value_type": "number", "unit": "мм" },
            { "name": "high", "header": "повышенная", "index": 2, "type": "value", "value_type": "number", "unit": "мм" }
          ],
          "rows": [
            {
              "row_index": 0, "type": "data",
              "cells": {
                "L_range": { "label": "От 6 до 50", "range": { "min": 6, "max": 50, "min_inclusive": true, "max_inclusive": true } },
                "normal": { "value": 0.1 },
                "high": { "value": 0.05 }
              }
            }
          ],
          "footnotes": [
            { "footnote_id": 1, "text": "Значения допусков соосности...", "applies_to": "whole_table" }
          ],
          "amendments": [
            { "amendment_id": "amd_1", "type": "Изменение № 1", "source": "ИУС 4-87", "affected_columns": ["normal", "high"], "action": "values_updated", "note": "Изменены допуски" }
          ],
          "image_key": "purgatory/assets/a1b2c3d4/tables/t1.png"
        }
      },
      {
        "clause": "6.1",
        "title": "Черт. 1 – Схема допуска соосности",
        "level": 2,
        "parent_clause": "6",
        "path": "6.1.fig1",
        "page": 2,
        "bbox": [30, 260, 180, 300],
        "type": "image",
        "content": {
          "caption": "Черт. 1 – Схема допуска соосности",
          "image_key": "purgatory/assets/a1b2c3d4/fig1.png",
          "description": "Схема для определения допуска соосности"
        }
      },
      {
        "clause": "6.1",
        "title": "Формула допуска соосности",
        "level": 2,
        "parent_clause": "6",
        "path": "6.1.formula1",
        "page": 1,
        "bbox": [100, 140, 180, 160],
        "type": "formula",
        "content": {
          "latex": "R_{\\text{доп}} = \\frac{\\Delta}{2}",
          "meaning": "Формула расчёта допустимого радиуса...",
          "image_key": "purgatory/assets/a1b2c3d4/formulas/eq1.png",
          "parameters": [
            { "symbol": "R_{\\text{доп}}", "description": "Допустимый радиус", "unit": "мм" },
            { "symbol": "\\Delta", "description": "Заданное отклонение", "unit": "мм" }
          ]
        }
      }
    ],
    "terminology": [
      {
        "term": "стойка установочная крепежная",
        "definition": "Металлическая деталь для монтажа радиоэлектронной аппаратуры.",
        "source_clause": "1",
        "normalized_term": "стойка установочная крепежная"
      }
    ],
    "references": [
      {
        "target_doc_code": "ГОСТ 20862-81 – ГОСТ 20867-81",
        "type": "range",
        "context": "изготовление крепежных установочных стоек",
        "current_status": "active",
        "note": null
      },
      {
        "target_doc_code": "ГОСТ 24705-81",
        "type": "single",
        "context": "резьбы",
        "current_status": "superseded",
        "replaced_by": "ГОСТ 24705-2004",
        "replacement_date": "2005-07-01"
      }
    ]
  },
  "validation": {
    "validation_id": "val-001",
    "structure_valid": true,
    "classification": {
      "mks_oks_code": "47.020",
      "mks_status": "CONFIRMED",
      "okstu_status": "NOT_USED",
      "udk_code": "629.5.021",
      "overall_status": "CONFIRMED"
    },
    "fingerprint": {
      "content_hash_sha256": "abc123...",
      "title_hash_sha256": "def456..."
    },
    "matching": {
      "predecessor_doc_id": null,
      "successor_doc_id": null
    },
    "cross_references": [],
    "decision": "auto",
    "status": "completed"
  },
  "llm_usage": {
    "model": "gpt-4o-mini",
    "tokens_used": 2048,
    "processing_time_ms": 3200
  }
}
```

**Поля ответа (верхний уровень):**

| Поле | Тип | Описание |
|---|---|---|
| `task_id` | string | ID задачи, переданный в запросе |
| `version_id` | string | ID версии файла, переданный в запросе |
| `document_id` | string | ID документа. Назначается при конвертации: извлекается существующий для дубликата, либо генерируется новый |
| `metadata` | object | Служебные метаданные ответа (схема, дата, информация о парсере) |
| `document` | object | Полная структура документа: источник, метаданные, контент, терминология, ссылки |
| `validation` | object | Результаты полной валидации (структура, классификация, fingerprint, сопоставление, кросс-ссылки) |
| `llm_usage` | object | Статистика использования LLM (если `use_llm = true`) |

**Поля `metadata`:**

| Поле | Тип | Описание |
|---|---|---|
| `schema` | string | Идентификатор схемы ответа — `"validated_v3"` |
| `created_at` | string (datetime) | Дата и время формирования ответа |
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
| `udc` | string | Код УДК (может быть `null`) |
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
| `content[].type` | string | Тип секции: `section`, `table`, `image`, `formula` |
| `content[].content` | object | Объектный контент, структура зависит от `type` |

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
| `fingerprint` | object | Хэши документа (`content_hash_sha256`, `title_hash_sha256`) |
| `matching` | object | Связи с существующими документами (`predecessor_doc_id`, `successor_doc_id`) |
| `cross_references` | array | Список кросс-ссылок на другие документы |
| `decision` | string | `auto` — автоматическое продвижение, `review_required` — требуется ручное подтверждение |
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
  "task_id": "task-8a3f2b",
  "version_id": "c4b9f2d3-...",
  "raw_json": { ... }
}
```

**Ответ `200`:**

```json
{
  "validation_id": "val-001",
  "document_id": "b3a8f1c2-...",
  "structure_valid": true,
  "classification": {
    "mks_oks_code": "47.020",
    "mks_status": "CONFIRMED",
    "okstu_status": "NOT_USED",
    "udk_code": "629.5.021",
    "overall_status": "CONFIRMED"
  },
  "fingerprint": {
    "content_hash_sha256": "abc123...",
    "title_hash_sha256": "def456..."
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
| `document_id` | string | ID документа. Назначается валидацией: извлекается существующий для дубликата, либо генерируется новый. |
| `structure_valid` | bool | Результат проверки структуры |
| `classification` | object | Статусы классификационных кодов |
| `fingerprint` | object | Хэши документа (`content_hash_sha256`, `title_hash_sha256`) |
| `matching` | object | Связи с существующими документами |
| `decision` | string | `auto` — автоматическое продвижение, `review_required` — требуется ручное подтверждение |
| `status` | string | Статус: `completed`, `failed` |

> **Внутренние функции валидации:**
> - `/validate/classifiers` — валидация классификационных кодов по справочнику Registry.
> - `/validate/check` — проверка текста на соответствие набору правил.
> - `/validate/extract/parameters` — извлечение структурированных параметров из документов (спецификации, материалы, размеры).
>
> Эти эндпоинты являются внутренними и вызываются Orchestrator'ом или Analyse Service по мере необходимости.
> Детальное описание форматов запроса/ответа — во внутренней документации сервиса.

---

## Сводная информация

| Аспект | Значение |
|---|---|
| Доступ к БД | **Нет** (сервис не пишет и не читает БД напрямую; при необходимости данные передаются через Orchestrator) |
| LLM | Опционально (управляется параметром `use_llm`) |
| Режимы | Preview (быстрые проверки) + Full (полный цикл конвертации и валидации) |
| Пайплайн | 1 (Формирование документа), Этап 1.5 (Converter-validator) |
| Вход | Raw JSON (частичный — для Preview, полный — для Full) |
| Выход | Иерархический типизированный JSON (схема `validated_v3`) с результатами валидации |

### Матрица эндпоинтов

| Метод | Путь | Режим | Описание | Запись в БД |
|---|---|---|---|---|
| `POST` | `/converter/preview/metadata` | Preview | Извлечение базовых метаданных (doc_code, title, document_type, year, revision) | Нет |
| `POST` | `/converter/convert` | Full | Полная конвертация + валидация + LLM + кросс-ссылки (схема `validated_v3`) | Нет |
| `POST` | `/validate/document` | Standalone | Комплексная валидация документа без переконвертации | Нет |

