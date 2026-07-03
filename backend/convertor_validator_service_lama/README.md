# convertor_validator_service_lama

LAMA Document Parser service for the PKB convertor/validator pipeline.

## Responsibility

This service is block 1 of the document processing pipeline.

Input:
- source PDF

Main flow:
- LlamaParse processes the original PDF
- service stores parse_job_id and raw artifacts
- LlamaExtract passes work by parse_job_id
- Python validator/assembler builds rich_document_package.json
- Python validator/critic creates quality_report and correction_proposals

Out of scope for this service:
- downcast to RAG Builder JSON
- RAG indexing
- search
