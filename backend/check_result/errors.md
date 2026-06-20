# Supervisor Logs

**Generated:** 2026-06-20T13:08:47.599338+00:00


---

## 📋 Быстрая навигация


- [ℹ️ INFO — auth.err](#auth-err)
- [ℹ️ INFO — auth.log](#auth-log)
- [❌ ERROR — converter_validator.err](#converter_validator-err)
- [ℹ️ INFO — converter_validator.log](#converter_validator-log)
- [ℹ️ INFO — gateway.err](#gateway-err)
- [ℹ️ INFO — gateway.log](#gateway-log)
- [ℹ️ INFO — integration.err](#integration-err)
- [ℹ️ INFO — integration.log](#integration-log)
- [ℹ️ INFO — ocr.err](#ocr-err)
- [❌ ERROR — ocr.log](#ocr-log)
- [ℹ️ INFO — orchestrator.err](#orchestrator-err)
- [❌ ERROR — orchestrator.log](#orchestrator-log)
- [❌ ERROR — parser.err](#parser-err)
- [❌ ERROR — parser.log](#parser-log)
- [❌ ERROR — query.err](#query-err)
- [ℹ️ INFO — query.log](#query-log)
- [ℹ️ INFO — rag_builder.err](#rag_builder-err)
- [ℹ️ INFO — rag_builder.log](#rag_builder-log)
- [ℹ️ INFO — rag_search.err](#rag_search-err)
- [ℹ️ INFO — rag_search.log](#rag_search-log)
- [ℹ️ INFO — registry.err](#registry-err)
- [ℹ️ INFO — registry.log](#registry-log)


---

## ℹ️ Info-логи

_16 файл(ов) без ошибок (пропущены): auth.err, auth.log, converter_validator.log, gateway.err, gateway.log, integration.err, integration.log, ocr.err, orchestrator.err, query.log, rag_builder.err, rag_builder.log, rag_search.err, rag_search.log, registry.err, registry.log_


## ❌ Error-логи


### converter_validator-err

**❌ ERROR** — `/var/log/supervisor/converter_validator.err`


```

/usr/local/lib/python3.13/site-packages/starlette/_exception_handler.py:59: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
  response = await handler(conn, exc)  # type: ignore[arg-type]

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-20 16:08:28,044", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-20 16:08:29,045", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.16s."}
{"timestamp": "2026-06-20 16:08:35,824", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-20 16:08:36,825", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.94s."}
{"timestamp": "2026-06-20 16:08:43,870", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-20 16:08:44,872", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/health HTTP/1.1" 404
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "POST /api/v1/drafts/ HTTP/1.1" 422
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/system/health HTTP/1.1" 200
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/monitor/metrics HTTP/1.1" 404
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/health HTTP/1.1" 404
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/tasks/ HTTP/1.1" 200
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/documents/ HTTP/1.1" 200
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/documents/queue HTTP/1.1" 200
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/documents/1 HTTP/1.1" 200
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "DELETE /api/v1/documents/1 HTTP/1.1" 200
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/documents/1/status HTTP/1.1" 200
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/documents/1/file HTTP/1.1" 200
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "POST /api/v1/drafts/ HTTP/1.1" 422
2026-06-20 16:08:27 | 31844c9152374f23 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-20 16:08:27 | 31844c9152374f23 | services.base_client         | ERROR    | HTTP error: GET /registry/drafts -> 404 (0.004s, retries exhausted)
2026-06-20 16:08:27 | 31844c9152374f23 | app.api.v1.endpoints.drafts  | ERROR    | Failed to list drafts: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts?page=1&page_size=50'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-20 16:08:27 | -                | uvicorn.access               | INFO     | 172.19.0.1:57912 - "GET /api/v1/drafts/ HTTP/1.1" 200
2026-06-20 16:08:31 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 1.05s.
2026-06-20 16:08:32 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 1.63s.
2026-06-20 16:08:34 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 4.69s.
2026-06-20 16:08:38 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "GET /api/v1/health HTTP/1.1" 404
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "POST /api/v1/drafts/ HTTP/1.1" 422
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "GET /api/v1/tasks/%7Btask_id%7D/status HTTP/1.1" 404
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "GET /api/v1/drafts/%7Bdraft_id%7D HTTP/1.1" 422
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "POST /api/v1/drafts/%7Bdraft_id%7D/preview HTTP/1.1" 422
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "GET /api/v1/drafts/%7Bdraft_id%7D/preview/status?longpoll=0 HTTP/1.1" 422
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "PATCH /api/v1/drafts/%7Bdraft_id%7D/decide HTTP/1.1" 422
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "GET /api/v1/drafts/%7Bdraft_id%7D HTTP/1.1" 422
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "POST /api/v1/drafts/ HTTP/1.1" 422
2026-06-20 16:08:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37858 - "GET /api/v1/tasks/%7Btask_id_2%7D/status HTTP/1.1" 404

```


### parser-err

**❌ ERROR** — `/var/log/supervisor/parser.err`


```

/usr/local/lib/python3.13/site-packages/starlette/_exception_handler.py:59: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
  response = await handler(conn, exc)  # type: ignore[arg-type]

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

{"timestamp": "2026-06-20 16:08:42,417", "severity": "INFO", "name": "app.api.v1.endpoints.status", "message": "Returning status for task 20002: TaskStatus.ACCEPTED"}
{"timestamp": "2026-06-20 16:08:42,418", "severity": "INFO", "name": "app.core.minio_client", "message": "Downloaded multi-doc-2-1781960917.pdf, size=123616 bytes"}
{"timestamp": "2026-06-20 16:08:42,422", "severity": "INFO", "name": "app.core.validator", "message": "Security check passed"}
{"timestamp": "2026-06-20 16:08:42,422", "severity": "INFO", "name": "app.core.validator", "message": "Validation passed, MIME=application/pdf"}
{"timestamp": "2026-06-20 16:08:42,424", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Parsing PDF for task 20002, options={}"}
Jun 20, 2026 4:08:42 PM org.opendataloader.pdf.processors.DocumentProcessor preprocessing
INFO: File name: /tmp/tmpnd5hdfr0.pdf
Jun 20, 2026 4:08:42 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11901 in stream 39 0 obj)
Jun 20, 2026 4:08:42 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16578 in stream 47 0 obj)
Jun 20, 2026 4:08:42 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16513 in stream 55 0 obj)
Jun 20, 2026 4:08:42 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 20, 2026 4:08:42 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 20, 2026 4:08:42 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 20, 2026 4:08:42 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 20, 2026 4:08:42 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 20, 2026 4:08:42 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 20, 2026 4:08:42 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 20, 2026 4:08:42 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
Jun 20, 2026 4:08:43 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmpkt4k2ks7/tmpnd5hdfr0.json
Jun 20, 2026 4:08:43 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmpkt4k2ks7/tmpnd5hdfr0.md
Jun 20, 2026 4:08:44 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmpkt4k2ks7/tmpnd5hdfr0.html
{"timestamp": "2026-06-20 16:08:44,065", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-20 16:08:44,066", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-20 16:08:44,196", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_0_617ab711356b06f8.png, size=7705 bytes"}
{"timestamp": "2026-06-20 16:08:44,295", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_1_f8052b5c9759d1e1.png, size=5144 bytes"}
{"timestamp": "2026-06-20 16:08:44,390", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_2_1d9c0ba54ed582b4.png, size=4605 bytes"}
{"timestamp": "2026-06-20 16:08:44,479", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_3_7cba379c2bca3a95.png, size=3890 bytes"}
{"timestamp": "2026-06-20 16:08:44,574", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_4_3f9976aee3a3dac5.png, size=11303 bytes"}
{"timestamp": "2026-06-20 16:08:44,671", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_5_28bd92663bf750a8.png, size=9275 bytes"}
{"timestamp": "2026-06-20 16:08:44,676", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-20 16:08:44,676", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-20 16:08:44,676", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-20 16:08:44,758", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-20 16:08:45,760", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.87s."}
{"timestamp": "2026-06-20 16:08:46,801", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-20 16:08:48,489", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 3.99s."}

```


### query-err

**❌ ERROR** — `/var/log/supervisor/query.err`


```

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
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.DataError'>: invalid input for query argument $4: 5 (expected str, got int)
[SQL: INSERT INTO chat_feedback (message_id, answer_id, user_id, rating, useful, comment, aspects, opened_citation_ids, created_at) VALUES ($1::INTEGER, $2::BIGINT, $3::VARCHAR, $4::VARCHAR, $5::BOOLEAN, $6::VARCHAR, $7::JSON, $8::JSON, $9::TIMESTAMP WITH TIME ZONE) RETURNING chat_feedback.feedback_id]
[parameters: (None, None, 'u-001', 5, None, None, 'null', 'null', datetime.datetime(2026, 6, 20, 13, 8, 27, 655494, tzinfo=datetime.timezone.utc))]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
{"request_id": "60b3e111-adb9-482f-9201-0dc260af3fcb", "user_id": null, "draft_id": null, "method": "GET", "path": "/api/v1/chat/history", "status": 200, "duration_ms": 11}
{"request_id": "3625a2a7-0ad4-4017-8a9a-3a02999d616f", "user_id": null, "draft_id": null, "method": "GET", "path": "/api/v1/chat/history/export", "status": 200, "duration_ms": 1}
{"request_id": "92e5750a-9ead-44df-859e-7a35fcf6e770", "user_id": null, "draft_id": null, "method": "POST", "path": "/api/v1/text/search", "status": 200, "duration_ms": 6}
{"request_id": "f34c7482-c94a-4587-81f7-144397d95b6b", "user_id": null, "draft_id": null, "method": "POST", "path": "/api/v1/text/ask", "status": 200, "duration_ms": 3}
{"request_id": "74c84db7-a8af-4b95-b192-2bbcfedefeb1", "user_id": null, "draft_id": null, "method": "GET", "path": "/api/v1/health", "status": 200, "duration_ms": 1}
{"request_id": "05dc5cfe-96b6-4501-8e72-f289eabbe06c", "user_id": null, "draft_id": null, "method": "POST", "path": "/api/v1/chat/sessions", "status": 201, "duration_ms": 9}
{"request_id": "3acf3faa-15d5-41a7-8482-c1ef9097c989", "user_id": null, "draft_id": null, "method": "POST", "path": "/api/v1/chat/sessions/3/messages", "status": 202, "duration_ms": 18}
{"request_id": "6bad3061-6de0-4694-b62b-f48c2babdcf8", "user_id": null, "draft_id": null, "method": "GET", "path": "/api/v1/chat/sessions/3/messages", "status": 200, "duration_ms": 44}
{"request_id": "0fd0c5bc-5527-4000-b562-13b6c0ed6333", "user_id": null, "draft_id": null, "method": "GET", "path": "/api/v1/health", "status": 200, "duration_ms": 1}
{"request_id": "dbc9f9e7-d5f8-4bef-8e8c-bed894d7c33b", "user_id": null, "draft_id": null, "method": "POST", "path": "/api/v1/chat/sessions", "status": 201, "duration_ms": 7}
{"request_id": "82778b0d-bc98-4946-b826-823d16b383ac", "user_id": null, "draft_id": null, "method": "POST", "path": "/api/v1/chat/sessions/4/messages", "status": 202, "duration_ms": 9}
{"request_id": "1b56a717-57b7-4f3c-bcf9-d4d2c9728ca2", "user_id": null, "draft_id": null, "method": "POST", "path": "/api/v1/text/search", "status": 200, "duration_ms": 0}
{"request_id": "53b81dde-4bf4-4d6e-a1a6-86af1e0318c7", "user_id": null, "draft_id": null, "method": "POST", "path": "/api/v1/text/search", "status": 200, "duration_ms": 1}

```
