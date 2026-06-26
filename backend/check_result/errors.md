# Supervisor Logs

**Generated:** 2026-06-26T10:05:31.961088+00:00


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

{"timestamp": "2026-06-26 13:04:48,496", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 1 for user: pipeline-user-20260626150447484912@test.com"}
{"timestamp": "2026-06-26 13:04:48,726", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 2 for user: pipeline-user-20260626150447484912@test.com"}
{"timestamp": "2026-06-26 13:04:48,961", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 3 for user: pipeline-user-20260626150447484912@test.com"}
{"timestamp": "2026-06-26 13:04:49,190", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 4 for user: pipeline-user-20260626150447484912@test.com"}
{"timestamp": "2026-06-26 13:04:49,422", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 5 for user: pipeline-user-20260626150447484912@test.com"}
{"timestamp": "2026-06-26 13:04:49,570", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:04:49,655", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login attempt 6 for user: pipeline-user-20260626150447484912@test.com"}
{"timestamp": "2026-06-26 13:04:49,692", "severity": "INFO", "name": "app.services.user_service", "message": "User updated: u-d43b8800a3e9"}
{"timestamp": "2026-06-26 13:04:49,709", "severity": "WARNING", "name": "app.services.auth_service", "message": "Failed login for unknown or inactive user: pipeline-user-20260626150447484912@test.com"}
{"timestamp": "2026-06-26 13:04:49,965", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:04:50,413", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:04:50,573", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:04:50,573", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 13:04:50,891", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:04:55,224", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:04:55,591", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 3.47s."}
{"timestamp": "2026-06-26 13:04:58,972", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:04:59,063", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:00,064", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:00,065", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.11s."}
{"timestamp": "2026-06-26 13:05:00,231", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:00,231", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 13:05:08,322", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:09,323", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:09,323", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-26 13:05:09,460", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:14,029", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:14,030", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.02s."}
{"timestamp": "2026-06-26 13:05:18,099", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:19,100", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:19,101", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.16s."}
{"timestamp": "2026-06-26 13:05:22,107", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 2.08s."}
{"timestamp": "2026-06-26 13:05:23,391", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:24,192", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 4.23s."}
{"timestamp": "2026-06-26 13:05:25,085", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:25,404", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:25,757", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:26,033", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:26,354", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:26,947", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:27,270", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:27,591", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:27,960", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 13:05:28,397", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:28,397", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.08s."}
{"timestamp": "2026-06-26 13:05:28,425", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:29,427", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:29,427", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.90s."}
{"timestamp": "2026-06-26 13:05:30,791", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:30,791", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 0.92s."}

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

{"timestamp": "2026-06-26 13:04:40,620", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 4.26s."}
{"timestamp": "2026-06-26 13:04:43,780", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:04:45,878", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.02s."}
{"timestamp": "2026-06-26 13:04:52,527", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:04:53,528", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.97s."}
{"timestamp": "2026-06-26 13:05:00,935", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:01,936", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.20s."}
{"timestamp": "2026-06-26 13:05:09,849", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:10,850", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.01s."}
{"timestamp": "2026-06-26 13:05:17,097", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:18,098", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
{"timestamp": "2026-06-26 13:05:20,740", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 4.05s."}
{"timestamp": "2026-06-26 13:05:24,793", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:25,795", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.98s."}
{"timestamp": "2026-06-26 13:05:32,343", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-26 13:05:25 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /api/v1/documents/10/versions HTTP/1.1" 404
2026-06-26 13:05:25 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /health HTTP/1.1" 404
2026-06-26 13:05:26 | 90663769800d4063 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:26 | 90663769800d4063 | services.base_client         | ERROR    | HTTP error: POST /registry/documents/check-uniqueness -> 404 (0.003s, retries exhausted)
2026-06-26 13:05:26 | 90663769800d4063 | app.api.v1.endpoints.drafts  | WARNING  | Uniqueness check failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/documents/check-uniqueness'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 13:05:26 | 90663769800d4063 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:26 | 90663769800d4063 | services.base_client         | ERROR    | HTTP error: POST /registry/drafts -> 404 (0.003s, retries exhausted)
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "POST /api/v1/drafts/ HTTP/1.1" 500
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /health HTTP/1.1" 404
2026-06-26 13:05:26 | 4a1adb320d2b4838 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:26 | 4a1adb320d2b4838 | services.base_client         | ERROR    | HTTP error: POST /registry/documents/check-uniqueness -> 404 (0.002s, retries exhausted)
2026-06-26 13:05:26 | 4a1adb320d2b4838 | app.api.v1.endpoints.drafts  | WARNING  | Uniqueness check failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/documents/check-uniqueness'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 13:05:26 | 4a1adb320d2b4838 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:26 | 4a1adb320d2b4838 | services.base_client         | ERROR    | HTTP error: POST /registry/drafts -> 404 (0.004s, retries exhausted)
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "POST /api/v1/drafts/ HTTP/1.1" 500
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /api/v1/tasks/%7Btask_id%7D/status HTTP/1.1" 422
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /api/v1/drafts/%7Bdraft_id%7D HTTP/1.1" 422
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "POST /api/v1/drafts/%7Bdraft_id%7D/preview HTTP/1.1" 422
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /api/v1/drafts/%7Bdraft_id%7D/preview/status?longpoll=1 HTTP/1.1" 422
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "PATCH /api/v1/drafts/%7Bdraft_id%7D/decide HTTP/1.1" 422
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /api/v1/drafts/%7Bdraft_id%7D HTTP/1.1" 422
2026-06-26 13:05:26 | 7c46f6b0d58f4b45 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:26 | 7c46f6b0d58f4b45 | services.base_client         | ERROR    | HTTP error: POST /registry/documents/check-uniqueness -> 404 (0.003s, retries exhausted)
2026-06-26 13:05:26 | 7c46f6b0d58f4b45 | app.api.v1.endpoints.drafts  | WARNING  | Uniqueness check failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/documents/check-uniqueness'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 13:05:26 | 7c46f6b0d58f4b45 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:26 | 7c46f6b0d58f4b45 | services.base_client         | ERROR    | HTTP error: POST /registry/drafts -> 404 (0.003s, retries exhausted)
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "POST /api/v1/drafts/ HTTP/1.1" 500
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /api/v1/tasks/%7Btask_id_2%7D/status HTTP/1.1" 422
2026-06-26 13:05:26 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /health HTTP/1.1" 404
2026-06-26 13:05:26 | 1abc9fc482844dab | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:27 | 1abc9fc482844dab | services.base_client         | ERROR    | HTTP error: POST /registry/documents/check-uniqueness -> 404 (0.003s, retries exhausted)
2026-06-26 13:05:27 | 1abc9fc482844dab | app.api.v1.endpoints.drafts  | WARNING  | Uniqueness check failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/documents/check-uniqueness'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 13:05:27 | 1abc9fc482844dab | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:27 | 1abc9fc482844dab | services.base_client         | ERROR    | HTTP error: POST /registry/drafts -> 404 (0.002s, retries exhausted)
2026-06-26 13:05:27 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "POST /api/v1/drafts/ HTTP/1.1" 500
2026-06-26 13:05:27 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "GET /health HTTP/1.1" 404
2026-06-26 13:05:27 | b1585518999f44ca | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:27 | b1585518999f44ca | services.base_client         | ERROR    | HTTP error: POST /registry/documents/check-uniqueness -> 404 (0.003s, retries exhausted)
2026-06-26 13:05:27 | b1585518999f44ca | app.api.v1.endpoints.drafts  | WARNING  | Uniqueness check failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/documents/check-uniqueness'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 13:05:27 | b1585518999f44ca | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 13:05:27 | b1585518999f44ca | services.base_client         | ERROR    | HTTP error: POST /registry/drafts -> 404 (0.003s, retries exhausted)
2026-06-26 13:05:27 | -                | uvicorn.access               | INFO     | 172.18.0.1:54506 - "POST /api/v1/drafts/ HTTP/1.1" 500
2026-06-26 13:05:29 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 0.90s.
2026-06-26 13:05:30 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 1.90s.
2026-06-26 13:05:32 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 3.76s.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11901 in stream 39 0 obj)
Jun 26, 2026 1:05:14 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16578 in stream 47 0 obj)
Jun 26, 2026 1:05:14 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16513 in stream 55 0 obj)
Jun 26, 2026 1:05:14 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 26, 2026 1:05:14 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 26, 2026 1:05:14 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 26, 2026 1:05:14 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 26, 2026 1:05:14 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 26, 2026 1:05:14 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 26, 2026 1:05:14 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 26, 2026 1:05:14 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
{"timestamp": "2026-06-26 13:05:15,380", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
Jun 26, 2026 1:05:15 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmpqf1nzyv0/tmpfafwsl0_.json
Jun 26, 2026 1:05:15 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmpqf1nzyv0/tmpfafwsl0_.md
Jun 26, 2026 1:05:15 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmpqf1nzyv0/tmpfafwsl0_.html
{"timestamp": "2026-06-26 13:05:15,622", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-26 13:05:15,623", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-26 13:05:15,779", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 2.24s."}
{"timestamp": "2026-06-26 13:05:16,063", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Task 20002 not completed yet, returning 409"}
{"timestamp": "2026-06-26 13:05:16,092", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-26 13:05:16,093", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-26 13:05:16,095", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-26 13:05:16,099", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-26 13:05:16,100", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-26 13:05:16,101", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-26 13:05:16,102", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Uploaded 6/6 images for task 20002 (errors: 0)"}
{"timestamp": "2026-06-26 13:05:16,106", "severity": "INFO", "name": "app.services.result_builder", "message": "Result built for task 20002, mode=full"}
{"timestamp": "2026-06-26 13:05:16,106", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-26 13:05:16,106", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-26 13:05:16,106", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-26 13:05:18,087", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Result for task 20002 returned successfully"}
{"timestamp": "2026-06-26 13:05:22,503", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:23,629", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.83s."}
{"timestamp": "2026-06-26 13:05:30,957", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:31,959", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.18s."}
{"timestamp": "2026-06-26 13:05:32,791", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:33,138", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.77s."}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-26 13:04:45,713", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"ceafed99-0281-4a7c-a1d1-a86b404a77e0\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 8}"}
{"timestamp": "2026-06-26 13:04:45,839", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:04:45,839", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.13s."}
{"timestamp": "2026-06-26 13:04:46,850", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"44c4f8b2-4817-474e-97ed-e360fc71aa2e\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 9}"}
{"timestamp": "2026-06-26 13:04:46,865", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"1a4b4ef3-b6dc-4e24-91da-1ae6055f2233\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions\", \"status\": 200, \"duration_ms\": 5}"}
{"timestamp": "2026-06-26 13:04:46,878", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"0f1eaae7-ee1a-4466-8e17-b3fd20219166\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/4\", \"status\": 200, \"duration_ms\": 2}"}
{"timestamp": "2026-06-26 13:04:46,904", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"8f472435-68ae-4f8e-af87-2997c570b33b\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/4/messages\", \"status\": 202, \"duration_ms\": 17}"}
{"timestamp": "2026-06-26 13:04:46,904", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline started", "message_id": 6, "session_id": 4}
{"timestamp": "2026-06-26 13:04:46,924", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"062217de-e785-4cf8-993f-1d9c53457cee\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/4/messages\", \"status\": 200, \"duration_ms\": 7}"}
{"timestamp": "2026-06-26 13:04:46,948", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"aa9487bd-86a5-4bb6-ae69-a077ce19fe09\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/4/messages/search\", \"status\": 200, \"duration_ms\": 8}"}
{"timestamp": "2026-06-26 13:04:46,980", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"610bddd5-51d9-4889-816c-4302b7b39eba\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history\", \"status\": 200, \"duration_ms\": 19}"}
{"timestamp": "2026-06-26 13:04:46,992", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"37ed2280-6ab4-42f6-a590-373e1c8e94a3\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/history/export\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-26 13:04:47,006", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"ca542fe2-82d5-4d2a-a37e-fbe5ca4e60d2\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-26 13:04:47,240", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline finished", "message_id": 6, "chunks": 2}
{"timestamp": "2026-06-26 13:04:47,469", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"9168e45c-e3bf-4821-86e8-065475325dad\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/health\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-26 13:04:47,483", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"54ccaec6-3477-4c64-a1e6-ae7171cd673f\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 11}"}
{"timestamp": "2026-06-26 13:04:48,243", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"23d03d24-b40b-4ee4-a229-bc3fd257befd\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 7}"}
{"timestamp": "2026-06-26 13:04:48,257", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"d32dcc55-1ae7-4452-8ebb-d6fcf9d5030d\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/5/messages\", \"status\": 202, \"duration_ms\": 9}"}
{"timestamp": "2026-06-26 13:04:48,257", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline started", "message_id": 8, "session_id": 5}
{"timestamp": "2026-06-26 13:04:48,264", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"80262973-2a80-4e4d-ab33-457c7730973f\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/api/v1/chat/sessions/5/messages\", \"status\": 200, \"duration_ms\": 4}"}
{"timestamp": "2026-06-26 13:04:48,588", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline finished", "message_id": 8, "chunks": 2}
{"timestamp": "2026-06-26 13:04:49,623", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:04:49,716", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"088f9682-6b2c-4c78-9df4-e2a94d91f931\", \"user_id\": null, \"draft_id\": null, \"method\": \"GET\", \"path\": \"/health\", \"status\": 200, \"duration_ms\": 1}"}
{"timestamp": "2026-06-26 13:04:49,737", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"56d34d0a-e94a-45f0-b17f-001ae5af1a1c\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 9}"}
{"timestamp": "2026-06-26 13:04:49,988", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"f1170eb6-9ecd-4750-a577-b158428c5547\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 6}"}
{"timestamp": "2026-06-26 13:04:50,005", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"7976f9e3-3d05-45c4-b827-486aa70e06e5\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions/6/messages\", \"status\": 202, \"duration_ms\": 10}"}
{"timestamp": "2026-06-26 13:04:50,006", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline started", "message_id": 10, "session_id": 6}
{"timestamp": "2026-06-26 13:04:50,011", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"963361c4-8700-462c-80d1-e8964ef55101\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-26 13:04:50,015", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"97f6534c-adc3-4871-ba41-f7428b2b2e9b\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/text/search\", \"status\": 200, \"duration_ms\": 0}"}
{"timestamp": "2026-06-26 13:04:50,338", "severity": "INFO", "name": "app.services.pipeline", "message": "pipeline finished", "message_id": 10, "chunks": 2}
{"timestamp": "2026-06-26 13:04:50,627", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:04:50,628", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-26 13:04:55,652", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:00,658", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:00,659", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.17s."}
{"timestamp": "2026-06-26 13:05:00,745", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:00,745", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.92s."}
{"timestamp": "2026-06-26 13:05:09,200", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:11,023", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:11,024", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.84s."}
{"timestamp": "2026-06-26 13:05:19,751", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:20,752", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:20,752", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.96s."}
{"timestamp": "2026-06-26 13:05:30,302", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 13:05:30,742", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:30,742", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 0.80s."}
{"timestamp": "2026-06-26 13:05:31,302", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 13:05:31,303", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.07s."}
{"timestamp": "2026-06-26 13:05:31,934", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"702e13f8-e6c2-49a7-9aaa-8ab7f4935124\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 8}"}
{"timestamp": "2026-06-26 13:05:31,953", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"acc6f987-8af7-4498-8ac5-68b22c02f5d8\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 9}"}

```
