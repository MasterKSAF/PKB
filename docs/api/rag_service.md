**

#### 2.2 RAG Service (rag-service:8081)

##### POST /index

Добавление чанков документа в векторный индекс.

Запрос:

json

{

  "document_id": "doc-8a3f2b",

  "chunks": [

    {

      "chunk_id": "chk-001",

      "text": "Для ледового класса Arc4...",

      "page_number": 42,

      "coordinates": {"x": 120, "y": 350, "width": 400, "height": 60},

      "metadata": {"document_type": "normative", "title": "Правила РС"}

    }

  ]

}

Ответ 201:

json

{

  "document_id": "doc-8a3f2b",

  "indexed_count": 128,

  "status": "completed"

}

##### DELETE /index/{document_id}

Удаление всех чанков документа из индекса.  
Ответ:

json

{

  "document_id": "doc-8a3f2b",

  "deleted_count": 128,

  "status": "completed"

}

##### POST /search

Гибридный поиск (внутренний, не путать с публичным /search).

Запрос:

json

{

  "query": "ледовый класс Arc4",

  "top_k": 10,

  "filters": {"document_type": "normative"},

  "search_type": "hybrid"

}

search_type: hybrid, sparse, dense.  
Ответ 200:

json

{

  "results": [

    {

      "chunk_id": "chk-001",

      "document_id": "doc-norm-001",

      "page_number": 42,

      "text": "Для ледового класса Arc4 толщина обшивки...",

      "coordinates": {"x": 120, "y": 350, "width": 400, "height": 60},

      "score": 0.92,

      "metadata": {"document_type": "normative", "title": "Правила РС"}

    }

  ],

  "search_type_used": "hybrid",

  "processing_time_ms": 120

}

#####

##### POST /generate

Генерация ответа языковой моделью.

Запрос:

json

{

  "messages": [

    {"role": "system", "content": "Ты – ассистент инженера-судостроителя."},

    {"role": "user", "content": "Какая толщина обшивки для Arc4?"}

  ],

  "context_chunks": [

    {

      "chunk_id": "chk-001",

      "text": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм.",

      "document_id": "doc-norm-001",

      "page_number": 42

    }

  ],

  "model": "llama-3-70b",

  "temperature": 0.2,

}

Ответ 200 (stream: false):

json

{

  "content": "Согласно Правилам, толщина обшивки для Arc4 не менее 12 мм.",

  "model_used": "llama-3-70b",

  "usage": {

    "prompt_tokens": 150,

    "completion_tokens": 40

  },

  "finish_reason": "stop"

}

**