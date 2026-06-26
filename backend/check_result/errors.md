# Supervisor Logs

**Generated:** 2026-06-26T17:15:39.790631+00:00


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

{"timestamp": "2026-06-26 20:14:58,965", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:59,334", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.98s."}
{"timestamp": "2026-06-26 20:15:00,410", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:01,642", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:02,319", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:02,320", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 20:15:05,410", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:05,410", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 20:15:07,027", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:08,028", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:08,028", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.14s."}
{"timestamp": "2026-06-26 20:15:10,267", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:11,027", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.86s."}
{"timestamp": "2026-06-26 20:15:12,886", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:13,888", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:13,888", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-26 20:15:15,270", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:15,270", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.17s."}
{"timestamp": "2026-06-26 20:15:17,087", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:18,069", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:18,307", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:19,299", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:19,515", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:19,515", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.16s."}
{"timestamp": "2026-06-26 20:15:19,860", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:21,490", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:22,534", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:23,325", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:23,325", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.13s."}
{"timestamp": "2026-06-26 20:15:23,537", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:23,537", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.95s."}
{"timestamp": "2026-06-26 20:15:25,538", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:26,361", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:27,364", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:27,365", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.94s."}
{"timestamp": "2026-06-26 20:15:28,248", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:31,166", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:31,167", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.82s."}
{"timestamp": "2026-06-26 20:15:31,756", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:33,257", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:33,258", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.84s."}
{"timestamp": "2026-06-26 20:15:33,793", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:34,855", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:35,732", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:35,965", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 2.07s."}
{"timestamp": "2026-06-26 20:15:36,734", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:36,735", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.13s."}
{"timestamp": "2026-06-26 20:15:38,040", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:39,714", "severity": "INFO", "name": "app.services.auth_service", "message": "User logged in: admin@example.com"}
{"timestamp": "2026-06-26 20:15:39,732", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.85s."}

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
INFO:     Started server process [37]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8086 (Press CTRL+C to quit)
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
Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
Registry classifier validation failed: Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/classifiers/validate/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404

```


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-26 20:14:06,146", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:07,147", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 20:14:09,987", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:10,990", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.94s."}
{"timestamp": "2026-06-26 20:14:13,883", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:14,889", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.01s."}
{"timestamp": "2026-06-26 20:14:18,088", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:19,091", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.99s."}
{"timestamp": "2026-06-26 20:14:20,015", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 20:14:22,306", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:23,307", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.94s."}
{"timestamp": "2026-06-26 20:14:25,884", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:26,887", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.84s."}
{"timestamp": "2026-06-26 20:14:29,675", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:30,676", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.04s."}
{"timestamp": "2026-06-26 20:14:33,782", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:34,783", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.86s."}
{"timestamp": "2026-06-26 20:14:37,748", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:38,749", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.82s."}
{"timestamp": "2026-06-26 20:14:41,187", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:42,189", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.94s."}
{"timestamp": "2026-06-26 20:14:45,299", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:46,301", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}
{"timestamp": "2026-06-26 20:14:49,578", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:50,579", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.99s."}
{"timestamp": "2026-06-26 20:14:53,370", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:54,373", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.09s."}
{"timestamp": "2026-06-26 20:14:57,374", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:58,377", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 20:15:01,105", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:02,106", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}
{"timestamp": "2026-06-26 20:15:05,322", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:06,324", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.89s."}
{"timestamp": "2026-06-26 20:15:09,276", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:10,279", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.92s."}
{"timestamp": "2026-06-26 20:15:13,200", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:14,202", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}
{"timestamp": "2026-06-26 20:15:17,298", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:18,300", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 20:15:21,085", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:22,087", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.96s."}
{"timestamp": "2026-06-26 20:15:25,191", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:26,194", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.14s."}
{"timestamp": "2026-06-26 20:15:29,085", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:30,087", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.92s."}
{"timestamp": "2026-06-26 20:15:32,746", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:33,751", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.02s."}
{"timestamp": "2026-06-26 20:15:36,720", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:37,722", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.99s."}
{"timestamp": "2026-06-26 20:15:40,407", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

2026-06-26 20:15:26 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.028s)
2026-06-26 20:15:26 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 20:15:26 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-26 20:15:26 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "GET /api/v1/tasks/43/status HTTP/1.1" 200
2026-06-26 20:15:26 | 44dc2bfd-da26-45df-9ff2-b85e7b93dc7e | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:26 | 44dc2bfd-da26-45df-9ff2-b85e7b93dc7e | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/39 -> 200 (0.020s)
2026-06-26 20:15:26 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "GET /api/v1/drafts/39 HTTP/1.1" 200
2026-06-26 20:15:26 | 8b0e6079-76ff-4765-8037-4e69c42b7aeb | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:26 | 8b0e6079-76ff-4765-8037-4e69c42b7aeb | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/39 -> 200 (0.035s)
2026-06-26 20:15:26 | 8b0e6079-76ff-4765-8037-4e69c42b7aeb | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 20:15:26 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "POST /api/v1/drafts/39/preview HTTP/1.1" 202
2026-06-26 20:15:26 | 47d2c013-60c4-4c70-b345-f6794da773b7 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:26 | 47d2c013-60c4-4c70-b345-f6794da773b7 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/39 -> 200 (0.051s)
2026-06-26 20:15:27 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.
2026-06-26 20:15:27 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "GET /api/v1/drafts/39/preview/status?longpoll=1 HTTP/1.1" 200
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | orchestrator.pipeline        | INFO     | Approving draft
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/39 -> 200 (0.020s)
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/39/preview -> 200 (0.016s)
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents -> 201 (0.034s)
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | services.base_client         | ERROR    | HTTP error: POST /api/v1/registry/drafts/39/snapshot -> 404 (0.019s, retries exhausted)
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | orchestrator.pipeline        | WARNING  | Failed to save preview snapshot: Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/39/snapshot'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
2026-06-26 20:15:27 | 78d19bd1-8f9d-4d09-afef-64a0b8049e90 | orchestrator.pipeline        | INFO     | Enqueued full OCR step
2026-06-26 20:15:27 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "PATCH /api/v1/drafts/39/decide HTTP/1.1" 200
2026-06-26 20:15:31 | 51b086ed-82c6-429a-a451-9a057b07184e | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:31 | 51b086ed-82c6-429a-a451-9a057b07184e | services.base_client         | INFO     | HTTP DELETE /api/v1/registry/drafts/39 -> 200 (0.021s)
2026-06-26 20:15:31 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "DELETE /api/v1/drafts/39 HTTP/1.1" 204
2026-06-26 20:15:32 | d815ef6e-78f9-4cd3-a64b-aaefdcae2b31 | app.storage                  | INFO     | Uploaded to MinIO: bucket=documents key=f-6c149ba59fef size=123616
2026-06-26 20:15:32 | d815ef6e-78f9-4cd3-a64b-aaefdcae2b31 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:32 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 0.94s.
2026-06-26 20:15:32 | d815ef6e-78f9-4cd3-a64b-aaefdcae2b31 | services.base_client         | INFO     | HTTP POST /api/v1/registry/documents/check-uniqueness -> 200 (0.046s)
2026-06-26 20:15:32 | d815ef6e-78f9-4cd3-a64b-aaefdcae2b31 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:32 | d815ef6e-78f9-4cd3-a64b-aaefdcae2b31 | services.base_client         | INFO     | HTTP POST /api/v1/registry/drafts -> 201 (0.047s)
2026-06-26 20:15:32 | d815ef6e-78f9-4cd3-a64b-aaefdcae2b31 | orchestrator.pipeline        | INFO     | Pipeline preview started
2026-06-26 20:15:32 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "POST /api/v1/drafts HTTP/1.1" 202
2026-06-26 20:15:32 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "GET /api/v1/tasks/44/status HTTP/1.1" 200
2026-06-26 20:15:33 | b41dbf41-ff84-4abc-9951-5187bdae2447 | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:33 | b41dbf41-ff84-4abc-9951-5187bdae2447 | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/40 -> 200 (0.035s)
2026-06-26 20:15:33 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "GET /api/v1/drafts/40 HTTP/1.1" 200
2026-06-26 20:15:33 | 55274e64-181c-4a5d-99ea-a91803901bfb | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:33 | 55274e64-181c-4a5d-99ea-a91803901bfb | services.base_client         | INFO     | HTTP PATCH /api/v1/registry/drafts/40/metadata -> 200 (0.052s)
2026-06-26 20:15:33 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "PATCH /api/v1/drafts/40/metadata HTTP/1.1" 200
2026-06-26 20:15:33 | cd8af60c-ea87-4d78-a54c-0c36bb50d26e | services.base_client         | INFO     | HTTP client initialized with retry + circuit breaker
2026-06-26 20:15:33 | cd8af60c-ea87-4d78-a54c-0c36bb50d26e | services.base_client         | INFO     | HTTP GET /api/v1/registry/drafts/40 -> 200 (0.031s)
2026-06-26 20:15:33 | -                | uvicorn.access               | INFO     | 127.0.0.1:45104 - "GET /api/v1/drafts/40 HTTP/1.1" 200
2026-06-26 20:15:33 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 1.64s.
2026-06-26 20:15:35 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | WARNING  | Transient error HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: /v1/traces (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 111] Connection refused")) encountered while exporting span batch, retrying in 4.21s.
2026-06-26 20:15:39 | -                | opentelemetry.exporter.otlp.proto.http.trace_exporter | ERROR    | Failed to export span batch due to timeout, max retries or shutdown.

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

Jun 26, 2026 8:15:06 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 26, 2026 8:15:06 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 26, 2026 8:15:06 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 26, 2026 8:15:06 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 26, 2026 8:15:06 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 26, 2026 8:15:06 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
{"timestamp": "2026-06-26 20:15:08,003", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Task 20002 not completed yet, returning 409"}
Jun 26, 2026 8:15:08 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmp75spwedc/tmp5gtkkr_o.json
Jun 26, 2026 8:15:08 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmp75spwedc/tmp5gtkkr_o.md
Jun 26, 2026 8:15:08 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmp75spwedc/tmp5gtkkr_o.html
{"timestamp": "2026-06-26 20:15:08,182", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-26 20:15:08,183", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-26 20:15:08,723", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/46814c0b7a59510eaddc21ba5f749f42f81a2603730068e8108cd1b207b854f8.png, size=5144 bytes"}
{"timestamp": "2026-06-26 20:15:08,724", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/6c668fedf8e98f48578fca8eae07288dc817f6e5d7a53ecbff9c3db9a9b28820.png, size=9275 bytes"}
{"timestamp": "2026-06-26 20:15:08,731", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/17f38761247931153c70de28a0b4b0aba9b08ffccf47e25b4e442f390e0b5f65.png, size=4605 bytes"}
{"timestamp": "2026-06-26 20:15:08,734", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/de39a0affa0713ab8d18367374324214f1bf7b9d9ea2d58164c72b118afb4efb.png, size=11303 bytes"}
{"timestamp": "2026-06-26 20:15:08,735", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/2167cff7974960b765abacd8fc3f330d46d8c77e35c61d90ce3783c4b8af0f12.png, size=7705 bytes"}
{"timestamp": "2026-06-26 20:15:08,736", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/88cdbe040537d46d827ead0ddb36dde1a488c294864329a488ed24de7d3ebfaa.png, size=3890 bytes"}
{"timestamp": "2026-06-26 20:15:08,737", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Uploaded 6/6 images for task 20002 (errors: 0)"}
{"timestamp": "2026-06-26 20:15:08,741", "severity": "INFO", "name": "app.services.result_builder", "message": "Result built for task 20002, mode=full"}
{"timestamp": "2026-06-26 20:15:08,742", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-26 20:15:08,742", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-26 20:15:08,742", "severity": "INFO", "name": "app.services.pipeline_service", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-26 20:15:09,582", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:10,025", "severity": "INFO", "name": "app.api.v1.endpoints.result", "message": "Result for task 20002 returned successfully"}
{"timestamp": "2026-06-26 20:15:10,585", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.04s."}
{"timestamp": "2026-06-26 20:15:13,912", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:14,914", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.82s."}
{"timestamp": "2026-06-26 20:15:17,584", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:18,586", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.93s."}
{"timestamp": "2026-06-26 20:15:21,757", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:22,760", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.16s."}
{"timestamp": "2026-06-26 20:15:25,538", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:26,314", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to localhost:4317, retrying in 1.03s."}
{"timestamp": "2026-06-26 20:15:29,079", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:30,490", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.11s."}
{"timestamp": "2026-06-26 20:15:33,952", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:34,943", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.95s."}
{"timestamp": "2026-06-26 20:15:38,016", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:39,018", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.85s."}
{"timestamp": "2026-06-26 20:15:41,618", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}

```


### query-log

**❌ ERROR** — `/var/log/supervisor/query.log`


```

{"timestamp": "2026-06-26 20:14:43,279", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.started host='localhost' port=11434 local_address=None timeout=120.0 socket_options=None"}
{"timestamp": "2026-06-26 20:14:43,280", "severity": "DEBUG", "name": "httpcore.connection", "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))"}
{"timestamp": "2026-06-26 20:14:43,285", "severity": "ERROR", "name": "app.services.pipeline", "message": "llm generation failed after retries", "message_id": 16}
{"timestamp": "2026-06-26 20:14:43,865", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 2.06s."}
{"timestamp": "2026-06-26 20:14:45,922", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:46,717", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:14:46,717", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 0.91s."}
{"timestamp": "2026-06-26 20:14:46,924", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:14:46,925", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.89s."}
{"timestamp": "2026-06-26 20:14:51,114", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:52,342", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:14:52,342", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.07s."}
{"timestamp": "2026-06-26 20:14:53,835", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for metrics exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:14:53,836", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting metrics to signoz-otel-collector:4317, retrying in 0.81s."}
{"timestamp": "2026-06-26 20:14:57,105", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:14:58,106", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:14:58,107", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.18s."}
{"timestamp": "2026-06-26 20:14:58,620", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export metrics to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:01,167", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.90s."}
{"timestamp": "2026-06-26 20:15:03,070", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:04,072", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:04,072", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.84s."}
{"timestamp": "2026-06-26 20:15:06,784", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:07,785", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:07,786", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.14s."}
{"timestamp": "2026-06-26 20:15:12,704", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:13,705", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:13,705", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.19s."}
{"timestamp": "2026-06-26 20:15:16,741", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:17,742", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:17,743", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.05s."}
{"timestamp": "2026-06-26 20:15:20,674", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:21,675", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:21,676", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.17s."}
{"timestamp": "2026-06-26 20:15:24,732", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:25,733", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:25,734", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.98s."}
{"timestamp": "2026-06-26 20:15:28,596", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:29,597", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:29,598", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.99s."}
{"timestamp": "2026-06-26 20:15:34,549", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:35,551", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:35,551", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 1.04s."}
{"timestamp": "2026-06-26 20:15:39,747", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"84511550-a7d3-4c51-96ac-c93e224a2a1c\", \"user_id\": null, \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/projects\", \"status\": 201, \"duration_ms\": 11}"}
{"timestamp": "2026-06-26 20:15:39,769", "severity": "INFO", "name": "query_service", "message": "{\"request_id\": \"fdf3f0b7-8f28-4559-ae41-d4440b8c2948\", \"user_id\": \"u-faff87f17afd\", \"draft_id\": null, \"method\": \"POST\", \"path\": \"/api/v1/chat/sessions\", \"status\": 201, \"duration_ms\": 6}"}
{"timestamp": "2026-06-26 20:15:40,155", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to signoz-otel-collector:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-26 20:15:41,111", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for traces exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:41,112", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to signoz-otel-collector:4317, retrying in 1.08s."}
{"timestamp": "2026-06-26 20:15:41,157", "severity": "DEBUG", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Reinitializing gRPC channel for logs exporter due to UNAVAILABLE error"}
{"timestamp": "2026-06-26 20:15:41,158", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to signoz-otel-collector:4317, retrying in 0.93s."}

```
