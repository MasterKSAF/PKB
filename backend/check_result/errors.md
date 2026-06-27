# Supervisor Logs

**Generated:** 2026-06-27T15:35:55.092566+00:00


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

{"timestamp": "2026-06-27 18:35:13,147", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:13,148", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.90s."}
{"timestamp": "2026-06-27 18:35:15,461", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:15,462", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 0.83s."}
{"timestamp": "2026-06-27 18:35:16,934", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:17,935", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:17,935", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.19s."}
{"timestamp": "2026-06-27 18:35:18,167", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:19,089", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:20,957", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:21,958", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:21,958", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.96s."}
{"timestamp": "2026-06-27 18:35:22,833", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:22,834", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.01s."}
{"timestamp": "2026-06-27 18:35:26,750", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:27,751", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:27,752", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.88s."}
{"timestamp": "2026-06-27 18:35:32,415", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:32,682", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:32,683", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.01s."}
{"timestamp": "2026-06-27 18:35:33,416", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:33,416", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.93s."}
{"timestamp": "2026-06-27 18:35:34,857", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:35,539", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:35,960", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:36,206", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.84s."}
{"timestamp": "2026-06-27 18:35:37,246", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:37,721", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:38,044", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:39,045", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:39,045", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.01s."}
{"timestamp": "2026-06-27 18:35:39,098", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:40,552", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:40,553", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.09s."}
{"timestamp": "2026-06-27 18:35:43,065", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:43,511", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:44,725", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:44,725", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.16s."}
{"timestamp": "2026-06-27 18:35:48,515", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:48,515", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.81s."}
{"timestamp": "2026-06-27 18:35:48,890", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:49,465", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:49,759", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:50,443", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:50,466", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:50,467", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.13s."}
{"timestamp": "2026-06-27 18:35:53,377", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:53,487", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.71s."}
{"timestamp": "2026-06-27 18:35:55,024", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 18:35:55,194", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-27 18:34:26,601", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.95s."}
{"timestamp": "2026-06-27 18:34:29,575", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:30,580", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.02s."}
{"timestamp": "2026-06-27 18:34:33,685", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:34,687", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.07s."}
{"timestamp": "2026-06-27 18:34:37,536", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:38,537", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.93s."}
{"timestamp": "2026-06-27 18:34:40,706", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 2.39s."}
{"timestamp": "2026-06-27 18:34:41,463", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:42,464", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.91s."}
{"timestamp": "2026-06-27 18:34:43,098", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:43,373", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.78s."}
{"timestamp": "2026-06-27 18:34:45,153", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:46,155", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.13s."}
{"timestamp": "2026-06-27 18:34:48,932", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:49,933", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.89s."}
{"timestamp": "2026-06-27 18:34:52,664", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:53,668", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.07s."}
{"timestamp": "2026-06-27 18:34:56,566", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:57,567", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.98s."}
{"timestamp": "2026-06-27 18:35:00,838", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:01,839", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.09s."}
{"timestamp": "2026-06-27 18:35:05,082", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:06,083", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.87s."}
{"timestamp": "2026-06-27 18:35:08,999", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:09,999", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.92s."}
{"timestamp": "2026-06-27 18:35:13,035", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:14,036", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.01s."}
{"timestamp": "2026-06-27 18:35:14,729", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:15,046", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 2.23s."}
{"timestamp": "2026-06-27 18:35:17,277", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:18,279", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.00s."}
{"timestamp": "2026-06-27 18:35:21,666", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:22,668", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.06s."}
{"timestamp": "2026-06-27 18:35:25,927", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:26,928", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.85s."}
{"timestamp": "2026-06-27 18:35:29,985", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:30,984", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.91s."}
{"timestamp": "2026-06-27 18:35:33,957", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:34,959", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.90s."}
{"timestamp": "2026-06-27 18:35:37,716", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:38,719", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}
{"timestamp": "2026-06-27 18:35:41,566", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:42,568", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}
{"timestamp": "2026-06-27 18:35:45,792", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:46,793", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.16s."}
{"timestamp": "2026-06-27 18:35:50,115", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:51,117", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.88s."}
{"timestamp": "2026-06-27 18:35:54,370", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:55,371", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.17s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-27 18:35:43 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-27 18:35:43 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "GET /api/v1/tasks/16/status HTTP/1.1" 200
2026-06-27 18:35:43 | 6e41a81b-282b-4045-ab3a-5a11b712cfd5 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:43 | 6e41a81b-282b-4045-ab3a-5a11b712cfd5 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/14 -> 200 (0.012s)
2026-06-27 18:35:43 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "GET /api/v1/drafts/14 HTTP/1.1" 200
2026-06-27 18:35:43 | 11848afa-472f-496b-a803-03e2bb53212f | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:43 | 11848afa-472f-496b-a803-03e2bb53212f | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/14 -> 200 (0.013s)
2026-06-27 18:35:43 | 11848afa-472f-496b-a803-03e2bb53212f | orchestrator.pipeline        | INFO     | Parser-first: enqueuing parser preview
2026-06-27 18:35:43 | 11848afa-472f-496b-a803-03e2bb53212f | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-27 18:35:43 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "POST /api/v1/drafts/14/preview HTTP/1.1" 202
2026-06-27 18:35:43 | 2720ef5f-3be1-4b33-8513-fcc2691a6d05 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:43 | 2720ef5f-3be1-4b33-8513-fcc2691a6d05 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/14 -> 200 (0.014s)
2026-06-27 18:35:44 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "GET /api/v1/drafts/14/preview/status?longpoll=1 HTTP/1.1" 200
2026-06-27 18:35:44 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | orchestrator.pipeline        | INFO     | Approving draft
2026-06-27 18:35:44 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:44 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/14 -> 200 (0.008s)
2026-06-27 18:35:44 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/14/preview -> 200 (0.008s)
2026-06-27 18:35:45 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents -> 201 (0.026s)
2026-06-27 18:35:45 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:45 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | services.base_client         | ERROR    | HTTP error: POST /api/v1/registry/drafts/14/snapshot -> 404 (0.006s, retries exhausted)
2026-06-27 18:35:45 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | orchestrator.pipeline        | WARNING  | Failed to save preview snapshot: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/14/snapshot'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-27 18:35:45 | 77d62074-ae89-4d0f-8666-95cfe34d51d1 | orchestrator.pipeline        | INFO     | Enqueued full Parser step (Parser-first)
2026-06-27 18:35:45 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "PATCH /api/v1/drafts/14/decide HTTP/1.1" 200
2026-06-27 18:35:46 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.
2026-06-27 18:35:48 | 9588e5c0-6270-477b-acf4-a8a255ed7e68 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:48 | 9588e5c0-6270-477b-acf4-a8a255ed7e68 | services.base_client         | INFO     | HTTP DELETE /api/v1/registry/drafts/14 -> 200 (0.016s)
2026-06-27 18:35:48 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "DELETE /api/v1/drafts/14 HTTP/1.1" 204
2026-06-27 18:35:48 | -                | uvicorn.access               | INFO     | 172.18.0.1:35512 - "GET /health HTTP/1.1" 404
2026-06-27 18:35:49 | ea3daeeb-da07-46c8-9ec2-4ebe6b94300d | app.storage                  | INFO     | Uploaded to MinIO: bucket=documents key=f-6c149ba59fef size=123616
2026-06-27 18:35:49 | ea3daeeb-da07-46c8-9ec2-4ebe6b94300d | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:49 | ea3daeeb-da07-46c8-9ec2-4ebe6b94300d | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents/check-uniqueness -> 200 (0.015s)
2026-06-27 18:35:49 | ea3daeeb-da07-46c8-9ec2-4ebe6b94300d | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:49 | ea3daeeb-da07-46c8-9ec2-4ebe6b94300d | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.018s)
2026-06-27 18:35:49 | ea3daeeb-da07-46c8-9ec2-4ebe6b94300d | orchestrator.pipeline        | INFO     | Parser-first: enqueuing parser preview
2026-06-27 18:35:49 | ea3daeeb-da07-46c8-9ec2-4ebe6b94300d | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-27 18:35:49 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-27 18:35:49 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "GET /api/v1/tasks/17/status HTTP/1.1" 200
2026-06-27 18:35:49 | dc5542d8-c57b-4e78-8dcf-88864e60d76d | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:49 | dc5542d8-c57b-4e78-8dcf-88864e60d76d | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/15 -> 200 (0.013s)
2026-06-27 18:35:49 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "GET /api/v1/drafts/15 HTTP/1.1" 200
2026-06-27 18:35:49 | e034da06-62da-481a-a2d2-8e0400f7d957 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:49 | e034da06-62da-481a-a2d2-8e0400f7d957 | services.base_client         | INFO     | HTTP PATCH /api/v1/registry/drafts/15/metadata -> 200 (0.022s)
2026-06-27 18:35:49 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "PATCH /api/v1/drafts/15/metadata HTTP/1.1" 200
2026-06-27 18:35:49 | a84fd035-2765-4076-8b6f-66903269fd6b | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 18:35:49 | a84fd035-2765-4076-8b6f-66903269fd6b | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/15 -> 200 (0.012s)
2026-06-27 18:35:49 | -                | uvicorn.access               | INFO     | 127.0.0.1:32944 - "GET /api/v1/drafts/15 HTTP/1.1" 200
2026-06-27 18:35:51 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 0.85s.
2026-06-27 18:35:52 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 2.16s.
2026-06-27 18:35:54 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 3.28s.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

Jun 27, 2026 6:35:24 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 27, 2026 6:35:24 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 27, 2026 6:35:24 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 27, 2026 6:35:24 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 27, 2026 6:35:24 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
{"timestamp": "2026-06-27 18:35:24,269", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
{"timestamp": "2026-06-27 18:35:25,018", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:25,148", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.79s."}
Jun 27, 2026 6:35:25 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmpvddbjo47/tmpptwqlkxc.json
Jun 27, 2026 6:35:25 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmpvddbjo47/tmpptwqlkxc.md
Jun 27, 2026 6:35:25 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmpvddbjo47/tmpptwqlkxc.html
{"timestamp": "2026-06-27 18:35:25,462", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-27 18:35:25,464", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-27 18:35:25,771", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Task 20002 not completed yet, returning 409"}
{"timestamp": "2026-06-27 18:35:26,092", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-27 18:35:26,095", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-27 18:35:26,097", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-27 18:35:26,100", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-27 18:35:26,102", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-27 18:35:26,105", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-27 18:35:26,107", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Uploaded 6/6 images for task 20002 (errors: 0)"}
{"timestamp": "2026-06-27 18:35:26,116", "severity": "INFO", "name": "app.services.result_builder", "message": "Result built for task 20002, mode=full"}
{"timestamp": "2026-06-27 18:35:26,118", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-27 18:35:26,118", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-27 18:35:26,119", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-27 18:35:26,942", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:27,810", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Result for task 20002 returned successfully"}
{"timestamp": "2026-06-27 18:35:27,945", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.87s."}
{"timestamp": "2026-06-27 18:35:30,733", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:31,022", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 2.04s."}
{"timestamp": "2026-06-27 18:35:33,066", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:35,674", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.09s."}
{"timestamp": "2026-06-27 18:35:39,105", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:40,107", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.93s."}
{"timestamp": "2026-06-27 18:35:42,657", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:43,659", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.15s."}
{"timestamp": "2026-06-27 18:35:47,000", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:48,001", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.80s."}
{"timestamp": "2026-06-27 18:35:51,118", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:52,120", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.13s."}
{"timestamp": "2026-06-27 18:35:54,958", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:55,959", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-27 18:34:51,316", "severity": "INFO", "name": "app.services.pipeline", "message": "no chunks found", "message_id": 10}
{"timestamp": "2026-06-27 18:34:52,361", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:53,363", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:34:53,363", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.96s."}
{"timestamp": "2026-06-27 18:34:58,183", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:34:58,189", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:34:58,190", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.16s."}
{"timestamp": "2026-06-27 18:34:59,184", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:34:59,184", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-27 18:35:01,207", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.64s."}
{"timestamp": "2026-06-27 18:35:02,208", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:03,209", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:03,210", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.97s."}
{"timestamp": "2026-06-27 18:35:06,038", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:07,039", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:07,039", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.01s."}
{"timestamp": "2026-06-27 18:35:09,900", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:10,901", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:10,902", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.07s."}
{"timestamp": "2026-06-27 18:35:15,861", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:15,933", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:15,933", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 1.04s."}
{"timestamp": "2026-06-27 18:35:16,863", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:16,863", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.93s."}
{"timestamp": "2026-06-27 18:35:18,825", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:19,656", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 2.06s."}
{"timestamp": "2026-06-27 18:35:21,714", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:22,716", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:22,717", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.82s."}
{"timestamp": "2026-06-27 18:35:27,201", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:28,202", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:28,202", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.95s."}
{"timestamp": "2026-06-27 18:35:31,015", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:32,015", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:32,016", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.09s."}
{"timestamp": "2026-06-27 18:35:36,872", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:37,874", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:37,876", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.99s."}
{"timestamp": "2026-06-27 18:35:40,727", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.96s."}
{"timestamp": "2026-06-27 18:35:42,686", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:43,687", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:43,688", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.17s."}
{"timestamp": "2026-06-27 18:35:48,406", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:49,407", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:49,407", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-27 18:35:52,469", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 18:35:53,471", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 18:35:53,471", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.11s."}
{"timestamp": "2026-06-27 18:35:55,060", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"bc4c3e34-8a29-49e0-ab13-eedf9d79e45d\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 14}"}
{"timestamp": "2026-06-27 18:35:55,084", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"03d51736-f4bb-43f6-92db-eaf83b150f00\", \"user_id\": \"u-911e4f171954\", \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 7}"}

```
