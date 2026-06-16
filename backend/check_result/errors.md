# Supervisor Logs

**Generated:** 2026-06-16T11:20:42.731168+00:00


---

## 📋 Быстрая навигация


- [ℹ️ INFO — auth.err](#auth-err)
- [ℹ️ INFO — auth.log](#auth-log)
- [ℹ️ INFO — converter_validator.err](#converter_validator-err)
- [ℹ️ INFO — converter_validator.log](#converter_validator-log)
- [ℹ️ INFO — gateway.err](#gateway-err)
- [ℹ️ INFO — gateway.log](#gateway-log)
- [ℹ️ INFO — integration.err](#integration-err)
- [ℹ️ INFO — integration.log](#integration-log)
- [ℹ️ INFO — ocr.err](#ocr-err)
- [❌ ERROR — ocr.log](#ocr-log)
- [ℹ️ INFO — orchestrator.err](#orchestrator-err)
- [❌ ERROR — orchestrator.log](#orchestrator-log)
- [ℹ️ INFO — parser.err](#parser-err)
- [❌ ERROR — parser.log](#parser-log)
- [ℹ️ INFO — query.err](#query-err)
- [ℹ️ INFO — query.log](#query-log)
- [ℹ️ INFO — rag_builder.err](#rag_builder-err)
- [ℹ️ INFO — rag_builder.log](#rag_builder-log)
- [ℹ️ INFO — rag_search.err](#rag_search-err)
- [❌ ERROR — rag_search.log](#rag_search-log)
- [ℹ️ INFO — registry.err](#registry-err)
- [ℹ️ INFO — registry.log](#registry-log)


---

## ℹ️ Info-логи

_18 файл(ов) без ошибок (пропущены): auth.err, auth.log, converter_validator.err, converter_validator.log, gateway.err, gateway.log, integration.err, integration.log, ocr.err, orchestrator.err, parser.err, query.err, query.log, rag_builder.err, rag_builder.log, rag_search.err, registry.err, registry.log_


## ❌ Error-логи


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-16 14:20:18,651", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-16 14:20:19,652", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.91s."}
{"timestamp": "2026-06-16 14:20:20,568", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 2.23s."}
{"timestamp": "2026-06-16 14:20:26,701", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-16 14:20:27,702", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.16s."}
{"timestamp": "2026-06-16 14:20:35,208", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-16 14:20:36,209", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.91s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

FROM tasks 
WHERE tasks.draft_id = $1::INTEGER ORDER BY tasks.created_at DESC
2026-06-16 14:20:42 | 9dbfe958de1b4aa7 | sqlalchemy.engine.Engine     | INFO     | [cached since 0.01508s ago] (4,)
2026-06-16 14:20:42 | 9dbfe958de1b4aa7 | sqlalchemy.engine.Engine     | INFO     | SELECT task_steps.id, task_steps.task_id, task_steps.step_name, task_steps.step_index, task_steps.service_name, task_steps.status, task_steps.input_data, task_steps.output_data, task_steps.error_code, task_steps.error_message, task_steps.created_at, task_steps.started_at, task_steps.completed_at 
FROM task_steps 
WHERE task_steps.task_id = $1::INTEGER ORDER BY task_steps.step_index
2026-06-16 14:20:42 | 9dbfe958de1b4aa7 | sqlalchemy.engine.Engine     | INFO     | [cached since 18.99s ago] (3,)
2026-06-16 14:20:42 | -                | uvicorn.access               | INFO     | 172.19.0.1:55990 - "GET /api/v1/drafts/4/preview/status?longpoll=0 HTTP/1.1" 200
2026-06-16 14:20:42 | 9dbfe958de1b4aa7 | sqlalchemy.engine.Engine     | INFO     | COMMIT
2026-06-16 14:20:42 | 4e96b38afab14bfa | sqlalchemy.engine.Engine     | INFO     | BEGIN (implicit)
2026-06-16 14:20:42 | 4e96b38afab14bfa | sqlalchemy.engine.Engine     | INFO     | SELECT tasks.id, tasks.draft_id, tasks.document_id, tasks.pipeline_type, tasks.status, tasks.pipeline_stage, tasks.progress_percent, tasks.priority, tasks.current_step_name, tasks.current_step_index, tasks.total_steps, tasks.trace_id, tasks.full_completed, tasks.error_code, tasks.error_message, tasks.retry_count, tasks.locked_by, tasks.locked_at, tasks.created_at, tasks.updated_at, tasks.started_at, tasks.completed_at 
FROM tasks 
WHERE tasks.draft_id = $1::INTEGER ORDER BY tasks.created_at DESC
2026-06-16 14:20:42 | 4e96b38afab14bfa | sqlalchemy.engine.Engine     | INFO     | [cached since 0.02144s ago] (4,)
2026-06-16 14:20:42 | 4e96b38afab14bfa | sqlalchemy.engine.Engine     | INFO     | SELECT tasks.id, tasks.draft_id, tasks.document_id, tasks.pipeline_type, tasks.status, tasks.pipeline_stage, tasks.progress_percent, tasks.priority, tasks.current_step_name, tasks.current_step_index, tasks.total_steps, tasks.trace_id, tasks.full_completed, tasks.error_code, tasks.error_message, tasks.retry_count, tasks.locked_by, tasks.locked_at, tasks.created_at, tasks.updated_at, tasks.started_at, tasks.completed_at 
FROM tasks 
WHERE tasks.id = $1::INTEGER
2026-06-16 14:20:42 | 4e96b38afab14bfa | sqlalchemy.engine.Engine     | INFO     | [cached since 19.62s ago] (3,)
2026-06-16 14:20:42 | e98b95ea66a84131 | orchestrator.pipeline        | INFO     | Approving draft
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | SELECT tasks.id, tasks.draft_id, tasks.document_id, tasks.pipeline_type, tasks.status, tasks.pipeline_stage, tasks.progress_percent, tasks.priority, tasks.current_step_name, tasks.current_step_index, tasks.total_steps, tasks.trace_id, tasks.full_completed, tasks.error_code, tasks.error_message, tasks.retry_count, tasks.locked_by, tasks.locked_at, tasks.created_at, tasks.updated_at, tasks.started_at, tasks.completed_at 
FROM tasks 
WHERE tasks.id = $1::INTEGER FOR UPDATE
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [cached since 19.61s ago] (3,)
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | UPDATE tasks SET pipeline_stage=$1::VARCHAR, progress_percent=$2::INTEGER, updated_at=now() WHERE tasks.id = $3::INTEGER
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [generated in 0.00018s] ('full', 50, 3)
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | SELECT task_steps.id, task_steps.task_id, task_steps.step_name, task_steps.step_index, task_steps.service_name, task_steps.status, task_steps.input_data, task_steps.output_data, task_steps.error_code, task_steps.error_message, task_steps.created_at, task_steps.started_at, task_steps.completed_at 
FROM task_steps 
WHERE task_steps.task_id = $1::INTEGER ORDER BY task_steps.step_index
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [cached since 19s ago] (3,)
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | INSERT INTO task_steps (task_id, step_name, step_index, service_name, status, input_data, error_code, error_message, started_at, completed_at) VALUES ($1::INTEGER, $2::VARCHAR, $3::INTEGER, $4::VARCHAR, $5::VARCHAR, $6::JSON, $7::VARCHAR, $8::VARCHAR, $9::TIMESTAMP WITH TIME ZONE, $10::TIMESTAMP WITH TIME ZONE) RETURNING task_steps.id, task_steps.created_at
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [cached since 19.61s ago] (3, 'full_ocr', 3, 'OCR Service', 'pending', '{"file_key": "f-6c149ba59fef", "mode": "full"}', None, None, None, None)
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | INSERT INTO task_steps (task_id, step_name, step_index, service_name, status, input_data, error_code, error_message, started_at, completed_at) VALUES ($1::INTEGER, $2::VARCHAR, $3::INTEGER, $4::VARCHAR, $5::VARCHAR, $6::JSON, $7::VARCHAR, $8::VARCHAR, $9::TIMESTAMP WITH TIME ZONE, $10::TIMESTAMP WITH TIME ZONE) RETURNING task_steps.id, task_steps.created_at
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [cached since 19.61s ago] (3, 'full_converter', 4, 'Converter-validator', 'pending', '{"file_key": "f-6c149ba59fef", "mode": "full"}', None, None, None, None)
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | INSERT INTO task_steps (task_id, step_name, step_index, service_name, status, input_data, error_code, error_message, started_at, completed_at) VALUES ($1::INTEGER, $2::VARCHAR, $3::INTEGER, $4::VARCHAR, $5::VARCHAR, $6::JSON, $7::VARCHAR, $8::VARCHAR, $9::TIMESTAMP WITH TIME ZONE, $10::TIMESTAMP WITH TIME ZONE) RETURNING task_steps.id, task_steps.created_at
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [cached since 19.62s ago] (3, 'registry_creation', 5, 'Registry', 'pending', '{"draft_id": 4}', None, None, None, None)
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | SELECT task_steps.id, task_steps.task_id, task_steps.step_name, task_steps.step_index, task_steps.service_name, task_steps.status, task_steps.input_data, task_steps.output_data, task_steps.error_code, task_steps.error_message, task_steps.created_at, task_steps.started_at, task_steps.completed_at 
FROM task_steps 
WHERE task_steps.task_id = $1::INTEGER ORDER BY task_steps.step_index
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [cached since 19s ago] (3,)
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | SELECT task_steps.id, task_steps.task_id, task_steps.step_name, task_steps.step_index, task_steps.service_name, task_steps.status, task_steps.input_data, task_steps.output_data, task_steps.error_code, task_steps.error_message, task_steps.created_at, task_steps.started_at, task_steps.completed_at 
FROM task_steps 
WHERE task_steps.id = $1::INTEGER FOR UPDATE
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [cached since 19.61s ago] (13,)
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | UPDATE task_steps SET status=$1::VARCHAR, started_at=$2::TIMESTAMP WITH TIME ZONE WHERE task_steps.id = $3::INTEGER
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | [cached since 19.61s ago] ('running', datetime.datetime(2026, 6, 16, 11, 20, 42, 58945, tzinfo=datetime.timezone.utc), 13)
2026-06-16 14:20:42 | e98b95ea66a84131 | orchestrator.pipeline        | INFO     | Enqueued full OCR step
2026-06-16 14:20:42 | -                | uvicorn.access               | INFO     | 172.19.0.1:55990 - "PATCH /api/v1/drafts/4/decide HTTP/1.1" 200
2026-06-16 14:20:42 | e98b95ea66a84131 | sqlalchemy.engine.Engine     | INFO     | COMMIT
2026-06-16 14:20:42 | 6fd1aba4bed04d54 | services.base_client         | DEBUG    | Mock call: GET /registry/drafts/4 -> 0.000s
2026-06-16 14:20:42 | -                | uvicorn.access               | INFO     | 172.19.0.1:55990 - "GET /api/v1/drafts/4 HTTP/1.1" 200

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

{"timestamp": "2026-06-16 14:20:37,490", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Process request received: task_id=20002, file_key=multi-doc-2-1781608833.pdf"}
{"timestamp": "2026-06-16 14:20:37,492", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Starting full pipeline for task 20002, file multi-doc-2-1781608833.pdf"}
{"timestamp": "2026-06-16 14:20:37,550", "severity": "INFO", "name": "app.api.v1.endpoints.status", "message": "Returning status for task 20002: TaskStatus.ACCEPTED"}
{"timestamp": "2026-06-16 14:20:37,552", "severity": "INFO", "name": "app.core.minio_client", "message": "Downloaded multi-doc-2-1781608833.pdf, size=123616 bytes"}
{"timestamp": "2026-06-16 14:20:37,562", "severity": "INFO", "name": "app.core.validator", "message": "Security check passed"}
{"timestamp": "2026-06-16 14:20:37,562", "severity": "INFO", "name": "app.core.validator", "message": "Validation passed, MIME=application/pdf"}
{"timestamp": "2026-06-16 14:20:37,564", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Parsing PDF for task 20002, options={}"}
{"timestamp": "2026-06-16 14:20:37,573", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 2.25s."}
Jun 16, 2026 2:20:37 PM org.opendataloader.pdf.processors.DocumentProcessor preprocessing
INFO: File name: /tmp/tmp9z3e1jn_.pdf
Jun 16, 2026 2:20:37 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11901 in stream 39 0 obj)
Jun 16, 2026 2:20:37 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16578 in stream 47 0 obj)
Jun 16, 2026 2:20:37 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16513 in stream 55 0 obj)
Jun 16, 2026 2:20:38 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 16, 2026 2:20:38 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 16, 2026 2:20:38 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 16, 2026 2:20:38 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 16, 2026 2:20:38 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 16, 2026 2:20:38 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 16, 2026 2:20:38 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 16, 2026 2:20:38 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
Jun 16, 2026 2:20:39 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmp97wuayqw/tmp9z3e1jn_.json
Jun 16, 2026 2:20:39 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmp97wuayqw/tmp9z3e1jn_.md
Jun 16, 2026 2:20:39 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmp97wuayqw/tmp9z3e1jn_.html
{"timestamp": "2026-06-16 14:20:39,567", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-16 14:20:39,568", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-16 14:20:39,705", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_0_617ab711356b06f8.png, size=7705 bytes"}
{"timestamp": "2026-06-16 14:20:39,792", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_1_f8052b5c9759d1e1.png, size=5144 bytes"}
{"timestamp": "2026-06-16 14:20:39,879", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_2_1d9c0ba54ed582b4.png, size=4605 bytes"}
{"timestamp": "2026-06-16 14:20:39,964", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_3_7cba379c2bca3a95.png, size=3890 bytes"}
{"timestamp": "2026-06-16 14:20:40,050", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_4_3f9976aee3a3dac5.png, size=11303 bytes"}
{"timestamp": "2026-06-16 14:20:40,135", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_5_28bd92663bf750a8.png, size=9275 bytes"}
{"timestamp": "2026-06-16 14:20:40,139", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-16 14:20:40,139", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-16 14:20:40,140", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-16 14:20:42,147", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 1.00s."}

```


### rag_search-log

**❌ ERROR** — `/var/log/supervisor/rag_search.log`


```

)
    ^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.UndefinedFunctionError: operator does not exist: bigint = uuid
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
2026-06-16 14:20:41 | INFO     | app.core.middleware | <-- POST /api/v1/rag/search | 500 | 0.014s
2026-06-16 14:20:41 | INFO     | app.core.middleware | --> POST /api/v1/rag/search
2026-06-16 14:20:41 | INFO     | rag-search.search.api | Search request: query='тестовый документ multi-doc', top_k=10, search_type=hybrid, rerank=True
2026-06-16 14:20:41 | INFO     | rag-search.search.hybrid | Executing hybrid search for query='тестовый документ multi-doc'
2026-06-16 14:20:41 | INFO     | rag-search.search.hybrid | Search completed: 4 results (total_found=4), search_type=hybrid
2026-06-16 14:20:41 | ERROR    | rag-search.search.api | Search failed: operator does not exist: bigint = uuid
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
Traceback (most recent call last):
  File "/app/backend/rag_search_service/app/api/v1/search.py", line 117, in search_chunks
    rows = await conn.fetch(base_query, *params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/asyncpg/connection.py", line 694, in fetch
    return await self._execute(
           ^^^^^^^^^^^^^^^^^^^^
    ...<5 lines>...
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/asyncpg/connection.py", line 1873, in _execute
    result, _ = await self.__execute(
                ^^^^^^^^^^^^^^^^^^^^^
    ...<7 lines>...
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/asyncpg/connection.py", line 1970, in __execute
    result, stmt = await self._do_execute(
                   ^^^^^^^^^^^^^^^^^^^^^^^
    ...<5 lines>...
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/asyncpg/connection.py", line 2013, in _do_execute
    stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/asyncpg/connection.py", line 443, in _get_statement
    statement = await self._protocol.prepare(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<5 lines>...
    )
    ^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.UndefinedFunctionError: operator does not exist: bigint = uuid
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
2026-06-16 14:20:41 | INFO     | app.core.middleware | <-- POST /api/v1/rag/search | 500 | 0.010s

```
