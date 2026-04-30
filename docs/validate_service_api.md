**

#### Validation & Extraction Service (validation-service:8082)

##### POST /extract/parameters

Извлечение структурированных параметров из документа (по ID и опционально странице).

Запрос:

json

{

  "document_id": "doc-8a3f2b",

  "page_id": null,

  "document_type": "specification"

}

Ответ 200 – структура параметров, аналогичная GET /documents/{doc_id}/parameters, плюс processing_time_ms.

##### POST /check

Выполнение заданного набора проверок над текстом.

Запрос:

json

{

  "text": "Обшивка ледового пояса 10 мм",

  "rules": ["min_thickness_12mm"],

  "document_type": "drawing"

}

Ответ:

json

{

  "passed": false,

  "checks": [

    {

      "rule": "min_thickness_12mm",

      "status": "fail",

      "message": "Толщина 10 мм меньше требования 12 мм",

      "details": "..."

    }

  ],

  "processing_time_ms": 50

}

##### POST /calculate

Арифметический движок для вычислений в контексте документа.

Запрос:

json

{

  "expression": "(1200 + 2*10) / 2",

  "context": {"переменная": ...}

}

Ответ:

json

{

  "expression": "(1200 + 2*10) / 2",

  "result": 610,

  "unit": "мм",

  "steps": ["1200 + 20 = 1220", "1220 / 2 = 610"]

}

##### POST /recommend

Рекомендации по исправлению ошибок проверки.

Запрос:

json

{

  "failures": [

    {"rule": "min_thickness_12mm", "status": "fail"}

  ],

  "document_type": "drawing"

}

Ответ:

json

{

  "recommendations": [

    {

      "failure_ref": "min_thickness_12mm",

      "recommendation_text": "Увеличить толщину обшивки до 12 мм согласно Правилам РС, часть I, стр.42.",

      "severity": "critical",

      "reference_document": "doc-norm-001"

    }

  ]

}

##### POST /compare

Сопоставление нормы и проектных данных (одиночное).

Запрос:

json

{

  "normative_text": "Толщина обшивки ледового пояса ≥ 12 мм",

  "project_text": "Обшивка ледового пояса 14 мм",

  "document_type": "drawing"

}

Ответ – объект comparison, как в публичном API, плюс comparison_id.

##### GET /compare/{comparison_id}

Получение ранее созданного сопоставления.

##### POST /compare/batch

Массовое сопоставление пар фрагментов.

Запрос:

json

{

  "pairs": [

    {"normative_chunk_id": "frg-42", "project_chunk_id": "frg-5"}

  ]

}

Ответ:

json

{

  "batch_id": "batch-001",

  "comparisons": [

    {

      "comparison_id": "cmp-007",

      "match_status": "match",

      "summary": "Толщина 14 мм соответствует требованию ≥12 мм"

    }

  ],

  "total_pairs": 1,

  "matched": 1,

  "discrepancies_found": 0,

  "insufficient_data": 0

}

**