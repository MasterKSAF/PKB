# Supervisor Logs

**Generated:** 2026-06-27T16:12:41.932957+00:00


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

{"timestamp": "2026-06-27 19:12:05,220", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.93s."}
{"timestamp": "2026-06-27 19:12:07,238", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:07,238", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.92s."}
{"timestamp": "2026-06-27 19:12:08,000", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:09,001", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:09,001", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.13s."}
{"timestamp": "2026-06-27 19:12:11,996", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:12,997", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:12,997", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.95s."}
{"timestamp": "2026-06-27 19:12:13,180", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:17,002", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:17,002", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.00s."}
{"timestamp": "2026-06-27 19:12:17,625", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:18,626", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:18,626", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.15s."}
{"timestamp": "2026-06-27 19:12:19,845", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:21,622", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:22,623", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:22,624", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.88s."}
{"timestamp": "2026-06-27 19:12:24,579", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:24,847", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:24,847", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.10s."}
{"timestamp": "2026-06-27 19:12:25,409", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:26,258", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:26,595", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:27,432", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:27,440", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:28,433", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:28,433", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.10s."}
{"timestamp": "2026-06-27 19:12:30,310", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:31,379", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:32,380", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:32,380", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-27 19:12:32,815", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:32,816", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.87s."}
{"timestamp": "2026-06-27 19:12:35,038", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:35,039", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 0.89s."}
{"timestamp": "2026-06-27 19:12:36,005", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:36,767", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:36,896", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:37,558", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:37,768", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:37,768", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.20s."}
{"timestamp": "2026-06-27 19:12:37,792", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:40,803", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:41,804", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:41,804", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.11s."}
{"timestamp": "2026-06-27 19:12:41,868", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-27 19:12:42,292", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:42,292", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.00s."}

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-27 19:11:06,931", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:07,932", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.87s."}
{"timestamp": "2026-06-27 19:11:10,691", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:11,692", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.83s."}
{"timestamp": "2026-06-27 19:11:14,746", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:15,113", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to localhost:4317, retrying in 1.89s."}
{"timestamp": "2026-06-27 19:11:32,327", "severity": "WARNING", "name": "app.core.security_scanner", "message": "YARA module not installed. Security scanning disabled."}
{"timestamp": "2026-06-27 19:11:33,013", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.84s."}
{"timestamp": "2026-06-27 19:11:33,708", "severity": "INFO", "name": "app.core.minio_client", "message": "Using real MinIOClient"}
{"timestamp": "2026-06-27 19:11:33,914", "severity": "INFO", "name": "root", "message": "Starting application lifespan"}
{"timestamp": "2026-06-27 19:11:33,915", "severity": "INFO", "name": "app.services.pipeline_service", "message": "PipelineService initialized: preview_limit=30, full_limit=5, queue_size=100"}
{"timestamp": "2026-06-27 19:11:33,915", "severity": "INFO", "name": "app.dependencies", "message": "Services initialized successfully"}
{"timestamp": "2026-06-27 19:11:34,190", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline worker started"}
{"timestamp": "2026-06-27 19:11:34,283", "severity": "INFO", "name": "root", "message": "MinIO buckets checked/created: documents, images"}
{"timestamp": "2026-06-27 19:11:35,985", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:36,971", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 2.36s."}
{"timestamp": "2026-06-27 19:11:39,336", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:40,842", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.99s."}
{"timestamp": "2026-06-27 19:11:43,612", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:44,614", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
{"timestamp": "2026-06-27 19:11:47,270", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:48,271", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.11s."}
{"timestamp": "2026-06-27 19:11:51,656", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:52,657", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.97s."}
{"timestamp": "2026-06-27 19:11:55,841", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:56,842", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.17s."}
{"timestamp": "2026-06-27 19:12:00,236", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:01,237", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}
{"timestamp": "2026-06-27 19:12:04,219", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:05,220", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.06s."}
{"timestamp": "2026-06-27 19:12:08,264", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:09,265", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.03s."}
{"timestamp": "2026-06-27 19:12:12,592", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:13,597", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.98s."}
{"timestamp": "2026-06-27 19:12:16,596", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:17,597", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.94s."}
{"timestamp": "2026-06-27 19:12:20,412", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:21,413", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.90s."}
{"timestamp": "2026-06-27 19:12:24,422", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:25,424", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.88s."}
{"timestamp": "2026-06-27 19:12:28,088", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:29,090", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}
{"timestamp": "2026-06-27 19:12:32,560", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:33,561", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.06s."}
{"timestamp": "2026-06-27 19:12:33,785", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:34,626", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.77s."}
{"timestamp": "2026-06-27 19:12:36,397", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:37,399", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.01s."}
{"timestamp": "2026-06-27 19:12:40,656", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:41,658", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.07s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-27 19:12:30 | c23fc669-1a75-4846-a3d8-7ece338a2776 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:30 | c23fc669-1a75-4846-a3d8-7ece338a2776 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/8 -> 200 (0.009s)
2026-06-27 19:12:30 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "GET /api/v1/drafts/8 HTTP/1.1" 200
2026-06-27 19:12:30 | f60fb54d-78a6-4f14-b642-7a8f601c1494 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:30 | f60fb54d-78a6-4f14-b642-7a8f601c1494 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/8 -> 200 (0.012s)
2026-06-27 19:12:30 | f60fb54d-78a6-4f14-b642-7a8f601c1494 | orchestrator.pipeline        | INFO     | Parser-first: enqueuing celery task
2026-06-27 19:12:30 | f60fb54d-78a6-4f14-b642-7a8f601c1494 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-27 19:12:30 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "POST /api/v1/drafts/8/preview HTTP/1.1" 202
2026-06-27 19:12:30 | e8ee54c7-a6ba-4d9d-8994-de10229b9a13 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:30 | e8ee54c7-a6ba-4d9d-8994-de10229b9a13 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/8 -> 200 (0.013s)
2026-06-27 19:12:31 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.
2026-06-27 19:12:32 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "GET /api/v1/drafts/8/preview/status?longpoll=1 HTTP/1.1" 200
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | orchestrator.pipeline        | INFO     | Approving draft
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/8 -> 200 (0.010s)
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/8/preview -> 200 (0.009s)
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents -> 201 (0.020s)
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | services.base_client         | INFO     | HTTP PATCH /api/v1/registry/drafts/8/status -> 200 (0.015s)
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | services.base_client         | ERROR    | HTTP error: POST /api/v1/registry/drafts/8/snapshot -> 404 (0.007s, retries exhausted)
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | orchestrator.pipeline        | WARNING  | Failed to save preview snapshot: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/8/snapshot'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-27 19:12:32 | b914a232-1bd6-4e54-bcd7-d54bd3d3666e | orchestrator.pipeline        | INFO     | Enqueued full Parser step (Parser-first)
2026-06-27 19:12:32 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "PATCH /api/v1/drafts/8/decide HTTP/1.1" 200
2026-06-27 19:12:35 | b7420ba8-debd-4927-962f-4bb36809779b | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:35 | b7420ba8-debd-4927-962f-4bb36809779b | services.base_client         | INFO     | HTTP DELETE /api/v1/registry/drafts/8 -> 200 (0.014s)
2026-06-27 19:12:35 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "DELETE /api/v1/drafts/8 HTTP/1.1" 204
2026-06-27 19:12:35 | -                | uvicorn.access               | INFO     | 172.18.0.1:46878 - "GET /health HTTP/1.1" 404
2026-06-27 19:12:36 | 70768326-bd8c-494b-b56b-42df7584f6e5 | app.storage                  | INFO     | Uploaded to MinIO: bucket=documents key=f-6c149ba59fef size=123616
2026-06-27 19:12:36 | 70768326-bd8c-494b-b56b-42df7584f6e5 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:36 | 70768326-bd8c-494b-b56b-42df7584f6e5 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents/check-uniqueness -> 200 (0.010s)
2026-06-27 19:12:36 | 70768326-bd8c-494b-b56b-42df7584f6e5 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:36 | 70768326-bd8c-494b-b56b-42df7584f6e5 | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.019s)
2026-06-27 19:12:36 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 0.89s.
2026-06-27 19:12:36 | 70768326-bd8c-494b-b56b-42df7584f6e5 | orchestrator.pipeline        | INFO     | Parser-first: enqueuing celery task
2026-06-27 19:12:36 | 70768326-bd8c-494b-b56b-42df7584f6e5 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-27 19:12:36 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-27 19:12:36 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "GET /api/v1/tasks/10/status HTTP/1.1" 200
2026-06-27 19:12:36 | 0ac26b00-0541-4a3d-9f83-bb59b8d28701 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:36 | 0ac26b00-0541-4a3d-9f83-bb59b8d28701 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/9 -> 200 (0.009s)
2026-06-27 19:12:36 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "GET /api/v1/drafts/9 HTTP/1.1" 200
2026-06-27 19:12:36 | b6e94129-a923-4616-8a93-060ac3a363e7 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:36 | b6e94129-a923-4616-8a93-060ac3a363e7 | services.base_client         | INFO     | HTTP PATCH /api/v1/registry/drafts/9/metadata -> 200 (0.019s)
2026-06-27 19:12:36 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "PATCH /api/v1/drafts/9/metadata HTTP/1.1" 200
2026-06-27 19:12:36 | 2477e304-f1ce-4697-a57f-650ec32f5599 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-27 19:12:36 | 2477e304-f1ce-4697-a57f-650ec32f5599 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/9 -> 200 (0.010s)
2026-06-27 19:12:36 | -                | uvicorn.access               | INFO     | 127.0.0.1:34306 - "GET /api/v1/drafts/9 HTTP/1.1" 200
2026-06-27 19:12:37 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 2.13s.
2026-06-27 19:12:39 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 4.61s.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 27, 2026 7:12:15 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 27, 2026 7:12:15 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 27, 2026 7:12:15 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 27, 2026 7:12:15 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 27, 2026 7:12:15 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 27, 2026 7:12:15 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 27, 2026 7:12:15 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
{"timestamp": "2026-06-27 19:12:16,538", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.18s."}
Jun 27, 2026 7:12:16 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmpfgycq9_8/tmpswxia6lg.json
Jun 27, 2026 7:12:16 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmpfgycq9_8/tmpswxia6lg.md
Jun 27, 2026 7:12:16 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmpfgycq9_8/tmpswxia6lg.html
{"timestamp": "2026-06-27 19:12:17,007", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-27 19:12:17,008", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-27 19:12:17,445", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-27 19:12:17,447", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-27 19:12:17,448", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-27 19:12:17,449", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-27 19:12:17,451", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-27 19:12:17,452", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-27 19:12:17,452", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Uploaded 6/6 images for task 20002 (errors: 0)"}
{"timestamp": "2026-06-27 19:12:17,456", "severity": "INFO", "name": "app.services.result_builder", "message": "Result built for task 20002, mode=full"}
{"timestamp": "2026-06-27 19:12:17,456", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-27 19:12:17,457", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-27 19:12:17,457", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-27 19:12:17,552", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Result for task 20002 returned successfully"}
{"timestamp": "2026-06-27 19:12:19,611", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:20,612", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.89s."}
{"timestamp": "2026-06-27 19:12:20,861", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:21,501", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 2.38s."}
{"timestamp": "2026-06-27 19:12:23,881", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:24,882", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.97s."}
{"timestamp": "2026-06-27 19:12:28,122", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:29,124", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.97s."}
{"timestamp": "2026-06-27 19:12:31,923", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:32,201", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to localhost:4317, retrying in 2.05s."}
{"timestamp": "2026-06-27 19:12:34,255", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:37,199", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.95s."}
{"timestamp": "2026-06-27 19:12:40,353", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:41,354", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.09s."}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-27 19:11:47,412", "severity": "DEBUG", "name": "httpcore.http11", "message": "receive_response_body.complete"}
{"timestamp": "2026-06-27 19:11:47,412", "severity": "DEBUG", "name": "httpcore.http11", "message": "response_closed.started"}
{"timestamp": "2026-06-27 19:11:47,412", "severity": "DEBUG", "name": "httpcore.http11", "message": "response_closed.complete"}
{"timestamp": "2026-06-27 19:11:47,413", "severity": "DEBUG", "name": "httpcore.connection", "message": "close.started"}
{"timestamp": "2026-06-27 19:11:47,413", "severity": "DEBUG", "name": "httpcore.connection", "message": "close.complete"}
{"timestamp": "2026-06-27 19:11:47,413", "severity": "INFO", "name": "app.services.pipeline", "message": "no chunks found", "message_id": 4}
{"timestamp": "2026-06-27 19:11:47,575", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:11:47,576", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.93s."}
{"timestamp": "2026-06-27 19:11:50,088", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:50,351", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.70s."}
{"timestamp": "2026-06-27 19:11:51,090", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:11:51,090", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.02s."}
{"timestamp": "2026-06-27 19:11:52,059", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:53,952", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 2.14s."}
{"timestamp": "2026-06-27 19:11:56,090", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:11:57,091", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:11:57,091", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.84s."}
{"timestamp": "2026-06-27 19:12:01,486", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:02,487", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:02,488", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.82s."}
{"timestamp": "2026-06-27 19:12:06,903", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:07,904", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:07,904", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.89s."}
{"timestamp": "2026-06-27 19:12:12,337", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:13,338", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:13,338", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.00s."}
{"timestamp": "2026-06-27 19:12:18,333", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:19,333", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:19,334", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.80s."}
{"timestamp": "2026-06-27 19:12:22,000", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.82s."}
{"timestamp": "2026-06-27 19:12:23,825", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:24,826", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:24,826", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.14s."}
{"timestamp": "2026-06-27 19:12:27,826", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:28,827", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:28,827", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-27 19:12:33,522", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:34,523", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:34,523", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.00s."}
{"timestamp": "2026-06-27 19:12:34,856", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:34,856", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 0.96s."}
{"timestamp": "2026-06-27 19:12:37,373", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-27 19:12:38,374", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:38,375", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.19s."}
{"timestamp": "2026-06-27 19:12:41,421", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.79s."}
{"timestamp": "2026-06-27 19:12:41,900", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"965b2d7b-8e96-47e4-92a2-ffffed6085f7\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 15}"}
{"timestamp": "2026-06-27 19:12:41,925", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"6d413a32-d7bb-4d31-9477-89899586834d\", \"user_id\": \"u-ef6da214b4cd\", \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 9}"}
{"timestamp": "2026-06-27 19:12:42,058", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-27 19:12:42,058", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.17s."}
{"timestamp": "2026-06-27 19:12:43,217", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}

```
