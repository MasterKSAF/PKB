# Supervisor Logs

**Generated:** 2026-06-17T18:09:52.419564+00:00


---

## 📋 Быстрая навигация


- [ℹ️ INFO — auth.err](#auth-err)
- [ℹ️ INFO — auth.log](#auth-log)
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
- [ℹ️ INFO — query.log](#query-log)
- [ℹ️ INFO — rag_builder.err](#rag_builder-err)
- [ℹ️ INFO — rag_builder.log](#rag_builder-log)
- [ℹ️ INFO — rag_search.err](#rag_search-err)
- [ℹ️ INFO — rag_search.log](#rag_search-log)
- [ℹ️ INFO — registry.err](#registry-err)
- [ℹ️ INFO — registry.log](#registry-log)


---

## ℹ️ Info-логи

_19 файл(ов) без ошибок (пропущены): auth.err, auth.log, converter_validator.err, converter_validator.log, gateway.err, gateway.log, integration.err, integration.log, ocr.err, orchestrator.err, parser.err, query.err, query.log, rag_builder.err, rag_builder.log, rag_search.err, rag_search.log, registry.err, registry.log_


## ❌ Error-логи


### ocr-log

**❌ ERROR** — `/var/log/supervisor/ocr.log`


```

{"timestamp": "2026-06-17 21:09:17,189", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-17 21:09:18,190", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.88s."}
{"timestamp": "2026-06-17 21:09:21,446", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 4.17s."}
{"timestamp": "2026-06-17 21:09:25,615", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-17 21:09:26,616", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.87s."}
{"timestamp": "2026-06-17 21:09:34,414", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-17 21:09:35,415", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 0.94s."}
{"timestamp": "2026-06-17 21:09:41,621", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-17 21:09:42,624", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.19s."}
{"timestamp": "2026-06-17 21:09:48,780", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-17 21:09:49,782", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting logs to localhost:4317, retrying in 1.09s."}

```


### orchestrator-log

**❌ ERROR** — `/var/log/supervisor/orchestrator.log`


```

FROM tasks 
WHERE tasks.draft_id = $1::INTEGER ORDER BY tasks.created_at DESC
2026-06-17 21:09:51 | 5f36361fd6b24f8b | sqlalchemy.engine.Engine     | INFO     | [cached since 0.01911s ago] (4,)
2026-06-17 21:09:51 | 5f36361fd6b24f8b | sqlalchemy.engine.Engine     | INFO     | SELECT task_steps.id, task_steps.task_id, task_steps.step_name, task_steps.step_index, task_steps.service_name, task_steps.status, task_steps.input_data, task_steps.output_data, task_steps.error_code, task_steps.error_message, task_steps.created_at, task_steps.started_at, task_steps.completed_at 
FROM task_steps 
WHERE task_steps.task_id = $1::INTEGER ORDER BY task_steps.step_index
2026-06-17 21:09:51 | 5f36361fd6b24f8b | sqlalchemy.engine.Engine     | INFO     | [cached since 34.8s ago] (3,)
2026-06-17 21:09:51 | -                | uvicorn.access               | INFO     | 172.19.0.1:41826 - "GET /api/v1/drafts/4/preview/status?longpoll=0 HTTP/1.1" 200
2026-06-17 21:09:51 | 5f36361fd6b24f8b | sqlalchemy.engine.Engine     | INFO     | COMMIT
2026-06-17 21:09:51 | 9a7b244466ce4eb8 | sqlalchemy.engine.Engine     | INFO     | BEGIN (implicit)
2026-06-17 21:09:51 | 9a7b244466ce4eb8 | sqlalchemy.engine.Engine     | INFO     | SELECT tasks.id, tasks.draft_id, tasks.document_id, tasks.pipeline_type, tasks.status, tasks.pipeline_stage, tasks.progress_percent, tasks.priority, tasks.current_step_name, tasks.current_step_index, tasks.total_steps, tasks.trace_id, tasks.full_completed, tasks.error_code, tasks.error_message, tasks.retry_count, tasks.locked_by, tasks.locked_at, tasks.created_at, tasks.updated_at, tasks.started_at, tasks.completed_at 
FROM tasks 
WHERE tasks.draft_id = $1::INTEGER ORDER BY tasks.created_at DESC
2026-06-17 21:09:51 | 9a7b244466ce4eb8 | sqlalchemy.engine.Engine     | INFO     | [cached since 0.02549s ago] (4,)
2026-06-17 21:09:51 | 9a7b244466ce4eb8 | sqlalchemy.engine.Engine     | INFO     | SELECT tasks.id, tasks.draft_id, tasks.document_id, tasks.pipeline_type, tasks.status, tasks.pipeline_stage, tasks.progress_percent, tasks.priority, tasks.current_step_name, tasks.current_step_index, tasks.total_steps, tasks.trace_id, tasks.full_completed, tasks.error_code, tasks.error_message, tasks.retry_count, tasks.locked_by, tasks.locked_at, tasks.created_at, tasks.updated_at, tasks.started_at, tasks.completed_at 
FROM tasks 
WHERE tasks.id = $1::INTEGER
2026-06-17 21:09:51 | 9a7b244466ce4eb8 | sqlalchemy.engine.Engine     | INFO     | [cached since 35.61s ago] (3,)
2026-06-17 21:09:51 | d81b9134eb924f0f | orchestrator.pipeline        | INFO     | Approving draft
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | SELECT tasks.id, tasks.draft_id, tasks.document_id, tasks.pipeline_type, tasks.status, tasks.pipeline_stage, tasks.progress_percent, tasks.priority, tasks.current_step_name, tasks.current_step_index, tasks.total_steps, tasks.trace_id, tasks.full_completed, tasks.error_code, tasks.error_message, tasks.retry_count, tasks.locked_by, tasks.locked_at, tasks.created_at, tasks.updated_at, tasks.started_at, tasks.completed_at 
FROM tasks 
WHERE tasks.id = $1::INTEGER FOR UPDATE
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [cached since 35.6s ago] (3,)
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | UPDATE tasks SET pipeline_stage=$1::VARCHAR, progress_percent=$2::INTEGER, updated_at=now() WHERE tasks.id = $3::INTEGER
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [generated in 0.00013s] ('full', 50, 3)
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | SELECT task_steps.id, task_steps.task_id, task_steps.step_name, task_steps.step_index, task_steps.service_name, task_steps.status, task_steps.input_data, task_steps.output_data, task_steps.error_code, task_steps.error_message, task_steps.created_at, task_steps.started_at, task_steps.completed_at 
FROM task_steps 
WHERE task_steps.task_id = $1::INTEGER ORDER BY task_steps.step_index
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [cached since 34.81s ago] (3,)
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | INSERT INTO task_steps (task_id, step_name, step_index, service_name, status, input_data, error_code, error_message, started_at, completed_at) VALUES ($1::INTEGER, $2::VARCHAR, $3::INTEGER, $4::VARCHAR, $5::VARCHAR, $6::JSON, $7::VARCHAR, $8::VARCHAR, $9::TIMESTAMP WITH TIME ZONE, $10::TIMESTAMP WITH TIME ZONE) RETURNING task_steps.id, task_steps.created_at
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [cached since 35.6s ago] (3, 'full_ocr', 3, 'OCR Service', 'pending', '{"file_key": "f-6c149ba59fef", "mode": "full"}', None, None, None, None)
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | INSERT INTO task_steps (task_id, step_name, step_index, service_name, status, input_data, error_code, error_message, started_at, completed_at) VALUES ($1::INTEGER, $2::VARCHAR, $3::INTEGER, $4::VARCHAR, $5::VARCHAR, $6::JSON, $7::VARCHAR, $8::VARCHAR, $9::TIMESTAMP WITH TIME ZONE, $10::TIMESTAMP WITH TIME ZONE) RETURNING task_steps.id, task_steps.created_at
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [cached since 35.6s ago] (3, 'full_converter', 4, 'Converter-validator', 'pending', '{"file_key": "f-6c149ba59fef", "mode": "full"}', None, None, None, None)
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | INSERT INTO task_steps (task_id, step_name, step_index, service_name, status, input_data, error_code, error_message, started_at, completed_at) VALUES ($1::INTEGER, $2::VARCHAR, $3::INTEGER, $4::VARCHAR, $5::VARCHAR, $6::JSON, $7::VARCHAR, $8::VARCHAR, $9::TIMESTAMP WITH TIME ZONE, $10::TIMESTAMP WITH TIME ZONE) RETURNING task_steps.id, task_steps.created_at
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [cached since 35.61s ago] (3, 'registry_creation', 5, 'Registry', 'pending', '{"draft_id": 4}', None, None, None, None)
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | SELECT task_steps.id, task_steps.task_id, task_steps.step_name, task_steps.step_index, task_steps.service_name, task_steps.status, task_steps.input_data, task_steps.output_data, task_steps.error_code, task_steps.error_message, task_steps.created_at, task_steps.started_at, task_steps.completed_at 
FROM task_steps 
WHERE task_steps.task_id = $1::INTEGER ORDER BY task_steps.step_index
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [cached since 34.82s ago] (3,)
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | SELECT task_steps.id, task_steps.task_id, task_steps.step_name, task_steps.step_index, task_steps.service_name, task_steps.status, task_steps.input_data, task_steps.output_data, task_steps.error_code, task_steps.error_message, task_steps.created_at, task_steps.started_at, task_steps.completed_at 
FROM task_steps 
WHERE task_steps.id = $1::INTEGER FOR UPDATE
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [cached since 35.6s ago] (13,)
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | UPDATE task_steps SET status=$1::VARCHAR, started_at=$2::TIMESTAMP WITH TIME ZONE WHERE task_steps.id = $3::INTEGER
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | [cached since 35.6s ago] ('running', datetime.datetime(2026, 6, 17, 18, 9, 51, 630477, tzinfo=datetime.timezone.utc), 13)
2026-06-17 21:09:51 | d81b9134eb924f0f | orchestrator.pipeline        | INFO     | Enqueued full OCR step
2026-06-17 21:09:51 | -                | uvicorn.access               | INFO     | 172.19.0.1:41826 - "PATCH /api/v1/drafts/4/decide HTTP/1.1" 200
2026-06-17 21:09:51 | d81b9134eb924f0f | sqlalchemy.engine.Engine     | INFO     | COMMIT
2026-06-17 21:09:51 | 8fde6dcaa54e412c | services.base_client         | DEBUG    | Mock call: GET /registry/drafts/4 -> 0.000s
2026-06-17 21:09:51 | -                | uvicorn.access               | INFO     | 172.19.0.1:41826 - "GET /api/v1/drafts/4 HTTP/1.1" 200

```


### parser-log

**❌ ERROR** — `/var/log/supervisor/parser.log`


```

{"timestamp": "2026-06-17 21:09:47,866", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export logs to localhost:4317, error code: StatusCode.UNAVAILABLE"}
{"timestamp": "2026-06-17 21:09:47,866", "severity": "WARNING", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317, retrying in 2.14s."}
{"timestamp": "2026-06-17 21:09:49,085", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Starting full pipeline for task 20002, file multi-doc-2-1781719784.pdf"}
{"timestamp": "2026-06-17 21:09:49,122", "severity": "INFO", "name": "app.core.minio_client", "message": "Downloaded multi-doc-2-1781719784.pdf, size=123616 bytes"}
{"timestamp": "2026-06-17 21:09:49,123", "severity": "INFO", "name": "app.api.v1.endpoints.status", "message": "Returning status for task 20002: TaskStatus.ACCEPTED"}
{"timestamp": "2026-06-17 21:09:49,126", "severity": "INFO", "name": "app.core.validator", "message": "Security check passed"}
{"timestamp": "2026-06-17 21:09:49,126", "severity": "INFO", "name": "app.core.validator", "message": "Validation passed, MIME=application/pdf"}
{"timestamp": "2026-06-17 21:09:49,128", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Parsing PDF for task 20002, options={}"}
Jun 17, 2026 9:09:49 PM org.opendataloader.pdf.processors.DocumentProcessor preprocessing
INFO: File name: /tmp/tmpi9s7s8op.pdf
Jun 17, 2026 9:09:49 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11901 in stream 39 0 obj)
Jun 17, 2026 9:09:49 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16578 in stream 47 0 obj)
Jun 17, 2026 9:09:49 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 16513 in stream 55 0 obj)
Jun 17, 2026 9:09:49 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 6539 in stream 63 0 obj)
Jun 17, 2026 9:09:49 PM org.verapdf.pd.font.type1.Type1PrivateParser decodeCharString
WARNING: Error in parsing private data in Type 1 font: incorrect amount of charstrings specified(offset = 11320 in stream 71 0 obj)
Jun 17, 2026 9:09:49 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Number of pages: 5
Jun 17, 2026 9:09:49 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Author: null
Jun 17, 2026 9:09:49 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Title: null
Jun 17, 2026 9:09:49 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Creation date: D:20081002124836+00'00'
Jun 17, 2026 9:09:49 PM org.opendataloader.pdf.processors.DocumentProcessor calculateDocumentInfo
INFO: Modification date: D:20081002124836+00'00'
Jun 17, 2026 9:09:49 PM org.opendataloader.pdf.processors.DocumentProcessor processDocument
INFO: Processing 5 pages with 1 threads
Jun 17, 2026 9:09:50 PM org.opendataloader.pdf.json.JsonWriter writeToJson
INFO: Created /tmp/tmplb_5d0jf/tmpi9s7s8op.json
Jun 17, 2026 9:09:50 PM org.opendataloader.pdf.markdown.MarkdownGenerator writeToMarkdown
INFO: Created /tmp/tmplb_5d0jf/tmpi9s7s8op.md
Jun 17, 2026 9:09:50 PM org.opendataloader.pdf.html.HtmlGenerator writeToHtml
INFO: Created /tmp/tmplb_5d0jf/tmpi9s7s8op.html
{"timestamp": "2026-06-17 21:09:50,546", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "opendataloader_pdf conversion completed for task 20002"}
{"timestamp": "2026-06-17 21:09:50,547", "severity": "INFO", "name": "app.services.parsers.pdf_parser", "message": "Found 6 image references in JSON"}
{"timestamp": "2026-06-17 21:09:50,635", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_0_617ab711356b06f8.png, size=7705 bytes"}
{"timestamp": "2026-06-17 21:09:50,723", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_1_f8052b5c9759d1e1.png, size=5144 bytes"}
{"timestamp": "2026-06-17 21:09:50,809", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_2_1d9c0ba54ed582b4.png, size=4605 bytes"}
{"timestamp": "2026-06-17 21:09:50,894", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_3_7cba379c2bca3a95.png, size=3890 bytes"}
{"timestamp": "2026-06-17 21:09:50,980", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_4_3f9976aee3a3dac5.png, size=11303 bytes"}
{"timestamp": "2026-06-17 21:09:51,064", "severity": "INFO", "name": "app.core.minio_client", "message": "Image uploaded to images/20002/20002_5_28bd92663bf750a8.png, size=9275 bytes"}
{"timestamp": "2026-06-17 21:09:51,069", "severity": "INFO", "name": "app.services.pipeline.steps", "message": "Result stored for task 20002"}
{"timestamp": "2026-06-17 21:09:51,069", "severity": "INFO", "name": "app.services.pipeline.pipeline", "message": "Pipeline completed successfully for task 20002"}
{"timestamp": "2026-06-17 21:09:51,069", "severity": "INFO", "name": "app.api.v1.endpoints.process", "message": "Full pipeline completed for task 20002"}
{"timestamp": "2026-06-17 21:09:53,359", "severity": "ERROR", "name": "opentelemetry.exporter.otlp.proto.grpc.exporter", "message": "Failed to export traces to localhost:4317, error code: StatusCode.UNAVAILABLE"}

```
