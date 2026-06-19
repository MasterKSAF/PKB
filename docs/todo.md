# todo — добавление title_key

## Задача

При вычислении `title_hash_sha256` сохранять также `title_key` — исходную конкатенированную строку, из которой сформирован хеш.

Формула бизнес-ключа: `SHA-256(era | source_type | mks_oks_code | okstu_code | doc_code | normalized_title)`

`title_key` = `era | source_type | mks_oks_code | okstu_code | doc_code | normalized_title`

Пример: `USSR|gost|47.020||20868-81|стойки...`

## План правок

- [x] 1. glossary.md — добавить термин `title_key`
- [x] 2. normalizer_specification.md — описать `title_key` как выход бизнес-ключа
- [x] 3. converter_specification.md — упомянуть `title_key` в разделе 6.1
- [x] 4. db_diagrams.md — добавить `title_key` в ER-диаграмму и описание `registry.documents`
- [x] 5. converter_validator_service_api.md — добавить `title_key` в preview, fingerprint, validate
- [x] 6. orchestrator_service_api.md — добавить `title_key` в ответы документов и черновиков
- [x] 7. registry_service_api.md — добавить `title_key` в ответы документов, check-uniqueness, примечания
- [x] 8. 6.dev_tasks_17_06.md — добавить задачу DB-28
- [x] 9. specificity.md — зафиксировать решение
- [x] 10. overview.md — упомянуть `title_key` в описании бизнес-ключа
- [x] 11. pipeline1-formation.md — упомянуть `title_key` на шаге 2.6 и в формуле
- [x] 12. schema/diagrams.md — добавить `title_key` в диаграмму metadata
