# Supervisor Logs

**Generated:** 2026-06-26T16:47:50.736170+00:00


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

{"timestamp": "2026-06-26 19:47:10,511", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:10,511", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.86s."}
{"timestamp": "2026-06-26 19:47:10,745", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:15,247", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:16,249", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:16,250", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-26 19:47:19,295", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:20,297", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:20,297", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.82s."}
{"timestamp": "2026-06-26 19:47:20,409", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:20,409", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-26 19:47:21,351", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:23,424", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:25,988", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:25,989", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.85s."}
{"timestamp": "2026-06-26 19:47:28,425", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:28,426", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-26 19:47:30,471", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:31,197", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 2.11s."}
{"timestamp": "2026-06-26 19:47:31,472", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:31,472", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.09s."}
{"timestamp": "2026-06-26 19:47:33,304", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:34,662", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:35,406", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:35,407", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 19:47:35,470", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:36,110", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:36,478", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:37,276", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:38,138", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:38,138", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 1.04s."}
{"timestamp": "2026-06-26 19:47:38,311", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:38,312", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-26 19:47:39,562", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:40,172", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:41,173", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:41,173", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.98s."}
{"timestamp": "2026-06-26 19:47:41,339", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:44,830", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:45,015", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:45,015", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.96s."}
{"timestamp": "2026-06-26 19:47:45,651", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:46,263", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:46,348", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:46,348", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.99s."}
{"timestamp": "2026-06-26 19:47:49,506", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:50,507", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:50,507", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.12s."}
{"timestamp": "2026-06-26 19:47:50,613", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 19:47:50,972", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}

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

{"timestamp": "2026-06-26 19:46:45,469", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:46:46,470", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 19:46:49,649", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:46:50,650", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.03s."}
{"timestamp": "2026-06-26 19:46:54,066", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:46:55,067", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.82s."}
{"timestamp": "2026-06-26 19:46:58,113", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:46:59,114", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
{"timestamp": "2026-06-26 19:47:02,147", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:03,150", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.04s."}
{"timestamp": "2026-06-26 19:47:06,037", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:07,038", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}
{"timestamp": "2026-06-26 19:47:10,503", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:11,506", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}
{"timestamp": "2026-06-26 19:47:14,157", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:15,159", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.02s."}
{"timestamp": "2026-06-26 19:47:18,052", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:19,053", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.11s."}
{"timestamp": "2026-06-26 19:47:20,164", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 2.11s."}
{"timestamp": "2026-06-26 19:47:22,278", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:23,279", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.12s."}
{"timestamp": "2026-06-26 19:47:26,368", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:27,369", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.97s."}
{"timestamp": "2026-06-26 19:47:30,185", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:31,186", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.13s."}
{"timestamp": "2026-06-26 19:47:34,130", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:35,131", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
{"timestamp": "2026-06-26 19:47:35,526", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:35,997", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.86s."}
{"timestamp": "2026-06-26 19:47:37,857", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:38,858", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.99s."}
{"timestamp": "2026-06-26 19:47:41,961", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:42,964", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.88s."}
{"timestamp": "2026-06-26 19:47:45,899", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:46,900", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.17s."}
{"timestamp": "2026-06-26 19:47:50,266", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:51,267", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.94s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-26 19:47:39 | ecc576b1-4628-49a9-8406-a1d3a343e1be | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:39 | ecc576b1-4628-49a9-8406-a1d3a343e1be | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.015s)
2026-06-26 19:47:39 | ecc576b1-4628-49a9-8406-a1d3a343e1be | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 19:47:39 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-26 19:47:39 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "GET /api/v1/tasks/15/status HTTP/1.1" 200
2026-06-26 19:47:39 | 6a81c1d1-5b95-432b-9169-89a78c6abe16 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:39 | 6a81c1d1-5b95-432b-9169-89a78c6abe16 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/13 -> 200 (0.011s)
2026-06-26 19:47:39 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "GET /api/v1/drafts/13 HTTP/1.1" 200
2026-06-26 19:47:39 | 0d32cec3-4ba7-4d98-91cc-ab1a69f5430b | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:39 | 0d32cec3-4ba7-4d98-91cc-ab1a69f5430b | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/13 -> 200 (0.010s)
2026-06-26 19:47:39 | 0d32cec3-4ba7-4d98-91cc-ab1a69f5430b | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 19:47:39 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "POST /api/v1/drafts/13/preview HTTP/1.1" 202
2026-06-26 19:47:40 | 81014f0d-d688-4506-86e1-cb5713715eee | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:40 | 81014f0d-d688-4506-86e1-cb5713715eee | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/13 -> 200 (0.010s)
2026-06-26 19:47:41 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "GET /api/v1/drafts/13/preview/status?longpoll=1 HTTP/1.1" 200
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | orchestrator.pipeline        | INFO     | Approving draft
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/13 -> 200 (0.010s)
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/13/preview -> 200 (0.008s)
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents -> 201 (0.014s)
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | services.base_client         | ERROR    | HTTP error: POST /api/v1/registry/drafts/13/snapshot -> 404 (0.005s, retries exhausted)
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | orchestrator.pipeline        | WARNING  | Failed to save preview snapshot: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/13/snapshot'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 19:47:41 | ecc576b1-4628-49a9-8406-a1d3a343e1be | orchestrator.pipeline        | INFO     | Enqueued full OCR step
2026-06-26 19:47:41 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "PATCH /api/v1/drafts/13/decide HTTP/1.1" 200
2026-06-26 19:47:41 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 3.70s.
2026-06-26 19:47:44 | 891de460-bc3d-4251-800e-a24c849e2d56 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:44 | 891de460-bc3d-4251-800e-a24c849e2d56 | services.base_client         | INFO     | HTTP DELETE /api/v1/registry/drafts/13 -> 200 (0.014s)
2026-06-26 19:47:44 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "DELETE /api/v1/drafts/13 HTTP/1.1" 204
2026-06-26 19:47:45 | 30650cbb-fa0b-4c84-84a2-26ee343f97e2 | app.storage                  | INFO     | Uploaded to MinIO: bucket=documents key=f-6c149ba59fef size=123616
2026-06-26 19:47:45 | 30650cbb-fa0b-4c84-84a2-26ee343f97e2 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:45 | 30650cbb-fa0b-4c84-84a2-26ee343f97e2 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents/check-uniqueness -> 200 (0.010s)
2026-06-26 19:47:45 | 30650cbb-fa0b-4c84-84a2-26ee343f97e2 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:45 | 30650cbb-fa0b-4c84-84a2-26ee343f97e2 | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.015s)
2026-06-26 19:47:45 | 30650cbb-fa0b-4c84-84a2-26ee343f97e2 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 19:47:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-26 19:47:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "GET /api/v1/tasks/16/status HTTP/1.1" 200
2026-06-26 19:47:45 | e31fe0c4-f926-45fd-b739-74b03699c3f0 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:45 | e31fe0c4-f926-45fd-b739-74b03699c3f0 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/14 -> 200 (0.012s)
2026-06-26 19:47:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "GET /api/v1/drafts/14 HTTP/1.1" 200
2026-06-26 19:47:45 | 85556c21-a73f-4632-b7a2-9ab282737dbd | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:45 | 85556c21-a73f-4632-b7a2-9ab282737dbd | services.base_client         | INFO     | HTTP PATCH /api/v1/registry/drafts/14/metadata -> 200 (0.022s)
2026-06-26 19:47:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "PATCH /api/v1/drafts/14/metadata HTTP/1.1" 200
2026-06-26 19:47:45 | fff9e317-8588-4d75-8e00-d915e1eb13e9 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 19:47:45 | fff9e317-8588-4d75-8e00-d915e1eb13e9 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/14 -> 200 (0.014s)
2026-06-26 19:47:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:34842 - "GET /api/v1/drafts/14 HTTP/1.1" 200
2026-06-26 19:47:45 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.
2026-06-26 19:47:50 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 0.97s.
2026-06-26 19:47:51 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 2.14s.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

Jun 26, 2026 7:47:24 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 26, 2026 7:47:24 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 26, 2026 7:47:24 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 26, 2026 7:47:24 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 26, 2026 7:47:24 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
{"timestamp": "2026-06-26 19:47:24,184", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
Jun 26, 2026 7:47:25 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmpp7nyh6da/tmp92elvdwp.json
Jun 26, 2026 7:47:25 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmpp7nyh6da/tmp92elvdwp.md
Jun 26, 2026 7:47:25 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmpp7nyh6da/tmp92elvdwp.html
{"timestamp": "2026-06-26 19:47:25,271", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-26 19:47:25,272", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-26 19:47:25,666", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Task 20002 not completed yet, returning 409"}
{"timestamp": "2026-06-26 19:47:25,689", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-26 19:47:25,699", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-26 19:47:25,700", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-26 19:47:25,701", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-26 19:47:25,702", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-26 19:47:25,703", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-26 19:47:25,704", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Uploaded 6/6 images for task 20002 (errors: 0)"}
{"timestamp": "2026-06-26 19:47:25,707", "severity": "INFO", "name": "app.services.result_builder", "message": "Result built for task 20002, mode=full"}
{"timestamp": "2026-06-26 19:47:25,708", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-26 19:47:25,708", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-26 19:47:25,708", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-26 19:47:27,443", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:27,689", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Result for task 20002 returned successfully"}
{"timestamp": "2026-06-26 19:47:28,444", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}
{"timestamp": "2026-06-26 19:47:28,884", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:29,408", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.74s."}
{"timestamp": "2026-06-26 19:47:31,148", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:32,149", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.07s."}
{"timestamp": "2026-06-26 19:47:34,972", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:35,973", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 19:47:36,862", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:36,900", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 2.13s."}
{"timestamp": "2026-06-26 19:47:39,031", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:40,032", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.83s."}
{"timestamp": "2026-06-26 19:47:42,971", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:43,973", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 19:47:46,991", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:47,992", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.10s."}
{"timestamp": "2026-06-26 19:47:50,967", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:51,968", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-26 19:47:08,500", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 19:47:08,500", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 19:47:09,308", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 19:47:09,310", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 19:47:10,186", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:10,186", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 19:47:10,344", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 19:47:10,345", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 19:47:10,532", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 19:47:10,533", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 19:47:10,536", "severity": "ERROR", "name": "app.services.pipeline", "message": "llm generation failed after retries", "message_id": 6}
{"timestamp": "2026-06-26 19:47:12,377", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 19:47:12,378", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 19:47:12,382", "severity": "ERROR", "name": "app.services.pipeline", "message": "llm generation failed after retries", "message_id": 8}
{"timestamp": "2026-06-26 19:47:12,875", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:13,326", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:13,326", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.97s."}
{"timestamp": "2026-06-26 19:47:13,876", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:13,876", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.06s."}
{"timestamp": "2026-06-26 19:47:16,175", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:17,783", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:17,783", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 19:47:20,574", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.61s."}
{"timestamp": "2026-06-26 19:47:22,184", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:23,185", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:23,186", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.90s."}
{"timestamp": "2026-06-26 19:47:25,955", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:26,956", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:26,957", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.97s."}
{"timestamp": "2026-06-26 19:47:31,420", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:32,421", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:32,421", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-26 19:47:35,221", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:36,223", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:36,223", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-26 19:47:37,714", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:37,715", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 1.08s."}
{"timestamp": "2026-06-26 19:47:40,665", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:41,891", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:41,891", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.95s."}
{"timestamp": "2026-06-26 19:47:46,346", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:47,347", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:47,347", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.95s."}
{"timestamp": "2026-06-26 19:47:50,159", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 19:47:50,639", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"595700d9-1e15-4f9a-8d14-3e847f457020\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 7}"}
{"timestamp": "2026-06-26 19:47:50,663", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"d24424f4-dadc-420b-8bd9-761dda9705b6\", \"user_id\": \"u-faff87f17afd\", \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 9}"}
{"timestamp": "2026-06-26 19:47:51,160", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:51,161", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.15s."}
{"timestamp": "2026-06-26 19:47:51,177", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 19:47:51,178", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.18s."}

```
