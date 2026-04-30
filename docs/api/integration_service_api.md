**

#### Integration Service (integration-service:8084)

##### POST /files/upload

Загрузка файла в общее хранилище.

Запрос: multipart/form-data с file и опциональным related_document_id.  
Ответ 201:

json

{

  "file_id": "file-xyz",

  "filename": "page_5.png",

  "size": 1048576,

  "mime_type": "image/png",

  "url": "/files/file-xyz",

  "uploaded_at": "2026-04-27T10:01:00Z"

}

##### GET /files/{file_id}

Бинарный поток файла с корректными заголовками.

##### DELETE /files/{file_id}

Удаление файла.  
Ответ: {"file_id": "...", "deleted_at": "..."}

##### GET /files/{file_id}/info

Метаданные файла без скачивания (все поля, как в ответе загрузки).

##### POST /meridian/export

Отправка структурированных данных в систему «Меридиан».

Запрос:

json

{

  "document_id": "doc-8a3f2b",

  "data": { ... }

}

Ответ:

json

{

  "export_id": "exp-001",

  "external_id": "mer-12345",

  "status": "sent",

  "sent_at": "2026-04-27T12:00:00Z",

  "response_message": "Принято"

}


Ответ – status_code, headers, body, latency_ms.

##### GET /external/status

Проверка доступности внешних систем.  
Ответ:

json

{

  "systems": [

    {

      "api_name": "meridian",

      "status": "available",

      "last_checked": "2026-04-27T12:05:00Z",

      "latency_ms": 230

    }

  ]

}

---

**