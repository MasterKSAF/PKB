# Supervisor Logs

**Generated:** 2026-06-26T14:00:53.149976+00:00


---

## 📋 Быстрая навигация


- [ℹ️ INFO — auth.err](#auth-err)
- [❌ ERROR — auth.log](#auth-log)
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
- [ℹ️ INFO — parser.err](#parser-err)
- [❌ ERROR — parser.log](#parser-log)
- [ℹ️ INFO — query.err](#query-err)
- [❌ ERROR — query.log](#query-log)
- [ℹ️ INFO — rag_builder.err](#rag_builder-err)
- [ℹ️ INFO — rag_builder.log](#rag_builder-log)
- [ℹ️ INFO — rag_search.err](#rag_search-err)
- [ℹ️ INFO — rag_search.log](#rag_search-log)
- [ℹ️ INFO — registry.err](#registry-err)
- [ℹ️ INFO — registry.log](#registry-log)


---

## ℹ️ Info-логи

_16 файл(ов) без ошибок (пропущены): auth.err, converter_validator.log, gateway.err, gateway.log, integration.err, integration.log, ocr.err, orchestrator.err, parser.err, query.err, rag_builder.err, rag_builder.log, rag_search.err, rag_search.log, registry.err, registry.log_


## ❌ Error-логи


### auth-log

**❌ ERROR** — `/var/log/supervisor/auth.log`


```

{"timestamp": "2026-06-26 17:00:39,802", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 17:00:39,803", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.16s."}
{"timestamp": "2026-06-26 17:00:40,455", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 17:00:40,733", "severity": "INFO", "name": "app.services.user_service", "message": "User created: prepare-user-482430@test.com"}
{"timestamp": "2026-06-26 17:00:40,765", "severity": "WARNING", "name": "app.services.user_service", "message": "Attempt to create duplicate role: knowledge_admin"}
{"timestamp": "2026-06-26 17:00:40,995", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 17:00:41,050", "severity": "INFO", "name": "app.services.auth_service", "message": "Refresh token revoked for user: u-60006fc915fc"}
{"timestamp": "2026-06-26 17:00:41,314", "severity": "INFO", "name": "app.services.user_service", "message": "User created: test@test.com"}
{"timestamp": "2026-06-26 17:00:41,371", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-d019dd0cb5a0"}
{"timestamp": "2026-06-26 17:00:41,404", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-d019dd0cb5a0"}
{"timestamp": "2026-06-26 17:00:41,434", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-d019dd0cb5a0"}
{"timestamp": "2026-06-26 17:00:41,474", "severity": "INFO", "name": "app.services.user_service", "message": "Role created: viewer"}
{"timestamp": "2026-06-26 17:00:41,822", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 17:00:43,823", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 17:00:43,825", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.96s."}
{"timestamp": "2026-06-26 17:00:44,357", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 17:00:46,660", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 17:00:46,854", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 17:00:46,856", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.19s."}
{"timestamp": "2026-06-26 17:00:47,379", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 17:00:47,662", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 17:00:47,663", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.10s."}
{"timestamp": "2026-06-26 17:00:48,730", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 17:00:49,899", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 1 for user: admin@example.com"}
{"timestamp": "2026-06-26 17:00:49,911", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 17:00:50,248", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 2 for user: admin@example.com"}
{"timestamp": "2026-06-26 17:00:51,609", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 17:00:51,610", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.01s."}
{"timestamp": "2026-06-26 17:00:53,085", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}

```


### converter_validator-err

**❌ ERROR** — `/var/log/supervisor/converter_validator.err`


```

Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-26 17:00:40,009", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 2.31s."}
{"timestamp": "2026-06-26 17:00:46,465", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 17:00:47,980", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.07s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-26 17:00:45 | c5cf68de104e45a2 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents/check-uniqueness -> 200 (0.043s)
2026-06-26 17:00:45 | c5cf68de104e45a2 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:45 | c5cf68de104e45a2 | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.019s)
2026-06-26 17:00:45 | c5cf68de104e45a2 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 17:00:45 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-26 17:00:45 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "GET /api/v1/drafts/ HTTP/1.1" 307
2026-06-26 17:00:45 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "GET /api/v1/drafts HTTP/1.1" 405
2026-06-26 17:00:45 | 6fbc8b199ad54914 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:45 | 6fbc8b199ad54914 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/4 -> 200 (0.015s)
2026-06-26 17:00:45 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "GET /api/v1/drafts/4 HTTP/1.1" 200
2026-06-26 17:00:45 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "GET /api/v1/drafts/4/tasks HTTP/1.1" 200
2026-06-26 17:00:45 | a65818940c034282 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:45 | a65818940c034282 | services.base_client         | INFO     | HTTP DELETE /api/v1/registry/drafts/4 -> 200 (0.017s)
2026-06-26 17:00:45 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "DELETE /api/v1/drafts/4 HTTP/1.1" 204
2026-06-26 17:00:45 | 80aa4b05d11f4d45 | orchestrator.pipeline        | INFO     | Approving draft
2026-06-26 17:00:45 | 80aa4b05d11f4d45 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:45 | 80aa4b05d11f4d45 | services.base_client         | ERROR    | HTTP error: GET /api/v1/registry/drafts/4 -> 404 (0.067s, retries exhausted)
2026-06-26 17:00:45 | 80aa4b05d11f4d45 | orchestrator.pipeline        | ERROR    | Failed to get draft data from Registry: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/4'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 17:00:46 | 80aa4b05d11f4d45 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents -> 201 (0.035s)
2026-06-26 17:00:46 | 80aa4b05d11f4d45 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:46 | 80aa4b05d11f4d45 | services.base_client         | ERROR    | HTTP error: POST /api/v1/registry/drafts/4/snapshot -> 404 (0.014s, retries exhausted)
2026-06-26 17:00:46 | 80aa4b05d11f4d45 | orchestrator.pipeline        | WARNING  | Failed to save preview snapshot: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/4/snapshot'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 17:00:46 | 80aa4b05d11f4d45 | orchestrator.pipeline        | INFO     | Enqueued full OCR step
2026-06-26 17:00:46 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "PATCH /api/v1/drafts/4/decide HTTP/1.1" 200
2026-06-26 17:00:46 | 61fff67c28ca4bc2 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:46 | 61fff67c28ca4bc2 | services.base_client         | ERROR    | HTTP error: PATCH /api/v1/registry/drafts/4/metadata -> 404 (0.079s, retries exhausted)
2026-06-26 17:00:46 | 61fff67c28ca4bc2 | app.api.v1.endpoints.drafts  | WARNING  | Registry 404 on metadata update for draft 4 (expected)
2026-06-26 17:00:46 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "PATCH /api/v1/drafts/4/metadata HTTP/1.1" 404
2026-06-26 17:00:46 | b11c2e285f324642 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:46 | b11c2e285f324642 | services.base_client         | ERROR    | HTTP error: GET /api/v1/registry/drafts/4/preview -> 404 (0.082s, retries exhausted)
2026-06-26 17:00:46 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "GET /api/v1/drafts/4/preview HTTP/1.1" 404
2026-06-26 17:00:46 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 4.45s.
2026-06-26 17:00:46 | 0fc906f278fb4229 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:46 | 0fc906f278fb4229 | services.base_client         | ERROR    | HTTP error: GET /api/v1/registry/drafts/4 -> 404 (0.079s, retries exhausted)
2026-06-26 17:00:46 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "POST /api/v1/drafts/4/preview HTTP/1.1" 404
2026-06-26 17:00:46 | 0562eb2b0aef475f | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 17:00:46 | 0562eb2b0aef475f | services.base_client         | ERROR    | HTTP error: GET /api/v1/registry/drafts/4 -> 404 (0.086s, retries exhausted)
2026-06-26 17:00:46 | 0562eb2b0aef475f | app.api.v1.endpoints.drafts  | WARNING  | Registry check failed for draft 4: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/4'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 17:00:46 | -                | uvicorn.access               | INFO     | 172.18.0.1:43516 - "GET /api/v1/drafts/4/preview/status?longpoll=0 HTTP/1.1" 200
2026-06-26 17:00:51 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.
2026-06-26 17:00:51 | -                | uvicorn.access               | INFO     | 127.0.0.1:45908 - "POST /api/v1/drafts HTTP/1.1" 422
2026-06-26 17:00:51 | -                | uvicorn.access               | INFO     | 127.0.0.1:45908 - "GET /api/v1/documents/queue HTTP/1.1" 200
2026-06-26 17:00:51 | -                | uvicorn.access               | INFO     | 127.0.0.1:45908 - "GET /api/v1/documents/4/status?longpoll=5 HTTP/1.1" 404
2026-06-26 17:00:51 | -                | uvicorn.access               | INFO     | 127.0.0.1:45908 - "GET /api/v1/documents/4/errors?page=1&page_size=10 HTTP/1.1" 404
2026-06-26 17:00:51 | -                | uvicorn.access               | INFO     | 127.0.0.1:45908 - "POST /api/v1/documents/4/reprocess HTTP/1.1" 409
2026-06-26 17:00:51 | -                | uvicorn.access               | INFO     | 127.0.0.1:45908 - "POST /api/v1/documents/4/versions HTTP/1.1" 404
2026-06-26 17:00:51 | -                | uvicorn.access               | INFO     | 127.0.0.1:45908 - "GET /api/v1/documents/4/tasks HTTP/1.1" 200

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

{"timestamp": "2026-06-26 17:00:43,981", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Task 12345 already exists with status accepted, returning existing response"}
{"timestamp": "2026-06-26 17:00:44,006", "severity": "INFO", "name": "app.api.v1.endpoints.status", "message": "Returning status for task 12345: accepted"}
{"timestamp": "2026-06-26 17:00:44,027", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Task 12345 not completed yet, returning 409"}
Jun 26, 2026 5:00:44 PM org.opendataloader.pdf.processors.DocumentProcessor preprocessing
INFO: File name: /tmp/tmpm64pxgc0.pdf
Jun 26, 2026 5:00:44 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11901 in stream 39 0 obj)
Jun 26, 2026 5:00:44 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16578 in stream 47 0 obj)
Jun 26, 2026 5:00:44 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16513 in stream 55 0 obj)
Jun 26, 2026 5:00:44 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 26, 2026 5:00:44 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 26, 2026 5:00:44 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 26, 2026 5:00:44 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 26, 2026 5:00:44 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 26, 2026 5:00:44 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 26, 2026 5:00:44 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 26, 2026 5:00:44 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
{"timestamp": "2026-06-26 17:00:45,509", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 17:00:46,512", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.05s."}
Jun 26, 2026 5:00:47 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmpszh15ynk/tmpm64pxgc0.json
Jun 26, 2026 5:00:47 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmpszh15ynk/tmpm64pxgc0.md
Jun 26, 2026 5:00:47 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmpszh15ynk/tmpm64pxgc0.html
{"timestamp": "2026-06-26 17:00:47,603", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 12345"}
{"timestamp": "2026-06-26 17:00:47,604", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-26 17:00:48,293", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-26 17:00:48,304", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-26 17:00:48,308", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-26 17:00:48,311", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-26 17:00:48,314", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-26 17:00:48,316", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-26 17:00:48,317", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Uploaded 6/6 images for task 12345 (errors: 0)"}
{"timestamp": "2026-06-26 17:00:48,328", "severity": "INFO", "name": "app.services.result_builder", "message": "Result built for task 12345, mode=full"}
{"timestamp": "2026-06-26 17:00:48,329", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 12345"}
{"timestamp": "2026-06-26 17:00:48,329", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 12345"}
{"timestamp": "2026-06-26 17:00:48,329", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline completed for task 12345"}
{"timestamp": "2026-06-26 17:00:52,920", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 17:00:53,923", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.93s."}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-26 17:00:47,941", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"5dfd30c0-cf0f-47ec-afb7-b816cd493044\", \"user_id\": null, \"draft_id\": null, \"method\": \"PUT\", \"path\": \"/api/v1/chat/projects/2\", \"status\": 200, \"duration_ms\": 19}"}
{"timestamp": "2026-06-26 17:00:47,952", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"22b63607-ac30-4ef6-a9cd-908c1635bb9b\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 8}"}
{"timestamp": "2026-06-26 17:00:47,978", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"ce20b798-3bcc-4509-be7f-22583cdb3c14\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions\", \"status\": 200, \"duration_ms\": 17}"}
{"timestamp": "2026-06-26 17:00:47,992", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"95fe51f5-9fb8-4efc-9ac1-7ed19aef3dc6\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/2\", \"status\": 200, \"duration_ms\": 10}"}
{"timestamp": "2026-06-26 17:00:48,010", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"0e765db1-a858-4994-b137-ad0bf1129944\", \"user_id\": null, \"draft_id\": null, \"method\": \"PUT\", \"path\": \"/api/v1/chat/sessions/2\", \"status\": 200, \"duration_ms\": 14}"}
{"timestamp": "2026-06-26 17:00:48,031", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"15cc4d5f-76b6-409b-8181-072608b433d7\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/2/messages\", \"status\": 202, \"duration_ms\": 16}"}
{"timestamp": "2026-06-26 17:00:48,032", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline started", "message_id": 4, "session_id": 2}
{"timestamp": "2026-06-26 17:00:48,051", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"afeea17a-5c50-4b7c-858a-84378732fc50\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/2/messages/last\", \"status\": 200, \"duration_ms\": 15}"}
{"timestamp": "2026-06-26 17:00:48,098", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:48,101", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 17:00:48,107", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"b391381f-3ec9-4e05-bd2d-0e716ccc71ac\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/2/messages\", \"status\": 200, \"duration_ms\": 47}"}
{"timestamp": "2026-06-26 17:00:48,129", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"2978f715-6444-4b91-8b8e-e87e4e05fc23\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/2/messages/4\", \"status\": 200, \"duration_ms\": 15}"}
{"timestamp": "2026-06-26 17:00:48,141", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"10e15658-4e8d-4988-b65c-1631a43d3867\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/2/messages/search\", \"status\": 200, \"duration_ms\": 7}"}
{"timestamp": "2026-06-26 17:00:48,155", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"f61f9a01-cb08-4f90-b1e1-12a7df0d1dcf\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/2/context\", \"status\": 200, \"duration_ms\": 7}"}
{"timestamp": "2026-06-26 17:00:48,169", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"56b56ac5-d2a2-412d-b488-d37821b5f1a0\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/2/export\", \"status\": 200, \"duration_ms\": 9}"}
{"timestamp": "2026-06-26 17:00:48,182", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"2d18b9e3-b103-4ce1-a235-306cf77acac3\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/feedback\", \"status\": 200, \"duration_ms\": 10}"}
{"timestamp": "2026-06-26 17:00:48,209", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"e956a312-4dee-48c8-b3db-73607d05f231\", \"user_id\": null, \"draft_id\": null, \"method\": \"DELETE\", \"path\": \"/api/v1/chat/sessions/2\", \"status\": 200, \"duration_ms\": 19}"}
{"timestamp": "2026-06-26 17:00:48,235", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"faa74dbf-c8d7-4dc8-84f3-8d6e8e4ce4b8\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history\", \"status\": 200, \"duration_ms\": 20}"}
{"timestamp": "2026-06-26 17:00:48,243", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"8507e95c-d24f-434f-a47a-80577303b356\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history/export\", \"status\": 200, \"duration_ms\": 2}"}
{"timestamp": "2026-06-26 17:00:48,267", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"e714d169-c048-4188-8ed8-2da590bcb574\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 17}"}
{"timestamp": "2026-06-26 17:00:48,275", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"854f7bf0-ad5c-49a8-87c5-bafd42b825fb\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/ask\", \"status\": 200, \"duration_ms\": 3}"}
{"timestamp": "2026-06-26 17:00:48,303", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"af1f783f-d357-42ca-b6ff-e3d791a67b35\", \"user_id\": null, \"draft_id\": null, \"method\": \"DELETE\", \"path\": \"/api/v1/chat/projects/2\", \"status\": 204, \"duration_ms\": 23}"}
{"timestamp": "2026-06-26 17:00:48,922", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:48,924", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 17:00:49,138", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:49,139", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 17:00:49,917", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"cee540ac-1c59-43b4-b573-c6ed395dc0c9\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 1}"}
{"timestamp": "2026-06-26 17:00:50,781", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 17:00:50,996", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:50,999", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 17:00:51,200", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:51,201", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 17:00:51,544", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 17:00:51,544", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.99s."}
{"timestamp": "2026-06-26 17:00:51,785", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 17:00:51,787", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.94s."}
{"timestamp": "2026-06-26 17:00:51,792", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"0a6dee35-5639-43db-8380-4b5fdcdb6b65\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions\", \"status\": 401, \"duration_ms\": 1}"}
{"timestamp": "2026-06-26 17:00:51,805", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"f4a1b291-8af1-4b94-8f63-2adfeabe2c55\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-26 17:00:51,824", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"05657957-93e1-43d8-bf3a-53dcf21cf3fa\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history/export\", \"status\": 401, \"duration_ms\": 1}"}
{"timestamp": "2026-06-26 17:00:51,844", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"d718a9f6-5cf9-4489-9303-8ef18adad1d8\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 401, \"duration_ms\": 1}"}
{"timestamp": "2026-06-26 17:00:53,091", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:53,092", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 17:00:53,116", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"7d087d8d-aa7d-4f15-a380-8a323cbd61f7\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 10}"}
{"timestamp": "2026-06-26 17:00:53,143", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"aefb3029-1eb8-4894-a300-84f120773ecf\", \"user_id\": \"u-60006fc915fc\", \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 6}"}
{"timestamp": "2026-06-26 17:00:53,268", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:53,269", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 17:00:54,155", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:54,156", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 17:00:54,355", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 17:00:54,357", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}

```
