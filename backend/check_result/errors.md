# Supervisor Logs

**Generated:** 2026-06-23T16:22:46.811670+00:00


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
- [ℹ️ INFO — query.err](#query-err)
- [❌ ERROR — query.log](#query-log)
- [ℹ️ INFO — rag_builder.err](#rag_builder-err)
- [ℹ️ INFO — rag_builder.log](#rag_builder-log)
- [ℹ️ INFO — rag_builder_spk.err](#rag_builder_spk-err)
- [ℹ️ INFO — rag_builder_spk.log](#rag_builder_spk-log)
- [ℹ️ INFO — rag_search.err](#rag_search-err)
- [ℹ️ INFO — rag_search.log](#rag_search-log)
- [ℹ️ INFO — registry.err](#registry-err)
- [ℹ️ INFO — registry.log](#registry-log)


---

## ℹ️ Info-логи

_19 файл(ов) без ошибок (пропущены): auth.err, converter_validator.err, converter_validator.log, gateway.err, gateway.log, integration.err, integration.log, ocr.err, orchestrator.err, parser.err, query.err, rag_builder.err, rag_builder.log, rag_builder_spk.err, rag_builder_spk.log, rag_search.err, rag_search.log, registry.err, registry.log_


## ❌ Error-логи


### auth-log

**❌ ERROR** — `/var/log/supervisor/auth.log`


```

{"timestamp": "2026-06-23 19:22:03,766", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:04,013", "severity": "INFO", "name": "app.services.user_service", "message": "User created: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:04,152", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:04,256", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:04,527", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 1 for user: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:04,756", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 2 for user: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:04,984", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 3 for user: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:05,213", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 4 for user: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:05,445", "severity": "WARNING", "name": "app.services.auth_service", "message": "Account locked after 5 failed attempts: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:05,453", "severity": "WARNING", "name": "app.services.auth_service", "message": "Locked account login attempt: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:05,482", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-968f540f54f3"}
{"timestamp": "2026-06-23 19:22:05,498", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login for unknown or inactive user: pipeline-user-20260623212203545083@test.com"}
{"timestamp": "2026-06-23 19:22:05,744", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:06,168", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:07,966", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:08,083", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:08,084", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.07s."}
{"timestamp": "2026-06-23 19:22:09,186", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:09,186", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.95s."}
{"timestamp": "2026-06-23 19:22:13,859", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:16,805", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:17,805", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:17,806", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.96s."}
{"timestamp": "2026-06-23 19:22:18,786", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:20,616", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.90s."}
{"timestamp": "2026-06-23 19:22:23,787", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:23,787", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.94s."}
{"timestamp": "2026-06-23 19:22:24,229", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:26,507", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:26,589", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 2.02s."}
{"timestamp": "2026-06-23 19:22:27,508", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:27,508", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.09s."}
{"timestamp": "2026-06-23 19:22:32,482", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:36,842", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:36,842", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.89s."}
{"timestamp": "2026-06-23 19:22:37,396", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:37,484", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:37,484", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.05s."}
{"timestamp": "2026-06-23 19:22:37,884", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:38,246", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:38,505", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:38,987", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:40,394", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 2.16s."}
{"timestamp": "2026-06-23 19:22:40,853", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:45,814", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:46,002", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:46,297", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:46,657", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-23 19:22:47,004", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:47,004", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.04s."}

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-23 19:21:57,121", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:21:58,122", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.10s."}
{"timestamp": "2026-06-23 19:22:00,005", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:01,415", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 4.36s."}
{"timestamp": "2026-06-23 19:22:05,771", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:06,773", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.95s."}
{"timestamp": "2026-06-23 19:22:14,033", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:15,033", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.01s."}
{"timestamp": "2026-06-23 19:22:21,911", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:22,912", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.10s."}
{"timestamp": "2026-06-23 19:22:30,563", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:31,564", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
{"timestamp": "2026-06-23 19:22:37,628", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:38,629", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}
{"timestamp": "2026-06-23 19:22:41,513", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 4.79s."}
{"timestamp": "2026-06-23 19:22:46,298", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:47,299", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-23 19:22:40 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:40 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP POST /registry/documents/check-uniqueness -> 200 (0.013s)
2026-06-23 19:22:40 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:40 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP POST /registry/drafts -> 201 (0.011s)
2026-06-23 19:22:40 | 4261c119076a4c4d | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-23 19:22:40 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "POST /api/v1/drafts/ HTTP/1.1" 202
2026-06-23 19:22:40 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "GET /api/v1/tasks/11/status HTTP/1.1" 200
2026-06-23 19:22:40 | d555d6d892ef4a49 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:41 | d555d6d892ef4a49 | services.base_client         | INFO     | HTTP GET /registry/drafts/10 -> 200 (0.007s)
2026-06-23 19:22:41 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "GET /api/v1/drafts/10 HTTP/1.1" 200
2026-06-23 19:22:41 | 67c7304bfa074b05 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:41 | 67c7304bfa074b05 | services.base_client         | INFO     | HTTP GET /registry/drafts/10 -> 200 (0.006s)
2026-06-23 19:22:41 | 67c7304bfa074b05 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-23 19:22:41 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "POST /api/v1/drafts/10/preview HTTP/1.1" 202
2026-06-23 19:22:41 | cefadd6770ec4ec8 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:41 | cefadd6770ec4ec8 | services.base_client         | INFO     | HTTP GET /registry/drafts/10 -> 200 (0.008s)
2026-06-23 19:22:42 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "GET /api/v1/drafts/10/preview/status?longpoll=1 HTTP/1.1" 200
2026-06-23 19:22:42 | 4261c119076a4c4d | orchestrator.pipeline        | INFO     | Approving draft
2026-06-23 19:22:42 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:42 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP GET /registry/drafts/10 -> 200 (0.007s)
2026-06-23 19:22:42 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP GET /registry/drafts/10/preview -> 200 (0.005s)
2026-06-23 19:22:42 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP POST /registry/documents -> 201 (0.013s)
2026-06-23 19:22:42 | 4261c119076a4c4d | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:42 | 4261c119076a4c4d | services.base_client         | ERROR    | HTTP error: POST /registry/drafts/10/snapshot -> 404 (0.002s, retries exhausted)
2026-06-23 19:22:42 | 4261c119076a4c4d | orchestrator.pipeline        | WARNING  | Failed to save preview snapshot: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/10/snapshot'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-23 19:22:42 | 4261c119076a4c4d | orchestrator.pipeline        | INFO     | Enqueued full OCR step
2026-06-23 19:22:42 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "PATCH /api/v1/drafts/10/decide HTTP/1.1" 200
2026-06-23 19:22:42 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 3.90s.
2026-06-23 19:22:45 | 9a0a7279486a4b3e | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:45 | 9a0a7279486a4b3e | services.base_client         | INFO     | HTTP DELETE /registry/drafts/10 -> 200 (0.012s)
2026-06-23 19:22:45 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "DELETE /api/v1/drafts/10 HTTP/1.1" 204
2026-06-23 19:22:45 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "GET /health HTTP/1.1" 404
2026-06-23 19:22:45 | e0702c174d7c465c | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:45 | e0702c174d7c465c | services.base_client         | INFO     | HTTP POST /registry/documents/check-uniqueness -> 200 (0.014s)
2026-06-23 19:22:45 | e0702c174d7c465c | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:45 | e0702c174d7c465c | services.base_client         | INFO     | HTTP POST /registry/drafts -> 201 (0.012s)
2026-06-23 19:22:45 | e0702c174d7c465c | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-23 19:22:45 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "POST /api/v1/drafts/ HTTP/1.1" 202
2026-06-23 19:22:45 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "GET /api/v1/tasks/12/status HTTP/1.1" 200
2026-06-23 19:22:45 | 270ab53cc9d344e8 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:45 | 270ab53cc9d344e8 | services.base_client         | INFO     | HTTP GET /registry/drafts/11 -> 200 (0.007s)
2026-06-23 19:22:45 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "GET /api/v1/drafts/11 HTTP/1.1" 200
2026-06-23 19:22:46 | 48d318d05a4b43c2 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:46 | 48d318d05a4b43c2 | services.base_client         | INFO     | HTTP PATCH /registry/drafts/11/metadata -> 200 (0.012s)
2026-06-23 19:22:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "PATCH /api/v1/drafts/11/metadata HTTP/1.1" 200
2026-06-23 19:22:46 | 164922cedeb04739 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-23 19:22:46 | 164922cedeb04739 | services.base_client         | INFO     | HTTP GET /registry/drafts/11 -> 200 (0.008s)
2026-06-23 19:22:46 | -                | uvicorn.access               | INFO     | 172.19.0.1:37830 - "GET /api/v1/drafts/11 HTTP/1.1" 200
2026-06-23 19:22:46 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

{"timestamp": "2026-06-23 19:22:26,436", "severity": "INFO", "name": "app.core.validator", "message": "Validation passed, MIME=application/pdf"}
{"timestamp": "2026-06-23 19:22:26,438", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Parsing PDF for task 20002, options={}"}
Jun 23, 2026 7:22:26 PM org.opendataloader.pdf.processors.DocumentProcessor preprocessing
INFO: File name: /tmp/tmpzwg3rutg.pdf
Jun 23, 2026 7:22:26 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11901 in stream 39 0 obj)
Jun 23, 2026 7:22:26 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16578 in stream 47 0 obj)
Jun 23, 2026 7:22:26 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16513 in stream 55 0 obj)
Jun 23, 2026 7:22:26 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 23, 2026 7:22:26 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 23, 2026 7:22:26 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 23, 2026 7:22:26 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 23, 2026 7:22:26 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 23, 2026 7:22:26 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 23, 2026 7:22:26 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 23, 2026 7:22:26 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
Jun 23, 2026 7:22:27 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmp0irevcj2/tmpzwg3rutg.json
Jun 23, 2026 7:22:27 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmp0irevcj2/tmpzwg3rutg.md
Jun 23, 2026 7:22:27 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmp0irevcj2/tmpzwg3rutg.html
{"timestamp": "2026-06-23 19:22:27,924", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-23 19:22:27,925", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-23 19:22:28,021", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-23 19:22:28,107", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-23 19:22:28,192", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-23 19:22:28,279", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-23 19:22:28,349", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:28,365", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-23 19:22:28,413", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 0.91s."}
{"timestamp": "2026-06-23 19:22:28,454", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-23 19:22:28,459", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-23 19:22:28,459", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-23 19:22:28,459", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-23 19:22:35,815", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:37,754", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.20s."}
{"timestamp": "2026-06-23 19:22:40,816", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 1.09s."}
{"timestamp": "2026-06-23 19:22:45,865", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:46,866", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.05s."}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-23 19:22:01,025", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"5bbc4510-15e8-43a6-9019-06fd22e756ba\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/2/messages/last\", \"status\": 200, \"duration_ms\": 13}"}
{"timestamp": "2026-06-23 19:22:01,036", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"b5dbf179-6c4a-4ab4-abc5-f05c7e0a19f9\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/2/messages\", \"status\": 200, \"duration_ms\": 7}"}
{"timestamp": "2026-06-23 19:22:01,050", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"e4be3e1e-cd20-42b9-b9a4-2180b1079614\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/2/messages/4\", \"status\": 200, \"duration_ms\": 9}"}
{"timestamp": "2026-06-23 19:22:01,064", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"e81ee928-6d5b-4e4b-be83-c7e67c2a3049\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/2/messages/search\", \"status\": 200, \"duration_ms\": 9}"}
{"timestamp": "2026-06-23 19:22:01,072", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"83f8bd01-3295-4bbb-a280-8250f65e81b7\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/2/context\", \"status\": 200, \"duration_ms\": 3}"}
{"timestamp": "2026-06-23 19:22:01,088", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"7ea11bdc-fd4e-460d-9f96-abf2b89d33dd\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/2/export\", \"status\": 200, \"duration_ms\": 10}"}
{"timestamp": "2026-06-23 19:22:01,105", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"3bb402c0-a4c1-422e-9e2d-f3f76711286e\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/feedback\", \"status\": 200, \"duration_ms\": 12}"}
{"timestamp": "2026-06-23 19:22:01,136", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"87e8c382-dcd0-49bc-b966-97bc31e52179\", \"user_id\": null, \"draft_id\": null, \"method\": \"DELETE\", \"path\": \"/api/v1/chat/sessions/2\", \"status\": 200, \"duration_ms\": 27}"}
{"timestamp": "2026-06-23 19:22:01,153", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"c4bc2858-f82c-4646-82d5-cc1f57ab49ca\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history\", \"status\": 200, \"duration_ms\": 13}"}
{"timestamp": "2026-06-23 19:22:01,164", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"ab92d0da-3317-4164-9554-77a6291efe79\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history/export\", \"status\": 200, \"duration_ms\": 4}"}
{"timestamp": "2026-06-23 19:22:01,181", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline finished", "message_id": 2, "chunks": 2}
{"timestamp": "2026-06-23 19:22:01,182", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"9214e7eb-032c-4483-bf03-5e2571904b64\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 10}"}
{"timestamp": "2026-06-23 19:22:01,189", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"b36dae1d-c0b9-4fe9-b9f0-dd4503fa0ba3\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/ask\", \"status\": 200, \"duration_ms\": 2}"}
{"timestamp": "2026-06-23 19:22:01,206", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"114443a6-cdc2-4718-8e2f-0bbfb1bb75da\", \"user_id\": null, \"draft_id\": null, \"method\": \"DELETE\", \"path\": \"/api/v1/chat/projects/2\", \"status\": 204, \"duration_ms\": 13}"}
{"timestamp": "2026-06-23 19:22:01,332", "severity": "WARNING", "name": "app.services.pipeline", "message": "pipeline: message deleted before finish, skipping sources", "message_id": 4}
{"timestamp": "2026-06-23 19:22:03,531", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"25574122-bd3e-448d-9113-db21a8620dd8\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/health\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-23 19:22:03,543", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"37a0078b-82ab-474f-a887-e3b52990ccaf\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 9}"}
{"timestamp": "2026-06-23 19:22:04,277", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"61bbd97c-e3ae-47b6-94c1-0a3a6e59991b\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 6}"}
{"timestamp": "2026-06-23 19:22:04,289", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"daad0260-79a3-4d3b-8d08-1dd638b35757\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/3/messages\", \"status\": 202, \"duration_ms\": 8}"}
{"timestamp": "2026-06-23 19:22:04,289", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline started", "message_id": 6, "session_id": 3}
{"timestamp": "2026-06-23 19:22:04,297", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"d05bea5d-867e-4878-8d1d-11f51872bb5d\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/3/messages\", \"status\": 200, \"duration_ms\": 5}"}
{"timestamp": "2026-06-23 19:22:04,615", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline finished", "message_id": 6, "chunks": 2}
{"timestamp": "2026-06-23 19:22:05,508", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"7971ddf1-a3e2-4290-b34f-392a90e45750\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/health\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-23 19:22:05,520", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"953c6e76-1611-47df-a5fb-7844fc8e3bfa\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 6}"}
{"timestamp": "2026-06-23 19:22:05,588", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:05,588", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.06s."}
{"timestamp": "2026-06-23 19:22:05,764", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"69494c09-e413-493d-925f-97305c11e52b\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 6}"}
{"timestamp": "2026-06-23 19:22:05,777", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"22e84100-7474-4bae-9528-a65bdd8e71a3\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/4/messages\", \"status\": 202, \"duration_ms\": 10}"}
{"timestamp": "2026-06-23 19:22:05,778", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline started", "message_id": 8, "session_id": 4}
{"timestamp": "2026-06-23 19:22:05,781", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"160b67ee-6408-4a1e-8b84-224e7e83d741\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-23 19:22:05,786", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"ee6bd0a8-4497-4d2f-8b07-7500b7b8adf6\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-23 19:22:06,111", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline finished", "message_id": 8, "chunks": 2}
{"timestamp": "2026-06-23 19:22:07,724", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:08,511", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.84s."}
{"timestamp": "2026-06-23 19:22:08,726", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:08,726", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.14s."}
{"timestamp": "2026-06-23 19:22:14,257", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:18,501", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:18,502", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.97s."}
{"timestamp": "2026-06-23 19:22:19,257", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:19,258", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.85s."}
{"timestamp": "2026-06-23 19:22:21,337", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 2.35s."}
{"timestamp": "2026-06-23 19:22:27,082", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:28,083", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:28,083", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.85s."}
{"timestamp": "2026-06-23 19:22:37,034", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-23 19:22:38,035", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-23 19:22:38,035", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.87s."}
{"timestamp": "2026-06-23 19:22:40,753", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 2.28s."}
{"timestamp": "2026-06-23 19:22:47,389", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}

```
