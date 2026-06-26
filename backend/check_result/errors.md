# Supervisor Logs

**Generated:** 2026-06-26T12:35:12.865107+00:00


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

{"timestamp": "2026-06-26 15:34:28,744", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:29,016", "severity": "INFO", "name": "app.services.user_service", "message": "User created: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:29,294", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:29,768", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 1 for user: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:30,004", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 2 for user: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:30,242", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 3 for user: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:30,484", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 4 for user: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:30,721", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 5 for user: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:30,955", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 6 for user: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:31,016", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-9bf89ddd7e1f"}
{"timestamp": "2026-06-26 15:34:31,039", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login for unknown or inactive user: pipeline-user-20260626173428453874@test.com"}
{"timestamp": "2026-06-26 15:34:31,276", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:31,641", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:31,641", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.12s."}
{"timestamp": "2026-06-26 15:34:32,147", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:33,258", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:34,258", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:34,258", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.03s."}
{"timestamp": "2026-06-26 15:34:34,267", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:40,681", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:42,210", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:42,974", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:42,974", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.06s."}
{"timestamp": "2026-06-26 15:34:45,686", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:45,687", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.98s."}
{"timestamp": "2026-06-26 15:34:51,434", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:52,435", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:52,435", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-26 15:34:52,616", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:53,887", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:55,210", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 2.10s."}
{"timestamp": "2026-06-26 15:34:57,310", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:57,864", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:58,332", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:58,647", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:34:58,895", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:58,895", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.01s."}
{"timestamp": "2026-06-26 15:34:59,205", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:35:00,672", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:01,129", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:35:01,674", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:35:01,675", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.02s."}
{"timestamp": "2026-06-26 15:35:06,248", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:35:06,812", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:35:06,959", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:07,301", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 15:35:11,303", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:35:11,303", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.96s."}
{"timestamp": "2026-06-26 15:35:11,969", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:35:11,970", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.19s."}

```


### converter_validator-err

**❌ ERROR** — `/var/log/supervisor/converter_validator.err`


```

Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-26 15:34:22,701", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:23,227", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 4.73s."}
{"timestamp": "2026-06-26 15:34:27,957", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:28,958", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
{"timestamp": "2026-06-26 15:34:35,619", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:36,620", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.04s."}
{"timestamp": "2026-06-26 15:34:43,574", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:44,576", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.03s."}
{"timestamp": "2026-06-26 15:34:51,434", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:52,434", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.89s."}
{"timestamp": "2026-06-26 15:34:59,205", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:00,206", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.95s."}
{"timestamp": "2026-06-26 15:35:07,567", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:08,568", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.89s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-26 15:35:01 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents/check-uniqueness -> 200 (0.010s)
2026-06-26 15:35:01 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:01 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.014s)
2026-06-26 15:35:01 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 15:35:01 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-26 15:35:01 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "GET /api/v1/tasks/13/status HTTP/1.1" 200
2026-06-26 15:35:01 | d75b2a2b-5b1b-4ea0-a8b0-0a87167f0250 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:01 | d75b2a2b-5b1b-4ea0-a8b0-0a87167f0250 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/12 -> 200 (0.008s)
2026-06-26 15:35:01 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "GET /api/v1/drafts/12 HTTP/1.1" 200
2026-06-26 15:35:01 | d7171909-9b6a-4f68-b959-8a24ceebc893 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:01 | d7171909-9b6a-4f68-b959-8a24ceebc893 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/12 -> 200 (0.011s)
2026-06-26 15:35:01 | d7171909-9b6a-4f68-b959-8a24ceebc893 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 15:35:01 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "POST /api/v1/drafts/12/preview HTTP/1.1" 202
2026-06-26 15:35:01 | ce22ef83-72c5-4b5b-ac95-1ed5545b9f61 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:01 | ce22ef83-72c5-4b5b-ac95-1ed5545b9f61 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/12 -> 200 (0.010s)
2026-06-26 15:35:02 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "GET /api/v1/drafts/12/preview/status?longpoll=1 HTTP/1.1" 200
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | orchestrator.pipeline        | INFO     | Approving draft
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/12 -> 200 (0.009s)
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/12/preview -> 200 (0.013s)
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents -> 201 (0.020s)
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | services.base_client         | ERROR    | HTTP error: POST /api/v1/registry/drafts/12/snapshot -> 404 (0.007s, retries exhausted)
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | orchestrator.pipeline        | WARNING  | Failed to save preview snapshot: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/12/snapshot'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 15:35:02 | 2bac4279-17e7-4b7e-81f8-fdc139e18a81 | orchestrator.pipeline        | INFO     | Enqueued full OCR step
2026-06-26 15:35:02 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "PATCH /api/v1/drafts/12/decide HTTP/1.1" 200
2026-06-26 15:35:02 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 3.59s.
2026-06-26 15:35:05 | 1292bace-10e9-4823-a894-dbe5e8566c4c | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:06 | 1292bace-10e9-4823-a894-dbe5e8566c4c | services.base_client         | INFO     | HTTP DELETE /api/v1/registry/drafts/12 -> 200 (0.014s)
2026-06-26 15:35:06 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "DELETE /api/v1/drafts/12 HTTP/1.1" 204
2026-06-26 15:35:06 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.
2026-06-26 15:35:06 | 2b486c7c-b2bc-4237-9e32-6262289748c9 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:06 | 2b486c7c-b2bc-4237-9e32-6262289748c9 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents/check-uniqueness -> 200 (0.010s)
2026-06-26 15:35:06 | 2b486c7c-b2bc-4237-9e32-6262289748c9 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:06 | 2b486c7c-b2bc-4237-9e32-6262289748c9 | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.014s)
2026-06-26 15:35:06 | 2b486c7c-b2bc-4237-9e32-6262289748c9 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 15:35:06 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-26 15:35:06 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "GET /api/v1/tasks/14/status HTTP/1.1" 200
2026-06-26 15:35:06 | fbd61338-1d38-46b6-93d1-334b0be3d719 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:06 | fbd61338-1d38-46b6-93d1-334b0be3d719 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/13 -> 200 (0.010s)
2026-06-26 15:35:06 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "GET /api/v1/drafts/13 HTTP/1.1" 200
2026-06-26 15:35:06 | 044412f7-9715-4a87-b699-e4a6c0b7801d | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:06 | 044412f7-9715-4a87-b699-e4a6c0b7801d | services.base_client         | INFO     | HTTP PATCH /api/v1/registry/drafts/13/metadata -> 200 (0.028s)
2026-06-26 15:35:06 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "PATCH /api/v1/drafts/13/metadata HTTP/1.1" 200
2026-06-26 15:35:06 | 4a031337-43e3-4378-9db5-c1c73e2b9acb | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 15:35:06 | 4a031337-43e3-4378-9db5-c1c73e2b9acb | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/13 -> 200 (0.012s)
2026-06-26 15:35:06 | -                | uvicorn.access               | INFO     | 127.0.0.1:35332 - "GET /api/v1/drafts/13 HTTP/1.1" 200
2026-06-26 15:35:11 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 0.93s.
2026-06-26 15:35:12 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 1.94s.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

INFO: File name: /tmp/tmp2nl6u94t.pdf
Jun 26, 2026 3:34:55 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11901 in stream 39 0 obj)
Jun 26, 2026 3:34:55 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16578 in stream 47 0 obj)
Jun 26, 2026 3:34:55 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16513 in stream 55 0 obj)
Jun 26, 2026 3:34:55 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 26, 2026 3:34:55 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 26, 2026 3:34:55 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 26, 2026 3:34:55 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 26, 2026 3:34:55 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 26, 2026 3:34:55 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 26, 2026 3:34:55 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 26, 2026 3:34:55 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
Jun 26, 2026 3:34:56 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmp_vaa11rg/tmp2nl6u94t.json
Jun 26, 2026 3:34:56 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmp_vaa11rg/tmp2nl6u94t.md
Jun 26, 2026 3:34:56 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmp_vaa11rg/tmp2nl6u94t.html
{"timestamp": "2026-06-26 15:34:56,351", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-26 15:34:56,352", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-26 15:34:56,792", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-26 15:34:56,793", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-26 15:34:56,794", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-26 15:34:56,797", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-26 15:34:56,798", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-26 15:34:56,804", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-26 15:34:56,804", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Uploaded 6/6 images for task 20002 (errors: 0)"}
{"timestamp": "2026-06-26 15:34:56,808", "severity": "INFO", "name": "app.services.result_builder", "message": "Result built for task 20002, mode=full"}
{"timestamp": "2026-06-26 15:34:56,808", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-26 15:34:56,809", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-26 15:34:56,809", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-26 15:34:56,940", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Result for task 20002 returned successfully"}
{"timestamp": "2026-06-26 15:34:59,956", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:00,872", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:01,875", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.11s."}
{"timestamp": "2026-06-26 15:35:09,037", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:10,038", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.90s."}
{"timestamp": "2026-06-26 15:35:12,032", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:12,106", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to localhost:4317, retrying in 2.17s."}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-26 15:34:35,726", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:36,525", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:36,526", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:37,557", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:37,559", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:37,760", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:37,761", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:39,464", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:39,591", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:39,592", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:41,793", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:41,794", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:42,577", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:42,825", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:42,826", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:43,578", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:43,579", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.14s."}
{"timestamp": "2026-06-26 15:34:43,628", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:43,629", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:44,466", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:44,467", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.86s."}
{"timestamp": "2026-06-26 15:34:44,660", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:44,661", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:44,858", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:44,858", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:44,863", "severity": "ERROR", "name": "app.services.pipeline", "message": "llm generation failed after retries", "message_id": 2}
{"timestamp": "2026-06-26 15:34:46,694", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 15:34:46,694", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 15:34:46,699", "severity": "ERROR", "name": "app.services.pipeline", "message": "llm generation failed after retries", "message_id": 4}
{"timestamp": "2026-06-26 15:34:52,217", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:53,219", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:53,220", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 15:34:53,981", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:34:55,886", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.90s."}
{"timestamp": "2026-06-26 15:34:58,982", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:34:58,982", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.95s."}
{"timestamp": "2026-06-26 15:35:01,791", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.86s."}
{"timestamp": "2026-06-26 15:35:02,366", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:03,367", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:35:03,368", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.14s."}
{"timestamp": "2026-06-26 15:35:06,976", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:08,338", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 3.97s."}
{"timestamp": "2026-06-26 15:35:11,324", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"14cc4342-9d1e-4a32-b347-2402fdf1cd93\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-26 15:35:11,834", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"27aadb51-cf44-4d86-b6f4-2dbb396b0e57\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-26 15:35:11,978", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:35:11,978", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 15:35:12,313", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 15:35:12,349", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"463ffac0-c099-49f5-90e5-fa24cc4287ad\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-26 15:35:13,314", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 15:35:13,314", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}

```
