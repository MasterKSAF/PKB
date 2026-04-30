**

#### OCR & Layout Service (ocr-service:8083)

Обработка одного файла или пакетная.

##### POST /ocr/process

Пакетная обработка многостраничного PDF.  
Запрос: file (ссылка на файл в хранилище), options, pages (строка диапазона, например "1-5,8").  
Ответ 200:

json

{

  "document_id": "temp-doc-batch",

  "pages": [

    {

      "page_number": 1,

      "text": "...",

      "confidence": 0.95,

      "engine_used": "paddleocr",

      "page_type_detected": "text",

      "blocks": [...],

      "status": "success",

      "errors": []

    }

  ],

  "total_pages": 5,

  "successful_pages": 4,

  "low_confidence_pages": 1,

  "failed_pages": 0

}

##### GET /ocr/engines

Список доступных OCR‑движков.  
Ответ:

json

{

  "engines": [

    {

      "engine_id": "paddleocr",

      "name": "PaddleOCR",

      "status": "available",

      "supported_languages": ["ru","en"],

      "average_processing_time_ms": 1500,

      "default_for_types": ["normative","specification"]

    },

    {

      "engine_id": "tesseract",

      "name": "Tesseract 5",

      "status": "available",

      "supported_languages": ["ru","en"],

      "average_processing_time_ms": 2500,

      "default_for_types": ["archival_scan"]

    }

  ]

}


**