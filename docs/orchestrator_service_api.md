**

#### 1. Документы (UC‑01, UC‑02, UC‑08, UC‑09)

##### POST /documents

Загрузка документа в очередь обработки.

Запрос (multipart/form-data):

- file – бинарный файл (PDF, PNG, JPG, TIFF)
  
- document_type – строка, enum:  
  normative (нормативный документ) / archival_scan (архивный скан) / drawing (чертёж) / specification (спецификация)
  
- metadata (опционально) – JSON-строка с произвольными метаданными.
  

Пример запроса (curl):

bash

curl -X POST https://host/api/v1/documents \

  -H "Authorization: Bearer ..." \

  -F "file=@21900M2_spec.pdf" \

  -F "document_type=specification" \

  -F 'metadata={"project":"21900M2","author":"Иванов"}'

Ответ 201:

json

{

  "document_id": "doc-8a3f2b",

  "status": "queued",

  "task_id": "task-ocr-001",

  "created_at": "2026-04-27T10:00:00Z"

}

Ошибки: 400 – неподдерживаемый формат/размер, 422 – повреждённый файл.

##### GET /documents

Список документов с фильтрацией.  
Параметры query: status (queued/processing/processed/error), type (enum как выше), date_from, date_to, search (по имени файла), limit, offset.

Ответ 200:

json

{

  "documents": [

    {

      "document_id": "doc-8a3f2b",

      "filename": "21900M2_spec.pdf",

      "document_type": "specification",

      "status": "processing",

      "pages_total": 12,

      "pages_processed": 5,

      "created_at": "2026-04-27T10:00:00Z",

      "updated_at": "2026-04-27T10:02:00Z"

    }

  ],

  "total": 18,

  "limit": 20,

  "offset": 0

}

##### GET /documents/{doc_id}

Детальная информация о документе.  
Ответ 200:

json

{

  "document_id": "doc-8a3f2b",

  "filename": "21900M2_spec.pdf",

  "document_type": "specification",

  "status": "processed",

  "file_size": 2048576,

  "pages_total": 12,

  "pages_processed": 12,

  "pages_failed": 0,

  "created_at": "2026-04-27T10:00:00Z",

  "updated_at": "2026-04-27T10:05:00Z",

  "metadata": {

    "project": "21900M2",

    "author": "Иванов"

  }

}

##### GET /documents/{doc_id}/status

Прогресс обработки документа.  
Ответ 200:

json

{

  "document_id": "doc-8a3f2b",

  "status": "processing",

  "progress_percent": 41.7,

  "steps": {

    "ocr": "in_progress",

    "layout_parsing": "pending",

    "indexing": "pending"

  },

  "started_at": "2026-04-27T10:00:30Z",

  "estimated_completion": "2026-04-27T10:06:00Z"

}

##### DELETE /documents/{doc_id}

Удаление документа и всех связанных данных.  
Ответ 200:

json

{

  "document_id": "doc-8a3f2b",

  "deleted_at": "2026-04-27T10:30:00Z"

}

##### POST /documents/{doc_id}/reprocess

Повторная обработка документа (UC‑08).  
Запрос:

json

{

  "mode": "enhanced_preprocess"

}

mode (enum): standard, enhanced_preprocess (усиленная фильтрация), fallback_ocr (использовать резервный OCR-движок).  
Ответ 200:

json

{

  "document_id": "doc-8a3f2b",

  "task_id": "task-ocr-002",

  "status": "reprocessing_queued",

  "mode": "enhanced_preprocess",

  "created_at": "2026-04-27T11:00:00Z"

}

##### GET /documents/{doc_id}/errors

Журнал ошибок обработки (UC‑09).  
Параметры query: stage (upload/ocr/parsing/indexing/generation), severity (warning/error), limit, offset.  
Ответ 200:

json

{

  "errors": [

    {

      "error_id": "err-001",

      "document_id": "doc-8a3f2b",

      "page_number": 5,

      "stage": "ocr",

      "error_code": "LOW_CONFIDENCE",

      "error_message": "Качество распознавания страницы ниже порога (confidence=0.62)",

      "severity": "warning",

      "retry_attempt": 0,

      "timestamp": "2026-04-27T10:01:00Z"

    }

  ],

  "total": 1

}

---

#### 2. Поиск и вопросно-ответная система (UC‑03, UC‑04)

##### POST /search

Семантический поиск фрагментов.

Запрос:

json

{

  "query": "требования к ледовому классу Arc4",

  "document_ids": ["doc-norm-001", "doc-norm-002"],

  "top_k": 5,

  "filters": {

    "document_type": ["normative"],

    "date_from": "2020-01-01",

    "date_to": null

  }

}

- document_ids – опционально, ограничивает поиск конкретными документами.
  
- top_k – число результатов (по умолчанию 5).
  
- filters – дополнительные фильтры по типу, дате и т.д.
  

Ответ 200:

json

{

  "query": "требования к ледовому классу Arc4",

  "results": [

    {

      "fragment_id": "frg-123abc",

      "document_id": "doc-norm-001",

      "document_title": "Правила классификации и постройки морских судов. Часть I",

      "page_number": 42,

      "text": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм...",

      "coordinates": {

        "x": 120, "y": 350, "width": 400, "height": 60

      },

      "score": 0.92,

      "document_type": "normative"

    }

  ],

  "total_found": 3,

  "processing_time_ms": 450

}

Ошибки: 400 – пустой запрос, 404 – ничего не найдено (возвращает пустой список).

##### GET /search

Быстрый GET-вариант (параметры в query string).  
?q=ледовый класс Arc4&document_id=doc-norm-001&page=1&limit=5  
Ответ аналогичен POST.

##### POST /ask

Генерация ответа с источниками. Поддерживает два режима: потоковый и обычный.

Запрос:

json

{

  "question": "Какая должна быть толщина обшивки для ледового класса Arc4?",

  "document_ids": null,

  "stream": false,

  "options": {

    "temperature": 0.2

  }

}

- stream – если true, то ответ возвращается через SSE (Server‑Sent Events).
  
- document_ids – опциональное ограничение корпуса.
  

Ответ 200 (stream: false):

json

{

  "question": "Какая должна быть толщина обшивки для ледового класса Arc4?",

  "answer": "Согласно Правилам классификации и постройки морских судов (Часть I, стр. 42), толщина обшивки для ледового класса Arc4 должна быть не менее 12 мм.",

  "sources": [

    {

      "document_id": "doc-norm-001",

      "document_title": "Правила классификации и постройки морских судов. Часть I",

      "page_number": 42,

      "fragment_id": "frg-123abc",

      "text": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм...",

      "score": 0.92

    }

  ],

  "processing_time_ms": 3200,

  "model_used": "llama-3-70b"

}

Потоковый режим (stream: true) – ответ в формате SSE:

text

event: delta

data: {"text": "Согласно Правилам классификации"}

event: delta

data: {"text": " и постройки морских судов"}

event: source

data: {"document_id":"doc-norm-001","page_number":42,"fragment_id":"frg-123abc","text":"..."}

event: done

data: {"sources":[...], "processing_time_ms":3100, "model_used":"llama-3-70b"}

---

#### 3. Просмотр документа и фрагментов (UC‑07)

##### GET /documents/{doc_id}/pages/{page_num}

Изображение страницы с опциональной подсветкой блока.

Параметры query: highlight – идентификатор блока (block_id) для подсветки.

Ответ 200:

json

{

  "image_url": "/files/page-img/doc-8a3f2b_5.png",

  "page_number": 5,

  "width": 2480,

  "height": 3508,

  "blocks": [

    {

      "block_id": "blk-001",

      "type": "title_block",

      "coordinates": {"x": 200, "y": 100, "width": 800, "height": 50},

      "text": "Спецификация 21900M2.362135.0903",

      "highlighted": false

    },

    {

      "block_id": "blk-002",

      "type": "table",

      "coordinates": {"x": 150, "y": 200, "width": 1800, "height": 600},

      "text": "...",

      "highlighted": true

    }

  ]

}

##### GET /documents/{doc_id}/pages/{page_num}/text

Текстовый слой и структура страницы (без изображения).

Ответ 200:

json

{

  "page_number": 5,

  "full_text": "Спецификация...\nПоз. 1 Кница...",

  "blocks": [

    {

      "block_id": "blk-001",

      "type": "title_block",

      "coordinates": {"x": 200, "y": 100, "width": 800, "height": 50},

      "text": "Спецификация 21900M2.362135.0903",

      "confidence": 0.98

    },

    {

      "block_id": "blk-002",

      "type": "table",

      "coordinates": {"x": 150, "y": 200, "width": 1800, "height": 600},

      "text": "Поз.|Наименование|Кол.|Масса|Материал",

      "confidence": 0.92,

      "table_data": [

        ["Поз.", "Наименование", "Кол.", "Масса", "Материал"],

        ["1", "Кница", "2", "0.5", "сталь 09Г2С"]

      ]

    }

  ]

}

---

#### 4. Извлечение параметров и сопоставление (UC‑05, UC‑06)

##### GET /documents/{doc_id}/parameters

Автоматически извлечённые структурированные параметры документа.

Ответ 200:

json

{

  "document_id": "doc-8a3f2b",

  "document_type": "specification",

  "parameters": {

    "designation": "21900M2.362135.0903",

    "title": "Секция 0903",

    "materials": ["сталь 09Г2С", "алюминий АМг5"],

    "dimensions": ["1200x800x6", "L=2500"],

    "references": ["21900M2.362135.0901СБ", "21900M2.362135.0902СБ"],

    "specification_items": [

      {

        "position": "1",

        "name": "Кница",

        "quantity": "2",

        "dimensions": "10x200x300",

        "weight": "0.5",

        "material": "сталь 09Г2С",

        "note": ""

      }

    ]

  },

  "extraction_confidence": 0.89,

  "unconfirmed_fields": ["dimensions позиции 3"],

  "updated_at": "2026-04-27T10:05:00Z"

}

##### POST /validate/compare

Запуск сопоставления нормы и проектного документа.

Запрос (возможны варианты):

json

{

  "normative_query": "толщина обшивки ледового класса Arc4",

  "project_document_id": "doc-draw-001"

}

или с конкретными идентификаторами фрагментов:

json

{

  "normative_fragment_id": "frg-norm-42",

  "project_fragment_id": "frg-draw-5"

}

Ответ 200 (инициирован процесс):

json

{

  "comparison_id": "cmp-007",

  "status": "processing",

  "created_at": "2026-04-27T12:00:00Z"

}

##### GET /validate/compare/{comparison_id}

Результат сопоставления.

Ответ 200 (когда status == "completed"):

json

{

  "comparison_id": "cmp-007",

  "status": "completed",

  "normative_block": {

    "document_id": "doc-norm-001",

    "document_title": "Правила РС часть I",

    "page_number": 42,

    "requirement_text": "Толщина обшивки в районе ледового пояса для класса Arc4 ≥ 12 мм"

  },

  "project_block": {

    "document_id": "doc-draw-001",

    "document_title": "21900M2.362135.0903СБ",

    "page_number": 1,

    "parameter_text": "Обшивка ледового пояса t=14 мм"

  },

  "match_status": "match",

  "details": "Требование выполнено: проектная толщина 14 мм превышает минимальные 12 мм.",

  "sources": [

    {"document_id": "doc-norm-001", "page": 42},

    {"document_id": "doc-draw-001", "page": 1}

  ],

  "disclaimer": "Результат носит информационный характер и подлежит обязательной инженерной проверке.",

  "processing_time_ms": 8700

}

Возможные статусы match_status: match (совпадает), possible_discrepancy (возможное расхождение), not_found_in_project (не найдено в проекте), not_found_in_norm (не найдено в норме), insufficient_data (недостаточно данных).

---

#### 5. Прочие вызовы

##### GET /health

Проверка состояния системы (публичный эндпоинт).

Ответ 200:

json

{

  "status": "ok",

  "version": "1.0.0",

  "uptime_seconds": 234567,

  "services": {

    "auth": "ok",

    "rag": "ok",

    "ocr": "degraded",

    "validation": "ok",

    "integration": "ok"

  }

}

---

**