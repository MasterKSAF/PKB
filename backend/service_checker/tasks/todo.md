# Todo: Перевод пайплайнов на Gateway

## Pipeline files (14 шт, orchestrator_draft_lifecycle уже готов)
- [x] orchestrator_draft_lifecycle.py (уже готов)

- [x] admin_user_lifecycle.py: services=["gateway"], все шаги gateway:8080
- [x] chat_inference.py: services=["gateway"], все шаги gateway:8080
- [x] document_approval.py: services=["gateway"], все шаги gateway:8080
- [x] document_processing.py: services=["gateway","minio"], gateway:8080, minio:19000
- [x] full_document_lifecycle.py: services=["gateway"], все шаги gateway:8080
- [x] multi_document_cross_search.py: services=["gateway","minio"], gateway:8080, minio:19000
- [x] orchestrator_document_reject.py: services=["gateway"], все шаги gateway:8080
- [x] orchestrator_document_reprocess.py: services=["gateway"], все шаги gateway:8080
- [x] orchestrator_document_versions.py: services=["gateway"], все шаги gateway:8080
- [x] orchestrator_draft_delete.py: services=["gateway"], все шаги gateway:8080
- [x] orchestrator_full_document_lifecycle.py: services=["gateway"], все шаги gateway:8080
- [x] orchestrator_metadata_update.py: services=["gateway"], все шаги gateway:8080
- [x] registry_lifecycle.py: services=["gateway"], все шаги gateway:8080
- [x] registry_quarantine.py: services=["gateway"], все шаги gateway:8080

## Test files
- [x] admin_user_lifecycle: gateway assertions
- [x] document_approval: gateway assertions
- [x] document_processing: gateway + minio assertions
- [x] full_document_lifecycle: gateway assertions
- [x] multi_document_cross_search: gateway + minio assertions
- [x] orchestrator_document_reject: gateway assertions
- [x] orchestrator_document_reprocess: gateway assertions
- [x] orchestrator_document_versions: gateway assertions
- [x] orchestrator_draft_delete: gateway assertions
- [x] orchestrator_full_document_lifecycle: gateway assertions
- [x] orchestrator_metadata_update: gateway assertions
- [x] registry_lifecycle: gateway assertions
- [x] registry_quarantine: gateway assertions
- [x] test_pipeline_steps.py: gateway assertions (document_processing, chat_inference, registry_lifecycle)
- [x] test_pipeline_service_consistency.py: EXTERNAL_SERVICES, добавить "gateway"

## Validation
- [x] Запустить тесты: 129 pipeline unit tests + 45 service consistency tests — все PASSED
