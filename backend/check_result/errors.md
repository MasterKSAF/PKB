# Supervisor Logs

**Generated:** 2026-06-27T13:18:06.416258+00:00


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
- [ℹ️ INFO — rag_search.err](#rag_search-err)
- [ℹ️ INFO — rag_search.log](#rag_search-log)
- [ℹ️ INFO — registry.err](#registry-err)
- [ℹ️ INFO — registry.log](#registry-log)


---

## ℹ️ Info-логи

_17 файл(ов) без ошибок (пропущены): auth.err, converter_validator.err, converter_validator.log, gateway.err, gateway.log, integration.err, integration.log, ocr.err, orchestrator.err, parser.err, query.err, rag_builder.err, rag_builder.log, rag_search.err, rag_search.log, registry.err, registry.log_


## ❌ Error-логи


### auth-log

**❌ ERROR** — `/var/log/supervisor/auth.log`


```

{"timestamp": "2026-06-27 16:17:28,753", "severity": "INFO", "name": "app.services.user_service", "message": "User created: test@test.com"}
{"timestamp": "2026-06-27 16:17:28,798", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-704e7b333bea"}
{"timestamp": "2026-06-27 16:17:28,827", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-704e7b333bea"}
{"timestamp": "2026-06-27 16:17:28,855", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-704e7b333bea"}
{"timestamp": "2026-06-27 16:17:28,892", "severity": "INFO", "name": "app.services.user_service", "message": "Role created: viewer"}
{"timestamp": "2026-06-27 16:17:31,110", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:31,111", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.85s."}
{"timestamp": "2026-06-27 16:17:31,703", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 16:17:32,521", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:33,526", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:33,526", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.85s."}
{"timestamp": "2026-06-27 16:17:34,974", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 16:17:35,823", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:36,161", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 16:17:36,229", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.78s."}
{"timestamp": "2026-06-27 16:17:36,762", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 16:17:37,020", "severity": "INFO", "name": "app.services.user_service", "message": "User created: gateway-prepare@test.com"}
{"timestamp": "2026-06-27 16:17:37,981", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 16:17:38,015", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:38,099", "severity": "INFO", "name": "app.services.auth_service", "message": "Refresh token revoked for user: u-c63101514b42"}
{"timestamp": "2026-06-27 16:17:38,166", "severity": "WARNING", "name": "app.services.user_service", "message": "Attempt to create duplicate user: test@test.com"}
{"timestamp": "2026-06-27 16:17:38,228", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-1e406c763960"}
{"timestamp": "2026-06-27 16:17:38,270", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-1e406c763960"}
{"timestamp": "2026-06-27 16:17:38,328", "severity": "WARNING", "name": "app.services.user_service", "message": "Attempt to create duplicate role: viewer"}
{"timestamp": "2026-06-27 16:17:39,017", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:39,018", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.87s."}
{"timestamp": "2026-06-27 16:17:40,841", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:40,842", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.02s."}
{"timestamp": "2026-06-27 16:17:41,775", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:42,776", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:42,777", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.02s."}
{"timestamp": "2026-06-27 16:17:43,741", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:45,656", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.94s."}
{"timestamp": "2026-06-27 16:17:47,593", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:48,594", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:48,594", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.94s."}
{"timestamp": "2026-06-27 16:17:48,746", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:48,747", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-27 16:17:53,198", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:54,198", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:54,199", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.12s."}
{"timestamp": "2026-06-27 16:17:57,189", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:58,190", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:58,190", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-27 16:18:00,942", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.67s."}
{"timestamp": "2026-06-27 16:18:02,614", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:18:03,615", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:18:03,615", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.13s."}
{"timestamp": "2026-06-27 16:18:06,360", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 16:18:06,610", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-27 16:17:28,161", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.09s."}
{"timestamp": "2026-06-27 16:17:31,374", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:32,376", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.90s."}
{"timestamp": "2026-06-27 16:17:35,341", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:36,342", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.95s."}
{"timestamp": "2026-06-27 16:17:39,405", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:40,407", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.11s."}
{"timestamp": "2026-06-27 16:17:43,820", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:44,821", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.95s."}
{"timestamp": "2026-06-27 16:17:45,824", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:48,867", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.95s."}
{"timestamp": "2026-06-27 16:17:52,002", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:53,004", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.19s."}
{"timestamp": "2026-06-27 16:17:56,161", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:57,162", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.92s."}
{"timestamp": "2026-06-27 16:18:00,009", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:18:01,010", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.19s."}
{"timestamp": "2026-06-27 16:18:03,968", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:18:04,969", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.82s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents/check-uniqueness -> 200 (0.012s)
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.014s)
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-27 16:17:37 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | orchestrator.pipeline        | INFO     | Approving draft
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/6 -> 200 (0.008s)
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/6/preview -> 200 (0.012s)
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents -> 201 (0.017s)
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | services.base_client         | ERROR    | HTTP error: POST /api/v1/registry/drafts/6/snapshot -> 404 (0.005s, retries exhausted)
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | orchestrator.pipeline        | WARNING  | Failed to save preview snapshot: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/6/snapshot'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-27 16:17:37 | c416677b-3ffe-4dde-a7ad-37d741e9f667 | orchestrator.pipeline        | INFO     | Enqueued full OCR step
2026-06-27 16:17:37 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "PATCH /api/v1/drafts/6/decide HTTP/1.1" 200
2026-06-27 16:17:37 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/system/health HTTP/1.1" 200
2026-06-27 16:17:39 | d945d373-ace6-4c1f-b20a-db2a3d1697ef | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:39 | d945d373-ace6-4c1f-b20a-db2a3d1697ef | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/6 -> 200 (0.012s)
2026-06-27 16:17:39 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/drafts/6 HTTP/1.1" 200
2026-06-27 16:17:39 | de88b922-fcc4-49da-8dcb-078773185862 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:39 | de88b922-fcc4-49da-8dcb-078773185862 | services.base_client         | INFO     | HTTP DELETE /api/v1/registry/drafts/6 -> 200 (0.016s)
2026-06-27 16:17:39 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "DELETE /api/v1/drafts/6 HTTP/1.1" 204
2026-06-27 16:17:39 | 5e4bd37e-c59d-4423-9e60-f54caedd1d6b | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:39 | 5e4bd37e-c59d-4423-9e60-f54caedd1d6b | services.base_client         | ERROR    | HTTP error: GET /api/v1/registry/drafts/6 -> 404 (0.012s, retries exhausted)
2026-06-27 16:17:39 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "POST /api/v1/drafts/6/preview HTTP/1.1" 404
2026-06-27 16:17:39 | b6772886-9b98-447d-8964-5d1f09bc5fb6 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:39 | b6772886-9b98-447d-8964-5d1f09bc5fb6 | services.base_client         | ERROR    | HTTP error: GET /api/v1/registry/drafts/6 -> 404 (0.010s, retries exhausted)
2026-06-27 16:17:39 | b6772886-9b98-447d-8964-5d1f09bc5fb6 | app.api.v1.endpoints.drafts  | WARNING  | Registry check failed for draft 6: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/6'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-27 16:17:41 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.
2026-06-27 16:17:44 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/drafts/6/preview/status?longpoll=5 HTTP/1.1" 200
2026-06-27 16:17:44 | 70322ccd-e5e0-49d8-aa08-de0155f8392e | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 16:17:45 | 70322ccd-e5e0-49d8-aa08-de0155f8392e | services.base_client         | ERROR    | HTTP error: PATCH /api/v1/registry/drafts/6/metadata -> 404 (0.012s, retries exhausted)
2026-06-27 16:17:45 | 70322ccd-e5e0-49d8-aa08-de0155f8392e | app.api.v1.endpoints.drafts  | WARNING  | Registry 404 on metadata update for draft 6 (expected)
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "PATCH /api/v1/drafts/6/metadata HTTP/1.1" 404
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/drafts/6/tasks HTTP/1.1" 200
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/tasks/6/status HTTP/1.1" 200
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/tasks/6/steps HTTP/1.1" 200
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/documents/queue HTTP/1.1" 200
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/documents/5/status?longpoll=5 HTTP/1.1" 404
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/documents/5/errors?page=1&page_size=10 HTTP/1.1" 404
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "POST /api/v1/documents/5/reprocess HTTP/1.1" 409
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "POST /api/v1/documents/5/versions HTTP/1.1" 404
2026-06-27 16:17:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:47292 - "GET /api/v1/documents/5/tasks HTTP/1.1" 200
2026-06-27 16:17:46 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 1.10s.
2026-06-27 16:17:47 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 2.33s.
2026-06-27 16:17:49 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 4.10s.
2026-06-27 16:17:53 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

Jun 27, 2026 4:17:32 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 27, 2026 4:17:32 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 27, 2026 4:17:32 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 27, 2026 4:17:32 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 27, 2026 4:17:32 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 27, 2026 4:17:32 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 27, 2026 4:17:32 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
{"timestamp": "2026-06-27 16:17:33,076", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.06s."}
Jun 27, 2026 4:17:34 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmp88zrzirx/tmpqvdmswbk.json
Jun 27, 2026 4:17:34 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmp88zrzirx/tmpqvdmswbk.md
Jun 27, 2026 4:17:34 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmp88zrzirx/tmpqvdmswbk.html
{"timestamp": "2026-06-27 16:17:34,622", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 12345"}
{"timestamp": "2026-06-27 16:17:34,623", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-27 16:17:35,288", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-27 16:17:35,296", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-27 16:17:35,297", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-27 16:17:35,298", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-27 16:17:35,299", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-27 16:17:35,300", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-27 16:17:35,300", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Uploaded 6/6 images for task 12345 (errors: 0)"}
{"timestamp": "2026-06-27 16:17:35,305", "severity": "INFO", "name": "app.services.result_builder", "message": "Result built for task 12345, mode=full"}
{"timestamp": "2026-06-27 16:17:35,307", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 12345"}
{"timestamp": "2026-06-27 16:17:35,307", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 12345"}
{"timestamp": "2026-06-27 16:17:35,307", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline completed for task 12345"}
{"timestamp": "2026-06-27 16:17:36,063", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:37,488", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.84s."}
{"timestamp": "2026-06-27 16:17:40,579", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:41,064", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 1.08s."}
{"timestamp": "2026-06-27 16:17:44,081", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:45,746", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.10s."}
{"timestamp": "2026-06-27 16:17:48,956", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:49,957", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.91s."}
{"timestamp": "2026-06-27 16:17:52,482", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:53,483", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.19s."}
{"timestamp": "2026-06-27 16:17:56,605", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:57,605", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}
{"timestamp": "2026-06-27 16:18:00,893", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:18:01,894", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.98s."}
{"timestamp": "2026-06-27 16:18:04,817", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:18:05,818", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.89s."}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-27 16:17:45,557", "severity": "DEBUG", "name": "httpcore.http11", "message": "response_closed.started"}
{"timestamp": "2026-06-27 16:17:45,557", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.07s."}
{"timestamp": "2026-06-27 16:17:45,558", "severity": "DEBUG", "name": "httpcore.http11", "message": "response_closed.complete"}
{"timestamp": "2026-06-27 16:17:45,558", "severity": "DEBUG", "name": "httpcore.connection", "message": "close.started"}
{"timestamp": "2026-06-27 16:17:45,559", "severity": "DEBUG", "name": "httpcore.connection", "message": "close.complete"}
{"timestamp": "2026-06-27 16:17:45,560", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"05faf48f-134e-4a06-87a0-61260c534d81\", \"user_id\": \"u-c63101514b42\", \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/4/messages/search\", \"status\": 200, \"duration_ms\": 14}"}
{"timestamp": "2026-06-27 16:17:45,591", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='127.0.0.1' port=8091 local_address=None timeout=30.0 socket_options=None"}
{"timestamp": "2026-06-27 16:17:45,594", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x7fe8740e7200>"}
{"timestamp": "2026-06-27 16:17:45,594", "severity": "DEBUG", "name": "httpcore.http11", "message": "send_request_headers.started request=<Request [b'POST']>"}
{"timestamp": "2026-06-27 16:17:45,595", "severity": "DEBUG", "name": "httpcore.http11", "message": "send_request_headers.complete"}
{"timestamp": "2026-06-27 16:17:45,595", "severity": "DEBUG", "name": "httpcore.http11", "message": "send_request_body.started request=<Request [b'POST']>"}
{"timestamp": "2026-06-27 16:17:45,595", "severity": "DEBUG", "name": "httpcore.http11", "message": "send_request_body.complete"}
{"timestamp": "2026-06-27 16:17:45,595", "severity": "DEBUG", "name": "httpcore.http11", "message": "receive_response_headers.started request=<Request [b'POST']>"}
{"timestamp": "2026-06-27 16:17:45,616", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"395f96f0-bd9c-4470-a2eb-aa5d7ff721c8\", \"user_id\": \"u-c63101514b42\", \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history\", \"status\": 200, \"duration_ms\": 23}"}
{"timestamp": "2026-06-27 16:17:45,617", "severity": "DEBUG", "name": "httpcore.http11", "message": "receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'date', b'Sat, 27 Jun 2026 13:17:45 GMT'), (b'server', b'uvicorn'), (b'content-length', b'100'), (b'content-type', b'application/json')])"}
{"timestamp": "2026-06-27 16:17:45,618", "severity": "INFO", "name": "httpx", "message": "HTTP Request: POST http://127.0.0.1:8091/api/v1/rag/search \"HTTP/1.1 200 OK\""}
{"timestamp": "2026-06-27 16:17:45,618", "severity": "DEBUG", "name": "httpcore.http11", "message": "receive_response_body.started request=<Request [b'POST']>"}
{"timestamp": "2026-06-27 16:17:45,618", "severity": "DEBUG", "name": "httpcore.http11", "message": "receive_response_body.complete"}
{"timestamp": "2026-06-27 16:17:45,618", "severity": "DEBUG", "name": "httpcore.http11", "message": "response_closed.started"}
{"timestamp": "2026-06-27 16:17:45,618", "severity": "DEBUG", "name": "httpcore.http11", "message": "response_closed.complete"}
{"timestamp": "2026-06-27 16:17:45,618", "severity": "DEBUG", "name": "httpcore.connection", "message": "close.started"}
{"timestamp": "2026-06-27 16:17:45,619", "severity": "DEBUG", "name": "httpcore.connection", "message": "close.complete"}
{"timestamp": "2026-06-27 16:17:45,619", "severity": "INFO", "name": "app.services.pipeline", "message": "no chunks found", "message_id": 6}
{"timestamp": "2026-06-27 16:17:45,631", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"eaebf306-db78-4636-b439-8a2b367b82eb\", \"user_id\": \"u-c63101514b42\", \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history/export\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-27 16:17:45,650", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"a44487bb-8dd1-4f91-a9ef-3eb7d94e93e9\", \"user_id\": \"u-c63101514b42\", \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-27 16:17:46,081", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"8b67a687-ac3a-40a6-8f95-66ff5db33fbe\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/health\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-27 16:17:46,085", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"88195818-289e-49c4-be0f-a44528620e0b\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-27 16:17:46,089", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"59ce028b-8f54-483b-bf93-d08c0bd92ca0\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-27 16:17:46,092", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"b242bcb1-2d5e-414d-8417-547a6dde6e4c\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-27 16:17:46,095", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:46,096", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.01s."}
{"timestamp": "2026-06-27 16:17:46,096", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"de729c8a-53b3-41cb-bddf-d783a38ec945\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 1}"}
{"timestamp": "2026-06-27 16:17:46,099", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"cdf616a3-6508-46e5-98e1-7e8320941dc0\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-27 16:17:46,101", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"42cafe26-d79e-40dd-be06-22fb3354e6e4\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/projects\", \"status\": 401, \"duration_ms\": 0}"}
{"timestamp": "2026-06-27 16:17:50,135", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:51,677", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:51,677", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-27 16:17:54,697", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:17:55,139", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:55,139", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.94s."}
{"timestamp": "2026-06-27 16:17:55,697", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:17:55,698", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.86s."}
{"timestamp": "2026-06-27 16:18:00,008", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:18:01,429", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:18:01,429", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.84s."}
{"timestamp": "2026-06-27 16:18:05,869", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 16:18:06,387", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"7d97c5fa-11cd-4c96-bf72-6143f85d6966\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 8}"}
{"timestamp": "2026-06-27 16:18:06,410", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"0adef3a9-dbc8-426b-b511-02a02c511ea8\", \"user_id\": \"u-c63101514b42\", \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 5}"}
{"timestamp": "2026-06-27 16:18:06,870", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 16:18:06,871", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}

```
