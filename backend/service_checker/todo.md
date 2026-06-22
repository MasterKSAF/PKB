# TODO: Пайплайн подтверждения документов (document_approval)

## 1. Изучить существующий orchestrator_draft_lifecycle
- [x] 1.1 Шаг 2 (POST /drafts) валится с 500 — Registry /drafts не реализован
- [x] 1.2 Создан новый пайплайн document_approval, tolerant к сломанным API

## 2. Создать пайплайн document_approval
- [x] 2.1 Файл `pipelines/document_approval.py`
- [x] 2.2 Шаги: аутентификация → создание черновика → preview → approve → full → индексация
- [x] 2.3 Зарегистрировать в `pipelines/__init__.py`

## 3. Проверить
- [x] 3.1 Запустить на сломанных API — все шаги с ожидаемыми ошибками (500, 404, 422) проходят
- [x] 3.2 Живая часть (Registry create + RAG Builder index) — работает
- [ ] 3.3 Перезапустить после фикса Registry /drafts — проверить полный cycle
