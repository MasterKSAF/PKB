# Тесты для Document API — ВЫПОЛНЕНО

## Что сделано
Все endpoint'ы Document API покрыты тестами.

| Endpoint | Класс | Тестов | Статус |
|----------|-------|:------:|--------|
| `GET /api/v1/documents/` | TestListDocuments | 17 | ✅ |
| `GET /api/v1/documents/queue` | TestDocumentQueue | 6 | ✅ |
| `GET /api/v1/documents/{doc_id}` | TestGetDocument | 4 | ✅ |
| `GET /api/v1/documents/{doc_id}/status` | TestDocumentStatus | 6 | ✅ |
| `GET /api/v1/documents/{doc_id}/file` | TestDocumentFile | 4 | ✅ |
| `GET /api/v1/documents/{doc_id}/pages` | TestDocumentPages | 4 | ✅ |
| `GET /api/v1/documents/{doc_id}/pages/{num}` | TestDocumentPageView | 3 | ✅ |
| `GET /api/v1/documents/{doc_id}/pages/{num}/text` | TestDocumentPageText | 5 | ✅ |
| `GET /api/v1/documents/{doc_id}/pages/{num}/preview` | TestDocumentPagePreview | 3 | ✅ |
| `GET /api/v1/documents/{doc_id}/errors` | TestDocumentErrors | 5 | ✅ |
| `GET /api/v1/documents/{doc_id}/parameters` | TestDocumentParameters | 5 | ✅ |
| `POST /api/v1/documents/{doc_id}/reprocess` | TestDocumentReprocess | 5 | ✅ |
| (ранее добавленные Versions + Approve + History) | | 26 | ✅ |

**Итого: 348 passed, 0 failed, 0 skipped**
