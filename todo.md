# Исправлено: Ошибка 500 при загрузке документов

**Корневая причина**: В контейнере `pkb-parser` (`python:3.11-slim`) отсутствовали системные библиотеки, необходимые Docling (`DocumentConverter`). При парсинге PDF возникала ошибка `libxcb.so.1: cannot open shared object file`.

**Что сделано:**
1. В `backend/parser_service/Dockerfile` добавлены пакеты: `libxcb1`, `libgl1`, `libglib2.0-0t64`
2. В запущенный контейнер доустановлены вручную: `libglib2.0-0t64`, `libgomp1`
3. Проверено тестом `test_quick.py` — весь пайплайн (preview → approve → full → registry → rag_index) завершён успешно
