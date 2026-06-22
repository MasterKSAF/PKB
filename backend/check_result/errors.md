# Supervisor Logs

**Generated:** 2026-06-22T14:59:18.017672+00:00


---

## 📋 Быстрая навигация


- [ℹ️ INFO — auth.err](#auth-err)
- [❌ ERROR — auth.log](#auth-log)
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
- [❌ ERROR — query.err](#query-err)
- [❌ ERROR — query.log](#query-log)
- [ℹ️ INFO — rag_builder.err](#rag_builder-err)
- [ℹ️ INFO — rag_builder.log](#rag_builder-log)
- [ℹ️ INFO — rag_builder_spk.err](#rag_builder_spk-err)
- [ℹ️ INFO — rag_builder_spk.log](#rag_builder_spk-log)
- [ℹ️ INFO — rag_search.err](#rag_search-err)
- [❌ ERROR — rag_search.log](#rag_search-log)
- [ℹ️ INFO — registry.err](#registry-err)
- [ℹ️ INFO — registry.log](#registry-log)


---

## ℹ️ Info-логи

_17 файл(ов) без ошибок (пропущены): auth.err, converter_validator.err, converter_validator.log, gateway.err, gateway.log, integration.err, integration.log, ocr.err, orchestrator.err, parser.err, rag_builder.err, rag_builder.log, rag_builder_spk.err, rag_builder_spk.log, rag_search.err, registry.err, registry.log_


## ❌ Error-логи


### auth-log

**❌ ERROR** — `/var/log/supervisor/auth.log`


```

{"timestamp": "2026-06-22 17:59:10,557", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-22 17:59:10,817", "severity": "INFO", "name": "app.services.user_service", "message": "User created: prepare-user-140349@test.com"}
{"timestamp": "2026-06-22 17:59:10,837", "severity": "WARNING", "name": "app.services.user_service", "message": "Attempt to create duplicate role: knowledge_admin"}
{"timestamp": "2026-06-22 17:59:11,067", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-22 17:59:11,113", "severity": "INFO", "name": "app.services.auth_service", "message": "Refresh token revoked for user: u-7c458512108f"}
{"timestamp": "2026-06-22 17:59:11,143", "severity": "WARNING", "name": "app.services.user_service", "message": "Attempt to create duplicate user: test@test.com"}
{"timestamp": "2026-06-22 17:59:11,179", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-0fbad5caeb51"}
{"timestamp": "2026-06-22 17:59:11,208", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-0fbad5caeb51"}
{"timestamp": "2026-06-22 17:59:11,238", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-0fbad5caeb51"}
{"timestamp": "2026-06-22 17:59:11,266", "severity": "WARNING", "name": "app.services.user_service", "message": "Attempt to create duplicate role: viewer"}
{"timestamp": "2026-06-22 17:59:12,264", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-22 17:59:12,502", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-22 17:59:12,959", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-22 17:59:12,960", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.83s."}
{"timestamp": "2026-06-22 17:59:13,505", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-22 17:59:13,506", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.04s."}
{"timestamp": "2026-06-22 17:59:14,076", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-22 17:59:14,745", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-22 17:59:15,747", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.17s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self._prepare_and_execute(operation, parameters)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.UniqueViolationError'>: duplicate key value violates unique constraint "uq_tasks_draft_pipeline"
DETAIL:  Key (draft_id, pipeline_type)=(0, reprocess) already exists.
[SQL: INSERT INTO tasks (draft_id, document_id, version_id, pipeline_type, status, pipeline_stage, progress_percent, priority, current_step_name, current_step_index, total_steps, trace_id, created_by, full_completed, error_code, error_message, retry_count, locked_by, locked_at, deleted_at, started_at, completed_at) VALUES ($1::INTEGER, $2::INTEGER, $3::INTEGER, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR, $7::INTEGER, $8::INTEGER, $9::VARCHAR, $10::INTEGER, $11::INTEGER, $12::VARCHAR, $13::VARCHAR, $14::BOOLEAN, $15::VARCHAR, $16::VARCHAR, $17::INTEGER, $18::VARCHAR, $19::TIMESTAMP WITH TIME ZONE, $20::TIMESTAMP WITH TIME ZONE, $21::TIMESTAMP WITH TIME ZONE, $22::TIMESTAMP WITH TIME ZONE) RETURNING tasks.id, tasks.created_at, tasks.updated_at]
[parameters: (0, None, None, 'reprocess', 'active', 'upload', 0, 5, None, 0, 1, None, None, False, None, None, 0, None, None, None, None, None)]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
2026-06-22 17:59:12 | -                | uvicorn.access               | INFO     | 172.19.0.1:47250 - "GET /api/v1/documents/1/errors HTTP/1.1" 200
2026-06-22 17:59:12 | -                | uvicorn.access               | INFO     | 172.19.0.1:47250 - "GET /api/v1/documents/1/parameters HTTP/1.1" 200
2026-06-22 17:59:12 | -                | uvicorn.access               | INFO     | 172.19.0.1:47250 - "GET /api/v1/documents/1/pages HTTP/1.1" 200
2026-06-22 17:59:12 | -                | uvicorn.access               | INFO     | 172.19.0.1:47250 - "GET /api/v1/documents/1/pages/1?highlight= HTTP/1.1" 200
2026-06-22 17:59:12 | -                | uvicorn.access               | INFO     | 172.19.0.1:47250 - "GET /api/v1/documents/1/pages/1/text HTTP/1.1" 200
2026-06-22 17:59:12 | -                | uvicorn.access               | INFO     | 172.19.0.1:47250 - "GET /api/v1/documents/1/pages/1/preview?format=&highlight= HTTP/1.1" 200
2026-06-22 17:59:12 | 5bd30b8e236d4087 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-22 17:59:12 | 5bd30b8e236d4087 | services.base_client         | ERROR    | HTTP error: POST /registry/documents/check-uniqueness -> 307 (0.003s, retries exhausted)
2026-06-22 17:59:12 | 5bd30b8e236d4087 | app.api.v1.endpoints.drafts  | WARNING  | Uniqueness check failed: Redirect response '307 Temporary Redirect' for url 'http://127.0.0.1:8084/api/v1/registry/documents/check-uniqueness'
Redirect location: 'http://127.0.0.1:8084/api/v1/registry/documents/check-uniqueness/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/307
2026-06-22 17:59:12 | 5bd30b8e236d4087 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-22 17:59:12 | 5bd30b8e236d4087 | services.base_client         | ERROR    | HTTP error: POST /registry/drafts -> 404 (0.003s, retries exhausted)
2026-06-22 17:59:12 | -                | uvicorn.access               | INFO     | 172.19.0.1:47250 - "POST /api/v1/drafts/ HTTP/1.1" 500
2026-06-22 17:59:12 | 996040ceb7ef406c | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-22 17:59:12 | 996040ceb7ef406c | services.base_client         | ERROR    | HTTP error: GET /registry/drafts -> 404 (0.005s, retries exhausted)
2026-06-22 17:59:12 | 996040ceb7ef406c | app.api.v1.endpoints.drafts  | ERROR    | Failed to list drafts: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts?page=1&page_size=50'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-22 17:59:12 | -                | uvicorn.access               | INFO     | 172.19.0.1:47250 - "GET /api/v1/drafts/ HTTP/1.1" 200
2026-06-22 17:59:16 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 0.82s.
2026-06-22 17:59:17 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 2.14s.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

{"timestamp": "2026-06-22 17:59:11,913", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Starting full pipeline for task 12345, file test-file-key.pdf"}
{"timestamp": "2026-06-22 17:59:11,954", "severity": "INFO", "name": "app.core.minio_client", "message": "Downloaded test-file-key.pdf, size=123616 bytes"}
{"timestamp": "2026-06-22 17:59:11,958", "severity": "INFO", "name": "app.core.validator", "message": "Security check passed"}
{"timestamp": "2026-06-22 17:59:11,958", "severity": "INFO", "name": "app.core.validator", "message": "Validation passed, MIME=application/pdf"}
{"timestamp": "2026-06-22 17:59:11,960", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Parsing PDF for task 12345, options={}"}
{"timestamp": "2026-06-22 17:59:11,963", "severity": "INFO", "name": "app.api.v1.endpoints.status", "message": "Returning status for task 12345: TaskStatus.ACCEPTED"}
Jun 22, 2026 5:59:12 PM org.opendataloader.pdf.processors.DocumentProcessor preprocessing
INFO: File name: /tmp/tmp3zo8xf7j.pdf
Jun 22, 2026 5:59:12 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11901 in stream 39 0 obj)
Jun 22, 2026 5:59:12 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16578 in stream 47 0 obj)
Jun 22, 2026 5:59:12 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16513 in stream 55 0 obj)
Jun 22, 2026 5:59:12 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 22, 2026 5:59:12 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 22, 2026 5:59:12 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 22, 2026 5:59:12 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 22, 2026 5:59:12 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 22, 2026 5:59:12 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 22, 2026 5:59:12 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 22, 2026 5:59:12 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
{"timestamp": "2026-06-22 17:59:14,045", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
Jun 22, 2026 5:59:14 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmp6mmvex3c/tmp3zo8xf7j.json
Jun 22, 2026 5:59:14 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmp6mmvex3c/tmp3zo8xf7j.md
Jun 22, 2026 5:59:14 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmp6mmvex3c/tmp3zo8xf7j.html
{"timestamp": "2026-06-22 17:59:14,379", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 12345"}
{"timestamp": "2026-06-22 17:59:14,380", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-22 17:59:14,487", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-22 17:59:14,597", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-22 17:59:14,708", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-22 17:59:14,821", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-22 17:59:14,915", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-22 17:59:15,006", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-22 17:59:15,011", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 12345"}
{"timestamp": "2026-06-22 17:59:15,011", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 12345"}
{"timestamp": "2026-06-22 17:59:15,011", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Full pipeline completed for task 12345"}
{"timestamp": "2026-06-22 17:59:15,046", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.09s."}

```


### query-err

**❌ ERROR** — `/var/log/supervisor/query.err`


```

~~~~~~~~~~~~~~~~~~~~~~~~~^
        dialect, context, statement, parameters
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        e, str_statement, effective_parameters, cursor, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self._prepare_and_execute(operation, parameters)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.ForeignKeyViolationError'>: insert or update on table "chat_sessions" violates foreign key constraint "chat_sessions_project_id_fkey"
DETAIL:  Key (project_id)=(7) is not present in table "chat_projects".
[SQL: INSERT INTO chat_sessions (user_id, project_id, title, document_ids, options, deleted_at, created_at, updated_at) VALUES ($1::VARCHAR, $2::INTEGER, $3::VARCHAR, $4::JSON, $5::JSON, $6::TIMESTAMP WITH TIME ZONE, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE) RETURNING chat_sessions.session_id]
[parameters: ('u-001', 7, 'Тестовая сессия API', '[]', '{}', None, datetime.datetime(2026, 6, 22, 14, 59, 13, 161941, tzinfo=datetime.timezone.utc), datetime.datetime(2026, 6, 22, 14, 59, 13, 161947, tzinfo=datetime.timezone.utc))]
(Background on this error at: https://sqlalche.me/e/20/gkpj)

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-22 17:59:11,700", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-22 17:59:12,699", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-22 17:59:12,699", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.89s."}
{"timestamp": "2026-06-22 17:59:12,899", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"e1340b0b-d214-4e57-af40-796f37468aae\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/projects\", \"status\": 200, \"duration_ms\": 3}"}
{"timestamp": "2026-06-22 17:59:12,904", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"f71b1838-3242-4251-b0c1-0fdabecaeff8\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/health\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-22 17:59:12,964", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"f30a1283-664b-4a7d-b827-7c5f340e3cb5\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 55}"}
{"timestamp": "2026-06-22 17:59:12,981", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"c060287c-7c1c-4a4d-9241-d6421f3b8cf0\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/8/messages\", \"status\": 202, \"duration_ms\": 14}"}
{"timestamp": "2026-06-22 17:59:12,982", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline started", "message_id": 14, "session_id": 8}
{"timestamp": "2026-06-22 17:59:12,987", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"59faf80d-2af3-43c0-94c9-7e922bb63387\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/health\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-22 17:59:12,992", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"e531743e-335a-4746-965f-5b8e9a3acc28\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/system/health\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-22 17:59:13,083", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"67684db6-a1a0-4e05-bc1d-5c708487ed7b\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/projects\", \"status\": 200, \"duration_ms\": 3}"}
{"timestamp": "2026-06-22 17:59:13,088", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"1a25a5b7-ae31-42cb-90f6-a5b82bb834b8\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/projects/7\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-22 17:59:13,101", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"b464ddf7-c672-4d32-8037-46588e68fa5c\", \"user_id\": null, \"draft_id\": null, \"method\": \"PUT\", \"path\": \"/api/v1/chat/projects/7\", \"status\": 200, \"duration_ms\": 8}"}
{"timestamp": "2026-06-22 17:59:13,154", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"f589cd80-d5f4-4d5e-a1cc-b2f52085733f\", \"user_id\": null, \"draft_id\": null, \"method\": \"DELETE\", \"path\": \"/api/v1/chat/projects/7\", \"status\": 204, \"duration_ms\": 47}"}
{"timestamp": "2026-06-22 17:59:13,202", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"843db728-289c-4093-b94f-47fe475ba3ec\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions\", \"status\": 200, \"duration_ms\": 5}"}
{"timestamp": "2026-06-22 17:59:13,213", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"a4b570d8-aaff-4918-a892-eea660e1e4d1\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/8\", \"status\": 200, \"duration_ms\": 5}"}
{"timestamp": "2026-06-22 17:59:13,266", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"33067275-bc2a-41a4-baa3-b14d61ddeaa6\", \"user_id\": null, \"draft_id\": null, \"method\": \"PUT\", \"path\": \"/api/v1/chat/sessions/8\", \"status\": 200, \"duration_ms\": 6}"}
{"timestamp": "2026-06-22 17:59:13,282", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"e9c96008-b42b-4cad-953b-b5f117d080af\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/8/messages\", \"status\": 202, \"duration_ms\": 12}"}
{"timestamp": "2026-06-22 17:59:13,283", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline started", "message_id": 16, "session_id": 8}
{"timestamp": "2026-06-22 17:59:13,292", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"914b3c77-786c-47df-b17b-3b5f20844f77\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/8/messages/last\", \"status\": 200, \"duration_ms\": 6}"}
{"timestamp": "2026-06-22 17:59:13,302", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"a4843c6a-2210-4c47-ad02-912499536d79\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/8/messages\", \"status\": 200, \"duration_ms\": 6}"}
{"timestamp": "2026-06-22 17:59:13,315", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"261a7bfc-7124-4a95-8654-85065c4232e3\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/8/messages/16\", \"status\": 200, \"duration_ms\": 7}"}
{"timestamp": "2026-06-22 17:59:13,320", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline finished", "message_id": 14, "chunks": 2}
{"timestamp": "2026-06-22 17:59:13,323", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"421913db-474c-455d-8b61-b0c69aa3e8f0\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/8/messages/search\", \"status\": 200, \"duration_ms\": 5}"}
{"timestamp": "2026-06-22 17:59:13,357", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"2d799994-76b0-4682-93b9-f34c4f5fc549\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/8/context\", \"status\": 200, \"duration_ms\": 3}"}
{"timestamp": "2026-06-22 17:59:13,369", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"0495d2c1-623c-4f3c-a246-5ac8d42a9286\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/8/export\", \"status\": 200, \"duration_ms\": 7}"}
{"timestamp": "2026-06-22 17:59:13,382", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"8effc24a-56db-483f-8d24-7c31e7744204\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/feedback\", \"status\": 200, \"duration_ms\": 7}"}
{"timestamp": "2026-06-22 17:59:13,398", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"d0db1c69-d981-4830-9f05-e465eda126bb\", \"user_id\": null, \"draft_id\": null, \"method\": \"DELETE\", \"path\": \"/api/v1/chat/sessions/8\", \"status\": 200, \"duration_ms\": 13}"}
{"timestamp": "2026-06-22 17:59:13,410", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"f4f0f820-2d30-4a41-99fe-22813305678c\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history\", \"status\": 200, \"duration_ms\": 8}"}
{"timestamp": "2026-06-22 17:59:13,414", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"8a13d6b6-7333-4814-a5dc-288563ad6d86\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history/export\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-22 17:59:13,456", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"ec14bb17-258d-4c2e-ba87-8d0c2fdab4ae\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-22 17:59:13,461", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"aefbc2d5-5189-4fdf-b409-1ea3a6d18556\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/ask\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-22 17:59:13,659", "severity": "ERROR", "name": "app.services.pipeline", "message": "pipeline error", "exc_info": "Traceback (most recent call last):\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 550, in _prepare_and_execute\n    self._rows = deque(await prepared_stmt.fetch(*parameters))\n                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/asyncpg/prepared_stmt.py\", line 177, in fetch\n    data = await self.__bind_execute(args, 0, timeout)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/asyncpg/prepared_stmt.py\", line 268, in __bind_execute\n    data, status, _ = await self.__do_execute(\n                      ^^^^^^^^^^^^^^^^^^^^^^^^\n        lambda protocol: protocol.bind_execute(\n        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n            self._state, args, '', limit, True, timeout))\n            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/asyncpg/prepared_stmt.py\", line 257, in __do_execute\n    return await executor(protocol)\n           ^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"asyncpg/protocol/protocol.pyx\", line 205, in bind_execute\nasyncpg.exceptions.ForeignKeyViolationError: insert or update on table \"chat_sources\" violates foreign key constraint \"chat_sources_message_id_fkey\"\nDETAIL:  Key (message_id)=(16) is not present in table \"chat_messages\".\n\nThe above exception was the direct cause of the following exception:\n\nTraceback (most recent call last):\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py\", line 2127, in _exec_insertmany_context\n    dialect.do_execute(\n    ~~~~~~~~~~~~~~~~~~^\n        cursor,\n        ^^^^^^^\n    ...<2 lines>...\n        context,\n        ^^^^^^^^\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/default.py\", line 952, in do_execute\n    cursor.execute(statement, parameters)\n    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 585, in execute\n    self._adapt_connection.await_(\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^\n        self._prepare_and_execute(operation, parameters)\n        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py\", line 132, in await_only\n    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501\n           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py\", line 196, in greenlet_spawn\n    value = await result\n            ^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 563, in _prepare_and_execute\n    self._handle_exception(error)\n    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 513, in _handle_exception\n    self._adapt_connection._handle_exception(error)\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 797, in _handle_exception\n    raise translated_error from error\nsqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.IntegrityError: <class 'asyncpg.exceptions.ForeignKeyViolationError'>: insert or update on table \"chat_sources\" violates foreign key constraint \"chat_sources_message_id_fkey\"\nDETAIL:  Key (message_id)=(16) is not present in table \"chat_messages\".\n\nThe above exception was the direct cause of the following exception:\n\nTraceback (most recent call last):\n  File \"/app/backend/query_service/app/services/pipeline.py\", line 149, in run_pipeline\n    async with db.begin():\n               ~~~~~~~~^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/ext/asyncio/session.py\", line 1886, in __aexit__\n    await greenlet_spawn(\n        self._sync_transaction().__exit__, type_, value, traceback\n    )\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py\", line 203, in greenlet_spawn\n    result = context.switch(value)\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/util.py\", line 147, in __exit__\n    with util.safe_reraise():\n         ~~~~~~~~~~~~~~~~~^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/util/langhelpers.py\", line 122, in __exit__\n    raise exc_value.with_traceback(exc_tb)\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/util.py\", line 145, in __exit__\n    self.commit()\n    ~~~~~~~~~~~^^\n  File \"<string>\", line 2, in commit\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/state_changes.py\", line 137, in _go\n    ret_value = fn(self, *arg, **kw)\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/session.py\", line 1315, in commit\n    self._prepare_impl()\n    ~~~~~~~~~~~~~~~~~~^^\n  File \"<string>\", line 2, in _prepare_impl\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/state_changes.py\", line 137, in _go\n    ret_value = fn(self, *arg, **kw)\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/session.py\", line 1290, in _prepare_impl\n    self.session.flush()\n    ~~~~~~~~~~~~~~~~~~^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/session.py\", line 4352, in flush\n    self._flush(objects)\n    ~~~~~~~~~~~^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/session.py\", line 4487, in _flush\n    with util.safe_reraise():\n         ~~~~~~~~~~~~~~~~~^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/util/langhelpers.py\", line 122, in __exit__\n    raise exc_value.with_traceback(exc_tb)\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/session.py\", line 4448, in _flush\n    flush_context.execute()\n    ~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/unitofwork.py\", line 465, in execute\n    rec.execute(self)\n    ~~~~~~~~~~~^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/unitofwork.py\", line 641, in execute\n    util.preloaded.orm_persistence.save_obj(\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^\n        self.mapper,\n        ^^^^^^^^^^^^\n        uow.states_for_mapper_hierarchy(self.mapper, False, False),\n        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n        uow,\n        ^^^^\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/persistence.py\", line 94, in save_obj\n    _emit_insert_statements(\n    ~~~~~~~~~~~~~~~~~~~~~~~^\n        base_mapper,\n        ^^^^^^^^^^^^\n    ...<3 lines>...\n        insert,\n        ^^^^^^^\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/orm/persistence.py\", line 1144, in _emit_insert_statements\n    result = connection.execute(\n        statement, multiparams, execution_options=execution_options\n    )\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py\", line 1421, in execute\n    return meth(\n        self,\n        distilled_parameters,\n        execution_options or NO_OPTIONS,\n    )\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/sql/elements.py\", line 526, in _execute_on_connection\n    return connection._execute_clauseelement(\n           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^\n        self, distilled_params, execution_options\n        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py\", line 1643, in _execute_clauseelement\n    ret = self._execute_context(\n        dialect,\n    ...<8 lines>...\n        cache_hit=cache_hit,\n    )\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py\", line 1846, in _execute_context\n    return self._exec_insertmany_context(dialect, context)\n           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py\", line 2135, in _exec_insertmany_context\n    self._handle_dbapi_exception(\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^\n        e,\n        ^^\n    ...<4 lines>...\n        is_sub_exec=True,\n        ^^^^^^^^^^^^^^^^^\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py\", line 2365, in _handle_dbapi_exception\n    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py\", line 2127, in _exec_insertmany_context\n    dialect.do_execute(\n    ~~~~~~~~~~~~~~~~~~^\n        cursor,\n        ^^^^^^^\n    ...<2 lines>...\n        context,\n        ^^^^^^^^\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/default.py\", line 952, in do_execute\n    cursor.execute(statement, parameters)\n    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 585, in execute\n    self._adapt_connection.await_(\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^\n        self._prepare_and_execute(operation, parameters)\n        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py\", line 132, in await_only\n    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501\n           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/util/_concurrency_py3k.py\", line 196, in greenlet_spawn\n    value = await result\n            ^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 563, in _prepare_and_execute\n    self._handle_exception(error)\n    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 513, in _handle_exception\n    self._adapt_connection._handle_exception(error)\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py\", line 797, in _handle_exception\n    raise translated_error from error\nsqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.ForeignKeyViolationError'>: insert or update on table \"chat_sources\" violates foreign key constraint \"chat_sources_message_id_fkey\"\nDETAIL:  Key (message_id)=(16) is not present in table \"chat_messages\".\n[SQL: INSERT INTO chat_sources (message_id, chunk_id, fragment_id, document_id, document_title, section_id, page_number, clause, section_title, excerpt, text, score, confidence, path, content_hash, page_preview_url, document_url) SELECT p0::INTEGER, p1::BI ... 748 characters truncated ... p14, p15, p16, sen_counter) ORDER BY sen_counter RETURNING chat_sources.id, chat_sources.id AS id__1]\n[parameters: (16, 420001, None, 1, 'Правила классификации и постройки морских судов, Часть II', 420001, 42, '4.2 Требования к обшивке ледового пояса', 'Ледовые усиления корпуса', 'Для ледового класса Arc4 толщина обшивки ледового пояса должна быть не менее 12 мм.', 'Для ледового класса Arc4 толщина обшивки ледового пояса должна быть не менее 12 мм. Расчёт выполняется с учётом района эксплуатации, материала и ледовой нагрузки.', 0.94, 0.91, None, None, None, None, 16, 420017, None, 2, 'НСИ ПКБ, версия 2026', 420017, 17, '3.1 Нормативные требования НСИ', 'Нормативные параметры корпуса', 'Класс Arc4: нормативная толщина — не менее 12 мм при стали категории Е.', 'Класс Arc4: нормативная толщина листов обшивки — не менее 12 мм при стали категории Е. При других категориях стали расчёт выполняется индивидуально.', 0.87, 0.84, None, None, None, None)]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)", "message_id": 16}
{"timestamp": "2026-06-22 17:59:15,379", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-22 17:59:15,379", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.08s."}

```


### rag_search-log

**❌ ERROR** — `/var/log/supervisor/rag_search.log`


```

{"timestamp": "2026-06-22 17:59:14,202", "severity": "INFO", "name": "app.core.middleware", "message": "--> GET /api/v1/health"}
{"timestamp": "2026-06-22 17:59:14,203", "severity": "INFO", "name": "app.core.middleware", "message": "<-- GET /api/v1/health | 200 | 0.001s"}
{"timestamp": "2026-06-22 17:59:14,206", "severity": "INFO", "name": "app.core.middleware", "message": "--> GET /api/v1/health"}
{"timestamp": "2026-06-22 17:59:14,209", "severity": "INFO", "name": "app.core.middleware", "message": "<-- GET /api/v1/health | 200 | 0.002s"}
{"timestamp": "2026-06-22 17:59:14,213", "severity": "INFO", "name": "app.core.middleware", "message": "--> POST /api/v1/rag/search"}
{"timestamp": "2026-06-22 17:59:14,254", "severity": "INFO", "name": "rag-search.search.api", "message": "Search request: query='ледовый класс Arc4', valid_at=2026-06-19"}
{"timestamp": "2026-06-22 17:59:14,255", "severity": "INFO", "name": "rag-search.search.hybrid", "message": "S2 dense_rerank: query='ледовый класс Arc4'"}
{"timestamp": "2026-06-22 17:59:17,586", "severity": "WARNING", "name": "rag-search.search.hybrid", "message": "TEI reranker unavailable, will use fallback"}
{"timestamp": "2026-06-22 17:59:17,586", "severity": "INFO", "name": "rag-search.search.hybrid", "message": "Search completed: 4 results (total_found=4), strategy=dense_rerank"}
{"timestamp": "2026-06-22 17:59:17,587", "severity": "ERROR", "name": "rag-search.search.api", "message": "Search failed: column d.valid_from does not exist", "exc_info": "Traceback (most recent call last):\n  File \"/app/backend/rag_search_service/app/api/v1/search.py\", line 135, in search_chunks\n    rows = await conn.fetch(base_query, *params)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/usr/local/lib/python3.13/site-packages/asyncpg/connection.py\", line 694, in fetch\n    return await self._execute(\n           ^^^^^^^^^^^^^^^^^^^^\n    ...<5 lines>...\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/asyncpg/connection.py\", line 1873, in _execute\n    result, _ = await self.__execute(\n                ^^^^^^^^^^^^^^^^^^^^^\n    ...<7 lines>...\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/asyncpg/connection.py\", line 1970, in __execute\n    result, stmt = await self._do_execute(\n                   ^^^^^^^^^^^^^^^^^^^^^^^\n    ...<5 lines>...\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/asyncpg/connection.py\", line 2013, in _do_execute\n    stmt = await self._get_statement(\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\n    ...<4 lines>...\n    )\n    ^\n  File \"/usr/local/lib/python3.13/site-packages/asyncpg/connection.py\", line 443, in _get_statement\n    statement = await self._protocol.prepare(\n                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n    ...<5 lines>...\n    )\n    ^\n  File \"asyncpg/protocol/protocol.pyx\", line 165, in prepare\nasyncpg.exceptions.UndefinedColumnError: column d.valid_from does not exist"}
{"timestamp": "2026-06-22 17:59:17,591", "severity": "INFO", "name": "app.core.middleware", "message": "<-- POST /api/v1/rag/search | 500 | 3.379s"}

```
